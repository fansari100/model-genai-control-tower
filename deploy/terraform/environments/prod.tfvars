########################################################################
# Control Tower – Production Environment
########################################################################
environment         = "production"
aws_region          = "us-east-1"
vpc_cidr            = "10.0.0.0/16"
eks_instance_types  = ["m6i.xlarge", "m6i.2xlarge"]
eks_min_nodes       = 3
eks_max_nodes       = 20
eks_desired_nodes   = 6
db_instance_class   = "db.r6g.xlarge"
msk_instance_type   = "kafka.m5.large"
msk_volume_size_gb  = 500
evidence_retention_days = 2555  # ~7 years regulatory
waf_rate_limit      = 2000
