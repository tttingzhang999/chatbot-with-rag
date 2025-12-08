# HR Chatbot Terraform Setup Guide

This guide will help you deploy the HR Chatbot infrastructure to your own AWS account.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Account Setup Options](#account-setup-options)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Prerequisites

Before you begin, ensure you have:

### 1. AWS Account & Permissions

- An AWS account with administrative access
- AWS CLI installed and configured
- (Optional but recommended) [aws-vault](https://github.com/99designs/aws-vault) for credential management

### 2. Domain & DNS

- A registered domain name
- A Route 53 hosted zone for your domain
  - Go to AWS Console > Route 53 > Hosted zones
  - Note down the **Hosted Zone ID** (starts with 'Z')

### 3. VPC Infrastructure

You need an existing VPC with:

- At least **2 private subnets** in different Availability Zones
- A **security group** with the following rules:
  - Outbound HTTPS (443) - for AWS API access
  - Outbound PostgreSQL (5432) - for database access
- **NAT Gateway** or **VPC Endpoints** for internet access from private subnets

**To create VPC infrastructure:**

```bash
# Option 1: Use AWS Console
AWS Console > VPC > Create VPC > VPC and more
- Select "VPC with Public and Private Subnets"
- Choose 2 Availability Zones
- Enable NAT Gateway

# Option 2: Use existing VPC
Just note down your subnet IDs and security group IDs
```

### 4. IAM Role for Lambda

Create an IAM role named `hr-chatbot-lambda-role` (or customize the name) with these policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::*-hr-chatbot-documents-*/*"
    },
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:*:*:secret:hr-chatbot/*"
    }
  ]
}
```

Also attach these AWS managed policies:

- `AWSLambdaVPCAccessExecutionRole`
- `AWSLambdaBasicExecutionRole`

### 5. ECR Repository

Create an ECR repository for your Lambda container image:

```bash
aws ecr create-repository \
  --repository-name your-assignment/hr-chatbot-backend \
  --region us-east-1
```

Then build and push your Docker image (see main README for instructions).

### 6. S3 Backend Bucket

Create an S3 bucket for storing Terraform state:

```bash
aws s3 mb s3://my-terraform-state-bucket --region us-east-1
aws s3api put-bucket-versioning \
  --bucket my-terraform-state-bucket \
  --versioning-configuration Status=Enabled
```

### 7. Tools

- Terraform >= 1.13 ([installation guide](https://www.terraform.io/downloads))

```bash
# Verify installation
terraform version
```

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name/infrastructure/terraform
```

### Step 2: Configure Terraform Variables

Copy the example files and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
cp backend.tfvars.example backend.tfvars
```

Edit `terraform.tfvars`:

```hcl
# Minimum required configuration
project_prefix    = "mycompany"  # Your unique prefix
owner_name        = "YourName"
github_repository = "yourusername/your-repo-name"

# Domain configuration
root_domain            = "example.com"
app_subdomain          = "hr-chatbot"
route53_hosted_zone_id = "Z0123456789ABCDEFGH"

# AWS account
aws_account_id         = "123456789012"
aws_profile            = "default"
route53_aws_account_id = "123456789012"  # Same if single account
route53_aws_profile    = "default"       # Same if single account
aws_region             = "us-east-1"

# VPC resources
lambda_security_group_ids   = ["sg-0123456789abcdef0"]
lambda_subnet_ids           = ["subnet-abc123", "subnet-def456"]
database_availability_zones = ["us-east-1a", "us-east-1b"]

# Lambda configuration
lambda_ecr_repository = "your-assignment/hr-chatbot-backend"
```

Edit `backend.tfvars`:

```hcl
bucket              = "my-terraform-state-bucket"
key                 = "yourusername/hr-chatbot.tfstate"
region              = "us-east-1"
profile             = "default"
allowed_account_ids = ["123456789012"]
```

### Step 3: Initialize Terraform

```bash
terraform init -backend-config=backend.tfvars
```

You should see: `Terraform has been successfully initialized!`

### Step 4: Review the Plan

```bash
terraform plan -var-file=terraform.tfvars
```

Review the resources that will be created. You should see:

- Aurora PostgreSQL cluster
- Lambda function
- API Gateway
- CloudFront distribution
- S3 buckets
- Route 53 records
- VPC endpoints
- And more...

### Step 5: Apply the Configuration

```bash
terraform apply -var-file=terraform.tfvars
```

Type `yes` when prompted. This will take 10-15 minutes.

### Step 6: Verify Deployment

After successful deployment, you'll see outputs:

```
Outputs:

api_endpoint = "https://api.hr-chatbot.example.com"
cloudfront_distribution_id = "E1234567890ABC"
frontend_url = "https://hr-chatbot.example.com"
```

Visit the frontend URL to verify your deployment.

## Configuration Reference

### Required Variables

| Variable                      | Description                  | Example                        |
| ----------------------------- | ---------------------------- | ------------------------------ |
| `project_prefix`              | Unique prefix for S3 buckets | `"mycompany"`                  |
| `owner_name`                  | Owner name for tagging       | `"John Doe"`                   |
| `github_repository`           | GitHub repo path             | `"user/repo"`                  |
| `root_domain`                 | Your domain name             | `"example.com"`                |
| `app_subdomain`               | Subdomain for app            | `"hr-chatbot"`                 |
| `route53_hosted_zone_id`      | Route 53 zone ID             | `"Z01234567..."`               |
| `aws_account_id`              | AWS account ID (12 digits)   | `"123456789012"`               |
| `aws_profile`                 | AWS CLI profile              | `"default"`                    |
| `route53_aws_account_id`      | Route 53 account ID          | `"123456789012"`               |
| `route53_aws_profile`         | Route 53 profile             | `"default"`                    |
| `lambda_security_group_ids`   | Security group IDs           | `["sg-abc123"]`                |
| `lambda_subnet_ids`           | Subnet IDs (2+ required)     | `["subnet-abc", "subnet-def"]` |
| `database_availability_zones` | AZs for database             | `["us-east-1a", "us-east-1b"]` |

### Optional Variables (with defaults)

| Variable                         | Default                                | Description                |
| -------------------------------- | -------------------------------------- | -------------------------- |
| `project_name`                   | `"hr-chatbot"`                         | Project name for resources |
| `retention_date`                 | `"2026-12-31"`                         | Resource retention date    |
| `aws_region`                     | `"ap-northeast-1"`                     | Primary AWS region         |
| `lambda_ecr_repository`          | `"ting-assignment/hr-chatbot-backend"` | ECR repository name        |
| `lambda_image_tag`               | `"latest"`                             | Docker image tag           |
| `lambda_memory_size`             | `1024`                                 | Lambda memory (MB)         |
| `lambda_timeout`                 | `60`                                   | Lambda timeout (seconds)   |
| `lambda_architecture`            | `"arm64"`                              | Lambda architecture        |
| `conversation_llm_model_id`      | `"amazon.nova-lite-v1:0"`              | LLM model for chat         |
| `embedding_model_id`             | `"cohere.embed-v4:0"`                  | Embedding model            |
| `cloudfront_price_class`         | `"PriceClass_200"`                     | CloudFront price class     |
| `api_gateway_log_retention_days` | `7`                                    | Log retention days         |
| `database_name`                  | `"hr_chatbot"`                         | PostgreSQL database name   |
| `database_master_username`       | `"postgres"`                           | Database username          |

## Account Setup Options

### Single Account Setup (Recommended for most users)

If all your resources (including Route 53) are in the same AWS account:

```hcl
aws_account_id         = "123456789012"
aws_profile            = "default"
route53_aws_account_id = "123456789012"  # Same as above
route53_aws_profile    = "default"       # Same as above
```

### Multi-Account Setup (Advanced)

If your Route 53 hosted zone is in a **different AWS account**:

```hcl
# Main account (for Lambda, S3, etc.)
aws_account_id = "111111111111"
aws_profile    = "main-account"

# DNS account (for Route 53)
route53_aws_account_id = "222222222222"
route53_aws_profile    = "dns-account"
```

**Prerequisites for multi-account setup:**

1. Configure cross-account access for ACM certificate validation
2. Ensure both profiles are configured in your AWS CLI or aws-vault
3. Verify permissions allow creating Route 53 records across accounts

## Troubleshooting

### Error: "Backend configuration changed"

**Solution:** Re-initialize Terraform:

```bash
terraform init -reconfigure -backend-config=backend.tfvars
```

### Error: "Invalid provider configuration"

**Cause:** AWS credentials not configured properly.

**Solution:** Verify your AWS profile:

```bash
# With AWS CLI
aws sts get-caller-identity --profile your-profile-name

# With aws-vault
aws-vault exec your-profile-name -- aws sts get-caller-identity
```

### Error: "Error creating ACM certificate"

**Cause:** Domain or Route 53 hosted zone issues.

**Solutions:**

1. Verify your domain is registered and the hosted zone exists
2. Check that `route53_hosted_zone_id` is correct
3. Ensure DNS delegation is set up correctly

### Error: "Error creating Lambda function"

**Possible causes:**

1. ECR image doesn't exist
2. IAM role doesn't exist or has wrong permissions
3. VPC/subnet configuration is incorrect

**Solutions:**

1. Verify ECR image exists: `aws ecr describe-images --repository-name your-repo`
2. Verify IAM role exists: `aws iam get-role --role-name hr-chatbot-lambda-role`
3. Verify subnets are in private subnets with NAT gateway access

### Error: "No changes. Infrastructure up-to-date"

**Cause:** This is not an error! It means Terraform detected no changes.

**Note:** If you just copied your configuration and expect changes, verify you correctly filled in `terraform.tfvars`.

### Permission Denied Errors

**Solution:** Ensure your AWS user/role has sufficient permissions:

```bash
# Required AWS permissions
- ec2:* (VPC, Security Groups, Subnets)
- lambda:* (Lambda functions)
- iam:PassRole (for Lambda role)
- s3:* (for S3 buckets)
- cloudfront:* (for CloudFront)
- apigateway:* (for API Gateway)
- route53:* (for DNS records)
- acm:* (for SSL certificates)
- rds:* (for Aurora database)
- secretsmanager:* (for Secrets Manager)
```

## Best Practices

### Security

1. **Never commit sensitive files:**
   - `terraform.tfvars` - Contains your private configuration
   - `backend.tfvars` - Contains your backend configuration
   - `*.tfstate` - Contains your infrastructure state
   - These are already in `.gitignore`, but double-check!

2. **Use aws-vault for credentials:**

   ```bash
   aws-vault add your-profile
   aws-vault exec your-profile -- terraform plan
   ```

3. **Enable S3 versioning on backend bucket:**

   ```bash
   aws s3api put-bucket-versioning \
     --bucket your-backend-bucket \
     --versioning-configuration Status=Enabled
   ```

4. **Use DynamoDB state locking** (optional but recommended):
   Add to `backend.tfvars`:
   ```hcl
   dynamodb_table = "terraform-state-lock"
   ```

### Testing

1. **Test in a separate AWS account first** before deploying to production
2. **Always run `terraform plan`** before `apply` to review changes
3. **Use workspaces** for managing multiple environments (if needed):
   ```bash
   terraform workspace new staging
   terraform workspace select production
   ```

### Cost Optimization

Monitor costs for these services:

- **Aurora PostgreSQL Serverless** - Main cost driver
- **CloudFront** - Data transfer costs
- **NAT Gateway** - If using NAT for VPC access
- **Bedrock API** - Based on usage (tokens)

**Tip:** Use `PriceClass_100` for CloudFront if you only serve US/EU traffic.

### Backup & Recovery

1. **S3 versioning** on backend bucket (automatically protects state)
2. **Aurora backups** are automatic (7 days retention by default)
3. **Snapshot before major changes:**
   ```bash
   aws rds create-db-cluster-snapshot \
     --db-cluster-identifier hr-chatbot-cluster \
     --db-cluster-snapshot-identifier hr-chatbot-backup-$(date +%Y%m%d)
   ```

### Updates & Maintenance

1. **Review and update regularly:**

   ```bash
   terraform plan  # Check for any drift
   ```

2. **Update Terraform providers:**

   ```bash
   terraform init -upgrade
   ```

3. **Monitor for deprecated resources:**
   - Check Terraform and AWS provider changelogs
   - Test updates in a non-production environment first

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [aws-vault Documentation](https://github.com/99designs/aws-vault)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review Terraform error messages carefully
3. Check AWS CloudWatch Logs for runtime errors
4. Open an issue on GitHub with:
   - Terraform version
   - Error message
   - Relevant configuration (remove sensitive data!)

---

**Happy deploying! 🚀**
