#!/bin/bash

# HR Chatbot Backend Deployment Script
# This script builds the backend Docker image and deploys to ECR + Lambda

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Load configuration from config.sh
source "${SCRIPT_DIR}/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Dockerfile path
DOCKERFILE_PATH="${PROJECT_ROOT}/infrastructure/docker/Dockerfile.backend"

echo -e "${GREEN}=== HR Chatbot Backend Deployment ===${NC}"
echo -e "ECR Repository: ${LAMBDA_ECR_REPOSITORY}"
echo -e "Image Tag: ${LAMBDA_IMAGE_TAG}"
echo -e "Lambda Function: ${LAMBDA_FUNCTION_NAME}"
echo -e "Region: ${AWS_REGION}"
echo -e "Profile: ${AWS_PROFILE}"

# Step 1: Login to ECR
echo -e "\n${YELLOW}Step 1: Logging into ECR...${NC}"
aws ecr get-login-password --region "${AWS_REGION}" --profile "${AWS_PROFILE}" | \
  docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to login to ECR${NC}"
  exit 1
fi

echo -e "${GREEN}ECR login successful!${NC}"

# Step 2: Build Docker image
echo -e "\n${YELLOW}Step 2: Building Docker image...${NC}"
echo -e "Dockerfile: ${DOCKERFILE_PATH}"
echo -e "Build context: ${PROJECT_ROOT}"

# Use docker buildx for proper platform support
docker buildx build \
  -f "${DOCKERFILE_PATH}" \
  --target backend \
  --platform linux/arm64 \
  --provenance=false \
  --load \
  -t "${ECR_IMAGE_URI}" \
  "${PROJECT_ROOT}"

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Docker build failed${NC}"
  exit 1
fi

echo -e "${GREEN}Docker image built successfully!${NC}"

# Step 3: Push to ECR
echo -e "\n${YELLOW}Step 3: Pushing image to ECR...${NC}"
docker push "${ECR_IMAGE_URI}"

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to push image to ECR${NC}"
  exit 1
fi

echo -e "${GREEN}Image pushed to ECR successfully!${NC}"

# Step 4: Update Lambda function
echo -e "\n${YELLOW}Step 4: Updating Lambda function...${NC}"
aws lambda update-function-code \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --image-uri "${ECR_IMAGE_URI}" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --no-cli-pager

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to update Lambda function${NC}"
  exit 1
fi

echo -e "${GREEN}Lambda function updated!${NC}"

# Step 5: Wait for Lambda update to complete
echo -e "\n${YELLOW}Step 5: Waiting for Lambda update to complete...${NC}"
aws lambda wait function-updated \
  --function-name "${LAMBDA_FUNCTION_NAME}" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}"

# Step 6: Display deployment summary
echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "Image URI: ${ECR_IMAGE_URI}"
echo -e "Lambda Function: ${LAMBDA_FUNCTION_NAME}"
echo -e "Region: ${AWS_REGION}"
echo -e "\n${YELLOW}Note: Lambda environment variables are managed by Terraform.${NC}"
echo -e "${YELLOW}Run 'cd infrastructure/terraform && terraform apply' to update env vars.${NC}"
