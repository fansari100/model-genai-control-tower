########################################################################
# Control Tower – Terraform Root Module
#
# Provisions all AWS infrastructure for the Control Tower platform:
#   - VPC with public/private subnets across 3 AZs
#   - EKS cluster with managed node groups
#   - Aurora PostgreSQL 17 (multi-AZ, encrypted)
#   - S3 buckets with Object Lock (WORM evidence store)
#   - MSK Kafka cluster (audit event stream)
#   - KMS keys (encryption at rest)
#   - WAF web ACL
#   - IAM roles + IRSA for pod-level AWS access
#   - Route53 DNS + health checks
#   - ECR container registries
########################################################################

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
  }

  backend "s3" {
    bucket         = "ct-terraform-state"
    key            = "control-tower/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ct-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "control-tower"
      Environment = var.environment
      ManagedBy   = "terraform"
      Team        = "model-control"
    }
  }
}

# ── Data Sources ─────────────────────────────────────────────
data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name       = "control-tower-${var.environment}"
  azs        = slice(data.aws_availability_zones.available.names, 0, 3)
  account_id = data.aws_caller_identity.current.account_id
}

# ── VPC ──────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.16"

  name = local.name
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i + 4)]
  database_subnets = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 4, i + 8)]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "production"
  enable_dns_hostnames = true
  enable_dns_support   = true

  create_database_subnet_group = true
  database_subnet_group_name   = "${local.name}-db"

  # Tag subnets for EKS auto-discovery
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
    "kubernetes.io/cluster/${local.name}" = "shared"
  }
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
}

# ── KMS Keys ─────────────────────────────────────────────────
resource "aws_kms_key" "main" {
  description             = "Control Tower encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "main" {
  name          = "alias/${local.name}"
  target_key_id = aws_kms_key.main.key_id
}

# ── EKS Cluster ──────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = local.name
  cluster_version = "1.31"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = var.environment != "production"
  cluster_endpoint_private_access = true

  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.main.arn
    resources        = ["secrets"]
  }

  eks_managed_node_groups = {
    app = {
      name           = "${local.name}-app"
      instance_types = var.eks_instance_types
      min_size       = var.eks_min_nodes
      max_size       = var.eks_max_nodes
      desired_size   = var.eks_desired_nodes

      labels = {
        role = "app"
      }
    }
  }

  # IRSA for Vault, S3, KMS access
  enable_irsa = true
}

# ── Aurora PostgreSQL 17 ─────────────────────────────────────
module "rds" {
  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "~> 9.12"

  name           = "${local.name}-db"
  engine         = "aurora-postgresql"
  engine_version = "17.2"
  instance_class = var.db_instance_class

  instances = {
    writer = {}
    reader = {}
  }

  vpc_id               = module.vpc.vpc_id
  db_subnet_group_name = module.vpc.database_subnet_group_name
  security_group_rules = {
    ingress = {
      cidr_blocks = module.vpc.private_subnets_cidr_blocks
    }
  }

  master_username = "ct_admin"
  database_name   = "control_tower"

  storage_encrypted   = true
  kms_key_id          = aws_kms_key.main.arn
  deletion_protection = var.environment == "production"

  backup_retention_period = var.environment == "production" ? 35 : 7
  preferred_backup_window = "02:00-03:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  apply_immediately = var.environment != "production"
}

# ── S3 Evidence Buckets (WORM) ───────────────────────────────
resource "aws_s3_bucket" "evidence" {
  bucket = "${local.name}-evidence"
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "evidence" {
  bucket              = aws_s3_bucket.evidence.id
  object_lock_enabled = "Enabled"

  rule {
    default_retention {
      mode = "GOVERNANCE"
      days = var.evidence_retention_days
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket                  = aws_s3_bucket.evidence.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name}-artifacts"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── MSK Kafka ────────────────────────────────────────────────
resource "aws_msk_cluster" "audit" {
  cluster_name           = "${local.name}-audit"
  kafka_version          = "3.7.x.kraft"
  number_of_broker_nodes = var.environment == "production" ? 6 : 3

  broker_node_group_info {
    instance_type  = var.msk_instance_type
    client_subnets = module.vpc.private_subnets

    storage_info {
      ebs_storage_info {
        volume_size = var.msk_volume_size_gb
      }
    }

    security_groups = [aws_security_group.msk.id]
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.main.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.audit.arn
    revision = aws_msk_configuration.audit.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }
}

resource "aws_msk_configuration" "audit" {
  name              = "${local.name}-audit-config"
  kafka_versions    = ["3.7.x.kraft"]
  server_properties = <<-PROPS
    auto.create.topics.enable=false
    default.replication.factor=3
    min.insync.replicas=2
    log.retention.hours=168
    log.retention.bytes=107374182400
  PROPS
}

resource "aws_security_group" "msk" {
  name_prefix = "${local.name}-msk-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9098
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "msk" {
  name              = "/aws/msk/${local.name}"
  retention_in_days = 90
}

# ── WAF ──────────────────────────────────────────────────────
resource "aws_wafv2_web_acl" "main" {
  name        = local.name
  scope       = "REGIONAL"
  description = "Control Tower API protection"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "ct-common-rules"
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 2
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "ct-sqli-rules"
    }
  }

  rule {
    name     = "RateLimit"
    priority = 10
    action { block {} }
    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "ct-rate-limit"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "ct-waf"
  }
}

# ── ECR Repositories ─────────────────────────────────────────
resource "aws_ecr_repository" "backend" {
  name                 = "control-tower/backend"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.main.arn
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "control-tower/frontend"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.main.arn
  }
}

# ── IAM Roles (IRSA) ────────────────────────────────────────
module "irsa_backend" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.47"

  role_name = "${local.name}-backend"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["control-tower:control-tower-backend"]
    }
  }

  role_policy_arns = {
    s3       = aws_iam_policy.s3_access.arn
    kms      = aws_iam_policy.kms_access.arn
  }
}

resource "aws_iam_policy" "s3_access" {
  name = "${local.name}-s3-access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject", "s3:PutObject", "s3:ListBucket",
          "s3:GetObjectVersion", "s3:GetBucketObjectLockConfiguration",
        ]
        Resource = [
          aws_s3_bucket.evidence.arn,
          "${aws_s3_bucket.evidence.arn}/*",
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "kms_access" {
  name = "${local.name}-kms-access"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"]
        Resource = [aws_kms_key.main.arn]
      }
    ]
  })
}
