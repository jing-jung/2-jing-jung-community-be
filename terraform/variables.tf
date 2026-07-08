# =============================================================================
# Variables
# =============================================================================

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "community-be"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability Zones"
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
}

# EKS Configuration
variable "eks_cluster_name" {
  description = "EKS Cluster Name"
  type        = string
  default     = "community-eks-cluster"
}

variable "eks_node_instance_type" {
  description = "EKS Worker Node Instance Type"
  type        = string
  default     = "t3.medium"
}

variable "eks_node_desired_size" {
  description = "EKS Node Group Desired Size"
  type        = number
  default     = 2
}

variable "eks_node_min_size" {
  description = "EKS Node Group Min Size"
  type        = number
  default     = 2
}

variable "eks_node_max_size" {
  description = "EKS Node Group Max Size"
  type        = number
  default     = 10
}

# RDS Configuration
variable "db_instance_class" {
  description = "RDS Instance Class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Database Name"
  type        = string
  default     = "communitydb"
}

variable "db_username" {
  description = "Database Username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database Password"
  type        = string
  sensitive   = true
}

variable "db_allocated_storage" {
  description = "RDS Allocated Storage (GB)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "RDS Max Allocated Storage (GB)"
  type        = number
  default     = 100
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis Node Type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis Cache Nodes"
  type        = number
  default     = 1
}

# Tags
variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
