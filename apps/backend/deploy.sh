#!/bin/bash

# HR Chatbot Backend Deployment Script
# This script builds the backend Docker image and deploys to ECR + Lambda

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_ACCOUNT_ID="593713876380"
AWS_REGION="ap-northeast-1"
ECR_REPOSITORY="ting-assignment/hr-chatbot-backend"
IMAGE_TAG="latest"
LAMBDA_FUNCTION_NAME="hr-chatbot-backend"
AWS_PROFILE="tf-gc-playground"

# Derived values
ECR_IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
DOCKERFILE_PATH="../../infrastructure/docker/Dockerfile.lambda"

echo -e "${GREEN}=== HR Chatbot Backend Deployment ===${NC}"
echo -e "ECR Repository: ${ECR_REPOSITORY}"
echo -e "Image Tag: ${IMAGE_TAG}"
echo -e "Lambda Function: ${LAMBDA_FUNCTION_NAME}"

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
echo -e "Build context: $(pwd)"

docker build \
  -f "${DOCKERFILE_PATH}" \
  --target backend \
  --platform linux/arm64 \
  --provenance=false \
  -t "${ECR_IMAGE_URI}" \
  .

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
echo -e "${YELLOW}Run 'cd ../../infrastructure/terraform && terraform apply' to update env vars.${NC}"
