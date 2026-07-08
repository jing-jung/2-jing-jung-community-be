# =============================================================================
# Amazon ElastiCache (Redis)
# =============================================================================

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.project_name}-redis-subnet-group"
  }
}

# Redis Replication Group (Cluster Mode Disabled)
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-redis"
  replication_group_description = "Redis cluster for ${var.project_name}"
  
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.redis_node_type
  num_cache_clusters   = var.redis_num_cache_nodes
  port                 = 6379
  
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  # Automatic Failover (Multi-AZ)
  automatic_failover_enabled = var.redis_num_cache_nodes > 1 ? true : false
  multi_az_enabled          = var.redis_num_cache_nodes > 1 ? true : false

  # Backup Configuration
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "mon:05:00-mon:07:00"

  # At-Rest Encryption
  at_rest_encryption_enabled = true
  
  # In-Transit Encryption
  transit_encryption_enabled = false  # 성능을 위해 비활성화, 필요시 true

  # Auto Minor Version Upgrade
  auto_minor_version_upgrade = true

  # Notification
  notification_topic_arn = aws_sns_topic.redis_alerts.arn

  tags = {
    Name = "${var.project_name}-redis"
  }
}

# Redis Parameter Group
resource "aws_elasticache_parameter_group" "redis" {
  name   = "${var.project_name}-redis-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = {
    Name = "${var.project_name}-redis-params"
  }
}

# SNS Topic for Redis Alerts
resource "aws_sns_topic" "redis_alerts" {
  name = "${var.project_name}-redis-alerts"

  tags = {
    Name = "${var.project_name}-redis-alerts"
  }
}
