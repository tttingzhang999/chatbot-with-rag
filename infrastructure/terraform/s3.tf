# S3 bucket for document uploads
resource "aws_s3_bucket" "example" {
  bucket = "hr-chatbot-documents-ap-northeast-1"

  tags = {
    Owner     = "TingZhang"
    Retention = "2025-12-31"
  }
}

# CORS configuration for direct browser uploads to S3 (presigned URLs)
resource "aws_s3_bucket_cors_configuration" "example" {
  bucket = aws_s3_bucket.example.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "PUT"]
    allowed_origins = [
      "https://ting-hr-chatbot.goingcloud.ai", # Production frontend (CloudFront)
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Enable versioning for document bucket
resource "aws_s3_bucket_versioning" "example" {
  bucket = aws_s3_bucket.example.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.example.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}
