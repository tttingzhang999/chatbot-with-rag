terraform {
  required_version = "~> 1.13"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Backend configuration is provided via backend.tfvars at init time
  # Run: terraform init -backend-config=backend.tfvars
  backend "s3" {}
}

provider "aws" {
  region              = var.aws_region
  profile             = var.aws_profile
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = local.common_tags
  }
}

# Additional provider for us-east-1 (required for ACM certificates used with CloudFront)
provider "aws" {
  alias               = "us-east-1"
  region              = "us-east-1"
  profile             = var.aws_profile
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = local.common_tags
  }
}

# Additional provider for Route 53 (hosted zone in different AWS account)
provider "aws" {
  alias               = "route53"
  region              = var.aws_region
  profile             = var.route53_aws_profile
  allowed_account_ids = [var.route53_aws_account_id]

  default_tags {
    tags = local.common_tags
  }
}
