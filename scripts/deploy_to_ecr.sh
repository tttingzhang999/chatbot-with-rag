#!/bin/bash

# Deploy Docker images to AWS ECR
# Usage: ./scripts/deploy_to_ecr.sh [backend|frontend|all]

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
BACKEND_REPO_NAME="${BACKEND_REPO_NAME:-hr-chatbot-backend}"
FRONTEND_REPO_NAME="${FRONTEND_REPO_NAME:-hr-chatbot-frontend}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_aws_account() {
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_info "Fetching AWS Account ID..."
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        if [ -z "$AWS_ACCOUNT_ID" ]; then
            print_error "Failed to get AWS Account ID. Please ensure AWS credentials are configured."
            exit 1
        fi
        print_info "AWS Account ID: $AWS_ACCOUNT_ID"
    fi
}

ecr_login() {
    print_info "Logging in to Amazon ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
}

create_ecr_repo() {
    local repo_name=$1
    print_info "Checking if ECR repository '$repo_name' exists..."

    if ! aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION >/dev/null 2>&1; then
        print_warning "Repository '$repo_name' does not exist. Creating..."
        aws ecr create-repository \
            --repository-name $repo_name \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256
        print_info "Repository '$repo_name' created successfully."
    else
        print_info "Repository '$repo_name' already exists."
    fi
}

build_and_push_backend() {
    print_info "Building backend Docker image..."
    docker build -f Dockerfile.backend -t $BACKEND_REPO_NAME:$IMAGE_TAG .

    print_info "Tagging backend image..."
    docker tag $BACKEND_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO_NAME:$IMAGE_TAG

    print_info "Pushing backend image to ECR..."
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO_NAME:$IMAGE_TAG

    print_info "Backend image pushed successfully!"
    echo "Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO_NAME:$IMAGE_TAG"
}

build_and_push_frontend() {
    print_info "Building frontend Docker image..."
    docker build -f Dockerfile.frontend -t $FRONTEND_REPO_NAME:$IMAGE_TAG .

    print_info "Tagging frontend image..."
    docker tag $FRONTEND_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO_NAME:$IMAGE_TAG

    print_info "Pushing frontend image to ECR..."
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO_NAME:$IMAGE_TAG

    print_info "Frontend image pushed successfully!"
    echo "Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO_NAME:$IMAGE_TAG"
}

# Main script
main() {
    local component=${1:-all}

    print_info "Starting deployment to ECR..."
    print_info "Region: $AWS_REGION"
    print_info "Component: $component"

    # Check AWS credentials
    check_aws_account

    # Login to ECR
    ecr_login

    case $component in
        backend)
            create_ecr_repo $BACKEND_REPO_NAME
            build_and_push_backend
            ;;
        frontend)
            create_ecr_repo $FRONTEND_REPO_NAME
            build_and_push_frontend
            ;;
        all)
            create_ecr_repo $BACKEND_REPO_NAME
            create_ecr_repo $FRONTEND_REPO_NAME
            build_and_push_backend
            build_and_push_frontend
            ;;
        *)
            print_error "Invalid component. Use: backend, frontend, or all"
            exit 1
            ;;
    esac

    print_info "Deployment completed successfully!"
}

# Run main function
main "$@"
