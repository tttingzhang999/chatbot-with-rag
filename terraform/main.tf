terraform {
  required_version = "~> 1.13"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket              = "gc-playground-tfstates"
    key                 = "tttingzhang999/chatbot-with-rag.tfstate"
    region              = "ap-northeast-1"
    profile             = "tf-gc-playground"
    allowed_account_ids = ["593713876380"]
  }
}

provider "aws" {
  region              = "ap-northeast-1"
  profile             = "tf-gc-playground"
  allowed_account_ids = ["593713876380"]

  default_tags {
    tags = {
      Managed   = "terraform"
      Source    = "tttingzhang999/chatbot-with-rag"
      Retention = "2025-12-31"
      Owner     = "TingZhang"
      Project   = "hr-chatbot"
    }
  }
}

# Additional provider for us-east-1 (required for ACM certificates used with App Runner)
provider "aws" {
  alias               = "us-east-1"
  region              = "us-east-1"
  profile             = "tf-gc-playground"
  allowed_account_ids = ["593713876380"]

  default_tags {
    tags = {
      Managed   = "terraform"
      Source    = "tttingzhang999/chatbot-with-rag"
      Retention = "2025-12-31"
      Owner     = "TingZhang"
      Project   = "hr-chatbot"
    }
  }
}

# Additional provider for Route 53 (hosted zone in different AWS account)
provider "aws" {
  alias               = "route53"
  region              = "ap-northeast-1"
  profile             = "tf-gc-dns"
  allowed_account_ids = ["368617320415"]

  default_tags {
    tags = {
      Managed   = "terraform"
      Source    = "tttingzhang999/chatbot-with-rag"
      Retention = "2025-12-31"
      Owner     = "TingZhang"
      Project   = "hr-chatbot"
    }
  }
}
