#!/bin/bash

# Deployment Configuration Helper
# This script reads configuration from Terraform outputs and tfvars
# Source this file in your deployment scripts: source "$(dirname "$0")/config.sh"

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/infrastructure/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to read value from terraform.tfvars
read_tfvar() {
  local var_name="$1"
  local tfvars_file="${TERRAFORM_DIR}/terraform.tfvars"

  if [ ! -f "$tfvars_file" ]; then
    echo -e "${RED}Error: terraform.tfvars not found at ${tfvars_file}${NC}" >&2
    echo -e "${YELLOW}Please create it from terraform.tfvars.example${NC}" >&2
    exit 1
  fi

  # Parse tfvars file (handles simple string values)
  grep "^${var_name}[[:space:]]*=" "$tfvars_file" | sed 's/^[^=]*=[[:space:]]*"\([^"]*\)".*/\1/' | tr -d '\n'
}

# Function to get Terraform output value
get_terraform_output() {
  local output_name="$1"
  local output_value

  # Change to terraform directory
  pushd "${TERRAFORM_DIR}" > /dev/null

  # Get terraform output
  output_value=$(terraform output -raw "${output_name}" 2>/dev/null || echo "")

  popd > /dev/null

  if [ -z "$output_value" ]; then
    echo -e "${YELLOW}Warning: Terraform output '${output_name}' not found or empty${NC}" >&2
    echo -e "${YELLOW}Run 'cd ${TERRAFORM_DIR} && terraform apply' first${NC}" >&2
  fi

  echo "$output_value"
}

# Read configuration from terraform.tfvars
echo -e "${GREEN}Reading configuration from Terraform...${NC}"

export AWS_ACCOUNT_ID=$(read_tfvar "aws_account_id")
export AWS_REGION=$(read_tfvar "aws_region")
export AWS_PROFILE=$(read_tfvar "aws_profile")
export PROJECT_PREFIX=$(read_tfvar "project_prefix")
export PROJECT_NAME=$(read_tfvar "project_name")
export LAMBDA_ECR_REPOSITORY=$(read_tfvar "lambda_ecr_repository")
export LAMBDA_IMAGE_TAG=$(read_tfvar "lambda_image_tag")

# Read values from Terraform outputs (these are actual deployed resources)
export S3_BUCKET=$(get_terraform_output "s3_bucket_name")
export CLOUDFRONT_DISTRIBUTION_ID=$(get_terraform_output "cloudfront_distribution_id")
export FRONTEND_URL=$(get_terraform_output "frontend_url")

# Construct Lambda function name (matches terraform naming convention: ${project_name}-backend)
export LAMBDA_FUNCTION_NAME="${PROJECT_NAME}-backend"

# Construct ECR image URI
export ECR_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${LAMBDA_ECR_REPOSITORY}:${LAMBDA_IMAGE_TAG}"

# Validate required variables
validate_config() {
  local missing_vars=()

  [ -z "$AWS_ACCOUNT_ID" ] && missing_vars+=("aws_account_id")
  [ -z "$AWS_REGION" ] && missing_vars+=("aws_region")
  [ -z "$AWS_PROFILE" ] && missing_vars+=("aws_profile")
  [ -z "$PROJECT_PREFIX" ] && missing_vars+=("project_prefix")
  [ -z "$PROJECT_NAME" ] && missing_vars+=("project_name")

  if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}Error: Missing required configuration variables:${NC}" >&2
    for var in "${missing_vars[@]}"; do
      echo -e "${RED}  - ${var}${NC}" >&2
    done
    echo -e "${YELLOW}Please check your terraform.tfvars file${NC}" >&2
    exit 1
  fi
}

validate_config

echo -e "${GREEN}Configuration loaded successfully!${NC}"
