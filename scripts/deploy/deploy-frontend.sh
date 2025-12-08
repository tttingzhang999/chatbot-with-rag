#!/bin/bash

# HR Chatbot Frontend Deployment Script
# This script builds the React app and deploys it to S3 + CloudFront

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/apps/frontend"

# Load configuration from config.sh
source "${SCRIPT_DIR}/config.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== HR Chatbot Frontend Deployment ===${NC}"
echo -e "S3 Bucket: ${S3_BUCKET}"
echo -e "CloudFront Distribution: ${CLOUDFRONT_DISTRIBUTION_ID}"
echo -e "Frontend URL: ${FRONTEND_URL}"
echo -e "Region: ${AWS_REGION}"
echo -e "Profile: ${AWS_PROFILE}"

# Validate that Terraform outputs are available
if [ -z "$S3_BUCKET" ] || [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
  echo -e "${RED}Error: Required Terraform outputs not found${NC}"
  echo -e "${YELLOW}Please run 'cd infrastructure/terraform && terraform apply' first${NC}"
  exit 1
fi

# Change to frontend directory
cd "${FRONTEND_DIR}"

# Step 1: Install dependencies
echo -e "\n${YELLOW}Step 1: Installing dependencies...${NC}"
npm install

# Step 2: Build the React application
echo -e "\n${YELLOW}Step 2: Building React application...${NC}"
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
  echo -e "${RED}Error: Build failed! 'dist' directory not found.${NC}"
  exit 1
fi

echo -e "${GREEN}Build completed successfully!${NC}"

# Step 3: Sync files to S3
echo -e "\n${YELLOW}Step 3: Uploading static assets (JS, CSS, images)...${NC}"
# Upload hashed assets (from /assets folder) with long-term caching
aws s3 sync dist/assets/ "s3://${S3_BUCKET}/assets/" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --delete \
  --cache-control "public, max-age=31536000, immutable"

echo -e "\n${YELLOW}Uploading index.html with no-cache...${NC}"
# Upload index.html with no-cache to ensure users get latest version
aws s3 cp dist/index.html "s3://${S3_BUCKET}/index.html" \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --cache-control "no-cache, no-store, must-revalidate" \
  --content-type "text/html"

# Upload other root files (robots.txt, etc.) if they exist
if [ -f "dist/robots.txt" ]; then
  aws s3 cp dist/robots.txt "s3://${S3_BUCKET}/robots.txt" \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --cache-control "public, max-age=3600"
fi

echo -e "${GREEN}Files uploaded to S3 successfully!${NC}"

# Step 4: Invalidate CloudFront cache
echo -e "\n${YELLOW}Step 4: Invalidating CloudFront cache...${NC}"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
  --paths "/*" \
  --profile "${AWS_PROFILE}" \
  --query 'Invalidation.Id' \
  --output text)

echo -e "${GREEN}CloudFront invalidation created: ${INVALIDATION_ID}${NC}"
echo -e "${YELLOW}Note: Invalidation may take a few minutes to complete.${NC}"

# Step 5: Display deployment summary
echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo -e "Website URL: ${GREEN}${FRONTEND_URL}${NC}"
echo -e "S3 Bucket: ${S3_BUCKET}"
echo -e "CloudFront Distribution: ${CLOUDFRONT_DISTRIBUTION_ID}"
echo -e "Region: ${AWS_REGION}"
echo -e "\n${YELLOW}Note: If this is your first deployment, DNS propagation may take a few minutes.${NC}"
