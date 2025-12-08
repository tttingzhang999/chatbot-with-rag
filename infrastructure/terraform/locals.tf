#=============================================================================
# COMPUTED VALUES
# These values are derived from input variables and should not be modified
#=============================================================================

locals {
  # Full domain names
  frontend_domain = "${var.app_subdomain}.${var.root_domain}"
  api_domain      = "api.${var.app_subdomain}.${var.root_domain}"

  # S3 bucket names (must be globally unique)
  documents_bucket_name = "${var.project_prefix}-${var.project_name}-documents-${var.aws_region}"
  frontend_bucket_name  = "${var.project_prefix}-${var.project_name}-frontend"

  # ECR image URI
  lambda_image_uri = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.lambda_ecr_repository}:${var.lambda_image_tag}"

  # IAM role ARN
  lambda_role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.lambda_iam_role_name}"

  # Common tags applied to all resources
  common_tags = {
    Managed   = "terraform"
    Source    = var.github_repository
    Retention = var.retention_date
    Owner     = var.owner_name
    Project   = var.project_name
  }

  # VPC endpoint service names
  secretsmanager_endpoint_service  = "com.amazonaws.${var.aws_region}.secretsmanager"
  bedrock_runtime_endpoint_service = "com.amazonaws.${var.aws_region}.bedrock-runtime"

  # Secrets Manager secret names
  app_secret_name = "${var.project_name}/app-secrets"
  db_secret_name  = "${var.project_name}/database"

  # Lambda environment variables
  lambda_environment_vars = {
    # Security & Database
    APP_SECRET_NAME = local.app_secret_name
    DB_SECRET_NAME  = local.db_secret_name

    # S3 Configuration
    DOCUMENT_BUCKET    = local.documents_bucket_name
    USE_PRESIGNED_URLS = tostring(var.use_presigned_urls)

    # LLM Models
    CONVERSATION_LLM_MODEL_ID = var.conversation_llm_model_id
    TITLE_LLM_MODEL_ID        = var.title_llm_model_id
    EMBEDDING_MODEL_ID        = var.embedding_model_id

    # RAG Configuration
    ENABLE_RAG = tostring(var.enable_rag)

    # CORS Configuration (JSON array format for Pydantic Settings)
    CORS_ORIGINS = jsonencode(["https://${local.frontend_domain}"])
  }
}
