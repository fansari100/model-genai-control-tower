########################################################################
# Control Tower – Terraform Outputs
#
# These values are consumed by Helm (via --set or values files)
# and by the CI/CD pipeline for deployment.
########################################################################

# ── VPC ──────────────────────────────────────────────────────
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for EKS workloads"
  value       = module.vpc.private_subnets
}

# ── EKS ──────────────────────────────────────────────────────
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API server endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_oidc_provider_arn" {
  description = "EKS OIDC provider ARN (for IRSA)"
  value       = module.eks.oidc_provider_arn
}

# ── RDS ──────────────────────────────────────────────────────
output "rds_cluster_endpoint" {
  description = "Aurora writer endpoint"
  value       = module.rds.cluster_endpoint
  sensitive   = true
}

output "rds_reader_endpoint" {
  description = "Aurora reader endpoint"
  value       = module.rds.cluster_reader_endpoint
  sensitive   = true
}

output "rds_database_name" {
  description = "Database name"
  value       = "control_tower"
}

# ── S3 ───────────────────────────────────────────────────────
output "s3_evidence_bucket" {
  description = "S3 evidence bucket name (WORM-enabled)"
  value       = aws_s3_bucket.evidence.id
}

output "s3_artifacts_bucket" {
  description = "S3 artifacts bucket name"
  value       = aws_s3_bucket.artifacts.id
}

# ── MSK ──────────────────────────────────────────────────────
output "msk_bootstrap_brokers_tls" {
  description = "MSK bootstrap brokers (TLS)"
  value       = aws_msk_cluster.audit.bootstrap_brokers_tls
  sensitive   = true
}

# ── KMS ──────────────────────────────────────────────────────
output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.main.arn
}

# ── WAF ──────────────────────────────────────────────────────
output "waf_web_acl_arn" {
  description = "WAF Web ACL ARN (attach to ALB)"
  value       = aws_wafv2_web_acl.main.arn
}

# ── ECR ──────────────────────────────────────────────────────
output "ecr_backend_url" {
  description = "ECR repository URL for backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

# ── IAM ──────────────────────────────────────────────────────
output "backend_irsa_role_arn" {
  description = "IAM role ARN for backend service account (IRSA)"
  value       = module.irsa_backend.iam_role_arn
}
