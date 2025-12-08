#=============================================================================
# PROJECT IDENTITY
#=============================================================================

variable "project_name" {
  description = "Project name used for resource naming (e.g., 'hr-chatbot')"
  type        = string
  default     = "hr-chatbot"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "project_prefix" {
  description = "Unique prefix for S3 buckets and other globally unique resources (e.g., 'ting', 'mycompany'). This helps avoid naming conflicts."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_prefix))
    error_message = "Project prefix must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "owner_name" {
  description = "Owner name for resource tagging (e.g., 'JohnDoe', 'TeamName')"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in format 'username/repo-name' for source tracking"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-]+/[a-zA-Z0-9-]+$", var.github_repository))
    error_message = "GitHub repository must be in format 'username/repo-name'."
  }
}

variable "retention_date" {
  description = "Resource retention date in YYYY-MM-DD format for lifecycle tracking"
  type        = string
  default     = "2026-12-31"

  validation {
    condition     = can(regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", var.retention_date))
    error_message = "Retention date must be in YYYY-MM-DD format."
  }
}

#=============================================================================
# DOMAIN CONFIGURATION
#=============================================================================

variable "root_domain" {
  description = "Root domain name (e.g., 'example.com', 'goingcloud.ai')"
  type        = string
}

variable "app_subdomain" {
  description = "Subdomain for the application frontend (e.g., 'app', 'hr-chatbot'). Full domain will be '{app_subdomain}.{root_domain}'"
  type        = string
}

variable "route53_hosted_zone_id" {
  description = "Route 53 Hosted Zone ID for the root domain. Find this in AWS Console > Route 53 > Hosted zones"
  type        = string

  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.route53_hosted_zone_id))
    error_message = "Route 53 Hosted Zone ID must start with 'Z' followed by alphanumeric characters."
  }
}

#=============================================================================
# AWS ACCOUNT CONFIGURATION
#=============================================================================

variable "aws_account_id" {
  description = "Primary AWS Account ID (12 digits) where main resources are deployed"
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "AWS Account ID must be exactly 12 digits."
  }
}

variable "aws_profile" {
  description = "AWS CLI profile name for the primary account (used with aws-vault or AWS CLI)"
  type        = string
}

variable "route53_aws_account_id" {
  description = "AWS Account ID for Route 53 (if different from primary account). Use same as aws_account_id if Route 53 is in the same account."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.route53_aws_account_id))
    error_message = "AWS Account ID must be exactly 12 digits."
  }
}

variable "route53_aws_profile" {
  description = "AWS CLI profile name for Route 53 account. Use same as aws_profile if Route 53 is in the same account."
  type        = string
}

variable "aws_region" {
  description = "Primary AWS region for resource deployment"
  type        = string
  default     = "ap-northeast-1"
}

#=============================================================================
# VPC & NETWORK CONFIGURATION
#=============================================================================

variable "lambda_security_group_ids" {
  description = "List of security group IDs for Lambda function VPC access"
  type        = list(string)

  validation {
    condition     = length(var.lambda_security_group_ids) > 0
    error_message = "At least one security group ID is required."
  }
}

variable "lambda_subnet_ids" {
  description = "List of subnet IDs for Lambda function VPC access (use private subnets)"
  type        = list(string)

  validation {
    condition     = length(var.lambda_subnet_ids) >= 2
    error_message = "At least two subnet IDs are required for high availability."
  }
}

variable "database_availability_zones" {
  description = "List of availability zones for Aurora PostgreSQL cluster"
  type        = list(string)

  validation {
    condition     = length(var.database_availability_zones) >= 2
    error_message = "At least two availability zones are required for high availability."
  }
}

variable "vpc_cidr_blocks" {
  description = "CIDR blocks for VPC subnets. Provide at least two for high availability."
  type        = list(string)
  default     = ["10.0.0.0/25", "10.0.0.128/25"]

  validation {
    condition     = length(var.vpc_cidr_blocks) >= 2
    error_message = "At least two CIDR blocks are required for high availability."
  }
}

#=============================================================================
# LAMBDA CONFIGURATION
#=============================================================================

variable "lambda_ecr_repository" {
  description = "ECR repository name for Lambda container image (format: 'assignment-name/app-name' or 'app-name')"
  type        = string
  default     = "ting-assignment/hr-chatbot-backend"
}

variable "lambda_image_tag" {
  description = "Docker image tag for Lambda function"
  type        = string
  default     = "latest"
}

variable "lambda_iam_role_name" {
  description = "Name of the existing IAM role for Lambda execution. This role must already exist with appropriate permissions."
  type        = string
  default     = "hr-chatbot-lambda-role"
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB (128-10240)"
  type        = number
  default     = 1024

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 and 10240 MB."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds (1-900)"
  type        = number
  default     = 60

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_reserved_concurrent_executions" {
  description = "Reserved concurrent executions for Lambda (-1 for unreserved)"
  type        = number
  default     = 1
}

variable "lambda_architecture" {
  description = "Lambda function architecture (x86_64 or arm64)"
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.lambda_architecture)
    error_message = "Lambda architecture must be either 'x86_64' or 'arm64'."
  }
}

#=============================================================================
# APPLICATION CONFIGURATION
#=============================================================================

variable "conversation_llm_model_id" {
  description = "Amazon Bedrock model ID for conversation (e.g., 'amazon.nova-lite-v1:0', 'anthropic.claude-sonnet-4')"
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "title_llm_model_id" {
  description = "Amazon Bedrock model ID for title generation"
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "embedding_model_id" {
  description = "Amazon Bedrock model ID for embeddings (e.g., 'cohere.embed-v4:0')"
  type        = string
  default     = "cohere.embed-v4:0"
}

variable "enable_rag" {
  description = "Enable Retrieval-Augmented Generation (RAG) features"
  type        = bool
  default     = true
}

variable "use_presigned_urls" {
  description = "Use presigned URLs for S3 uploads"
  type        = bool
  default     = true
}

#=============================================================================
# CLOUDFRONT CONFIGURATION
#=============================================================================

variable "cloudfront_price_class" {
  description = "CloudFront distribution price class (PriceClass_100, PriceClass_200, PriceClass_All)"
  type        = string
  default     = "PriceClass_200"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "Invalid CloudFront price class. Must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

#=============================================================================
# LOGGING & MONITORING
#=============================================================================

variable "api_gateway_log_retention_days" {
  description = "CloudWatch log retention in days for API Gateway"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.api_gateway_log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

#=============================================================================
# DATABASE CONFIGURATION
#=============================================================================

variable "database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "hr_chatbot"

  validation {
    condition     = can(regex("^[a-z_][a-z0-9_]*$", var.database_name))
    error_message = "Database name must start with a letter or underscore and contain only lowercase letters, numbers, and underscores."
  }
}

variable "database_master_username" {
  description = "Master username for PostgreSQL database"
  type        = string
  default     = "postgres"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.database_master_username))
    error_message = "Database username must start with a letter and contain only letters, numbers, and underscores."
  }
}
