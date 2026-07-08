# =============================================================================
# Outputs
# =============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "EKS Cluster Name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS Cluster Endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_security_group_id" {
  description = "EKS Cluster Security Group ID"
  value       = module.eks.cluster_security_group_id
}

output "configure_kubectl" {
  description = "Configure kubectl command"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "rds_primary_endpoint" {
  description = "RDS Primary Endpoint"
  value       = aws_db_instance.primary.endpoint
  sensitive   = true
}

output "rds_replica_endpoint" {
  description = "RDS Read Replica Endpoint"
  value       = aws_db_instance.replica.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis Primary Endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR Repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "backend_pod_role_arn" {
  description = "Backend Pod IAM Role ARN (for IRSA)"
  value       = aws_iam_role.backend_pod_role.arn
}

# 배포에 필요한 모든 정보 출력
output "deployment_info" {
  description = "All deployment information"
  value = {
    aws_region        = var.aws_region
    eks_cluster_name  = module.eks.cluster_name
    db_host          = split(":", aws_db_instance.primary.endpoint)[0]
    db_replica_host  = split(":", aws_db_instance.replica.endpoint)[0]
    redis_host       = aws_elasticache_replication_group.redis.primary_endpoint_address
    ecr_url          = aws_ecr_repository.backend.repository_url
    backend_role_arn = aws_iam_role.backend_pod_role.arn
  }
  sensitive = true
}
