########################################################################
# Control Tower – Terraform Variables
########################################################################

variable "aws_region" {
  description = "AWS region for primary deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# ── EKS ──────────────────────────────────────────────────────
variable "eks_instance_types" {
  description = "EC2 instance types for EKS managed node group"
  type        = list(string)
  default     = ["m6i.xlarge"]
}

variable "eks_min_nodes" {
  description = "Minimum nodes in EKS node group"
  type        = number
  default     = 3
}

variable "eks_max_nodes" {
  description = "Maximum nodes in EKS node group"
  type        = number
  default     = 20
}

variable "eks_desired_nodes" {
  description = "Desired nodes in EKS node group"
  type        = number
  default     = 3
}

# ── RDS ──────────────────────────────────────────────────────
variable "db_instance_class" {
  description = "RDS Aurora instance class"
  type        = string
  default     = "db.r6g.large"
}

# ── S3 ───────────────────────────────────────────────────────
variable "evidence_retention_days" {
  description = "Default WORM retention period for evidence artifacts (days)"
  type        = number
  default     = 2555  # ~7 years (regulatory retention)
}

# ── MSK ──────────────────────────────────────────────────────
variable "msk_instance_type" {
  description = "MSK broker instance type"
  type        = string
  default     = "kafka.m5.large"
}

variable "msk_volume_size_gb" {
  description = "EBS volume size per MSK broker (GB)"
  type        = number
  default     = 500
}

# ── WAF ──────────────────────────────────────────────────────
variable "waf_rate_limit" {
  description = "WAF rate limit (requests per 5-minute window per IP)"
  type        = number
  default     = 2000
}
