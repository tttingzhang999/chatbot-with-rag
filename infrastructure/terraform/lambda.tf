resource "aws_lambda_function" "hr-chatbot-backend" {
  function_name                  = "hr-chatbot-backend"
  package_type                   = "Image"
  image_uri                      = "593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/ting-assignment/hr-chatbot-backend:latest"
  role                           = "arn:aws:iam::593713876380:role/hr-chatbot-lambda-role"
  architectures                  = ["arm64"]
  reserved_concurrent_executions = 1
  timeout                        = 60
  memory_size                    = 1024
  publish                        = false

  vpc_config {
    ipv6_allowed_for_dual_stack = false
    security_group_ids = [
      "sg-0dfc84b0acf5f5565"
    ]
    subnet_ids = [
      "subnet-0815a8642250d1459",
      "subnet-0b7dc9e7411b5bec4"
    ]
  }

  environment {
    variables = {
      # Security & Database
      APP_SECRET_NAME = "hr-chatbot/app-secrets"
      DB_SECRET_NAME  = "hr-chatbot/database"

      # S3 Configuration
      DOCUMENT_BUCKET    = "hr-chatbot-documents-ap-northeast-1"
      USE_PRESIGNED_URLS = "true"

      # LLM Models
      CONVERSATION_LLM_MODEL_ID = "amazon.nova-lite-v1:0"
      TITLE_LLM_MODEL_ID        = "amazon.nova-lite-v1:0"
      EMBEDDING_MODEL_ID        = "cohere.embed-v4:0"

      # RAG Configuration
      ENABLE_RAG = "true"

      # CORS Configuration (JSON array format for Pydantic Settings)
      CORS_ORIGINS = "[\"https://ting-hr-chatbot.goingcloud.ai\"]"
    }
  }

  tags = {
    Managed   = "terraform"
    Owner     = "TingZhang"
    Project   = "hr-chatbot"
    Retention = "2025-12-31"
    Source    = "tttingzhang999/chatbot-with-rag"
  }
}
