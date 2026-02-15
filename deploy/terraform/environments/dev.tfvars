########################################################################
# Control Tower – Development Environment
########################################################################
environment         = "development"
aws_region          = "us-east-1"
vpc_cidr            = "10.0.0.0/16"
eks_instance_types  = ["m6i.large"]
eks_min_nodes       = 2
eks_max_nodes       = 5
eks_desired_nodes   = 2
db_instance_class   = "db.r6g.medium"
msk_instance_type   = "kafka.t3.small"
msk_volume_size_gb  = 100
evidence_retention_days = 30
waf_rate_limit      = 5000
