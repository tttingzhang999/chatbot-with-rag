#!/bin/bash

# AWS IAM 自动配置脚本
# 用途: 自动创建 HR Chatbot 所需的所有 IAM 角色和策略
# 作者: Ting Zhang
# 日期: 2025-12-01

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 AWS CLI 是否已安装
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI 未安装，请先安装: https://aws.amazon.com/cli/"
        exit 1
    fi
    log_success "AWS CLI 已安装"
}

# 检查 AWS 凭证是否已配置
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS 凭证未配置，请运行: aws configure"
        exit 1
    fi

    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    CALLER_ARN=$(aws sts get-caller-identity --query Arn --output text)

    log_success "AWS 凭证已配置"
    log_info "账户 ID: $ACCOUNT_ID"
    log_info "当前身份: $CALLER_ARN"
}

# 获取用户输入
get_user_inputs() {
    log_info "请输入配置信息..."

    # GitHub 用户名
    read -p "GitHub 用户名或组织名 (例如: tingzhang): " GITHUB_USERNAME
    if [ -z "$GITHUB_USERNAME" ]; then
        log_error "GitHub 用户名不能为空"
        exit 1
    fi

    # GitHub 仓库名
    read -p "GitHub 仓库名 [默认: hr-chatbot]: " GITHUB_REPO
    GITHUB_REPO=${GITHUB_REPO:-hr-chatbot}

    # AWS 区域
    read -p "AWS 区域 [默认: us-east-1]: " AWS_REGION
    AWS_REGION=${AWS_REGION:-us-east-1}
    export AWS_DEFAULT_REGION=$AWS_REGION

    log_info "配置信息:"
    log_info "  GitHub 仓库: ${GITHUB_USERNAME}/${GITHUB_REPO}"
    log_info "  AWS 区域: $AWS_REGION"
    log_info "  AWS 账户: $ACCOUNT_ID"

    read -p "确认以上信息正确? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_warning "已取消"
        exit 0
    fi
}

# 创建 GitHub OIDC Provider
create_github_oidc_provider() {
    log_info "检查 GitHub OIDC Provider..."

    PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

    if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVIDER_ARN" &> /dev/null; then
        log_warning "GitHub OIDC Provider 已存在，跳过创建"
    else
        log_info "创建 GitHub OIDC Provider..."

        # 获取 thumbprint (GitHub Actions 的)
        THUMBPRINT="6938fd4d98bab03faadb97b34396831e3780aea1"

        aws iam create-open-id-connect-provider \
            --url https://token.actions.githubusercontent.com \
            --client-id-list sts.amazonaws.com \
            --thumbprint-list "$THUMBPRINT" \
            --tags Key=Project,Value=hr-chatbot Key=ManagedBy,Value=script

        log_success "GitHub OIDC Provider 创建成功"
    fi
}

# 创建 Lambda 执行角色
create_lambda_execution_role() {
    log_info "创建 Lambda 执行角色..."

    ROLE_NAME="hr-chatbot-lambda-execution-role"

    # 检查角色是否已存在
    if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
        log_warning "Lambda 执行角色已存在，跳过创建"
        return 0
    fi

    # 创建信任策略
    cat > /tmp/lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # 创建角色
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --description "Lambda 执行角色 - HR Chatbot 后端函数运行时使用" \
        --tags Key=Project,Value=hr-chatbot Key=Environment,Value=production Key=ManagedBy,Value=script

    log_success "Lambda 执行角色创建成功"

    # 附加 AWS 托管策略
    log_info "附加 AWS 托管策略..."

    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"

    log_success "AWS 托管策略附加成功"

    # 创建 Bedrock 访问策略
    log_info "创建 Bedrock 访问内联策略..."

    cat > /tmp/bedrock-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeClaudeModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
      ]
    },
    {
      "Sid": "InvokeCohereEmbedding",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/cohere.embed-v4:0"
      ]
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "BedrockAccess" \
        --policy-document file:///tmp/bedrock-policy.json

    # 创建 Secrets Manager 访问策略
    log_info "创建 Secrets Manager 访问内联策略..."

    cat > /tmp/secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GetDatabaseCredentials",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:${AWS_REGION}:${ACCOUNT_ID}:secret:hr-chatbot/*"
      ]
    },
    {
      "Sid": "DecryptSecrets",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "secretsmanager.${AWS_REGION}.amazonaws.com"
          ]
        }
      }
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "SecretsManagerAccess" \
        --policy-document file:///tmp/secrets-policy.json

    # 创建 S3 访问策略
    log_info "创建 S3 文档访问内联策略..."

    cat > /tmp/s3-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadDocuments",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::hr-chatbot-documents-*",
        "arn:aws:s3:::hr-chatbot-documents-*/*"
      ]
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "S3DocumentAccess" \
        --policy-document file:///tmp/s3-policy.json

    log_success "Lambda 执行角色所有策略配置完成"

    # 清理临时文件
    rm -f /tmp/lambda-trust-policy.json /tmp/bedrock-policy.json /tmp/secrets-policy.json /tmp/s3-policy.json
}

# 创建 GitHub Actions 部署角色
create_github_actions_role() {
    log_info "创建 GitHub Actions 部署角色..."

    ROLE_NAME="hr-chatbot-github-actions-role"

    # 检查角色是否已存在
    if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
        log_warning "GitHub Actions 角色已存在，跳过创建"
        return 0
    fi

    # 创建信任策略
    cat > /tmp/github-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_USERNAME}/${GITHUB_REPO}:*"
        }
      }
    }
  ]
}
EOF

    # 创建角色
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/github-trust-policy.json \
        --description "GitHub Actions 部署角色 - 用于 CI/CD 流程" \
        --tags Key=Project,Value=hr-chatbot Key=Environment,Value=production Key=ManagedBy,Value=script

    log_success "GitHub Actions 角色创建成功"

    # 创建 ECR 管理策略
    log_info "创建 ECR 管理内联策略..."

    cat > /tmp/ecr-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRAuthentication",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRRepositoryManagement",
      "Effect": "Allow",
      "Action": [
        "ecr:CreateRepository",
        "ecr:DescribeRepositories",
        "ecr:ListImages",
        "ecr:DescribeImages",
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:CompleteLayerUpload",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": [
        "arn:aws:ecr:${AWS_REGION}:${ACCOUNT_ID}:repository/hr-chatbot-*"
      ]
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "ECRManagement" \
        --policy-document file:///tmp/ecr-policy.json

    # 创建 Lambda 管理策略
    log_info "创建 Lambda 管理内联策略..."

    cat > /tmp/lambda-mgmt-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaFunctionManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListFunctions",
        "lambda:PublishVersion",
        "lambda:CreateFunctionUrlConfig",
        "lambda:UpdateFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig",
        "lambda:AddPermission",
        "lambda:GetPolicy"
      ],
      "Resource": [
        "arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:hr-chatbot-*"
      ]
    },
    {
      "Sid": "LambdaVPCConfiguration",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs"
      ],
      "Resource": "*"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "LambdaManagement" \
        --policy-document file:///tmp/lambda-mgmt-policy.json

    # 创建 IAM PassRole 策略
    log_info "创建 IAM PassRole 内联策略..."

    cat > /tmp/passrole-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PassLambdaExecutionRole",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole",
        "iam:GetRole"
      ],
      "Resource": [
        "arn:aws:iam::${ACCOUNT_ID}:role/hr-chatbot-lambda-execution-role"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "IAMPassRole" \
        --policy-document file:///tmp/passrole-policy.json

    # 创建 S3 管理策略
    log_info "创建 S3 管理内联策略..."

    cat > /tmp/s3-mgmt-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3BucketManagement",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:PutBucketNotification",
        "s3:GetBucketNotification",
        "s3:PutBucketPolicy",
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::hr-chatbot-documents-*",
        "arn:aws:s3:::hr-chatbot-documents-*/*"
      ]
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "S3Management" \
        --policy-document file:///tmp/s3-mgmt-policy.json

    # 创建 CloudWatch Logs 管理策略
    log_info "创建 CloudWatch Logs 管理内联策略..."

    cat > /tmp/logs-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageLambdaLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups"
      ],
      "Resource": [
        "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/lambda/hr-chatbot-*"
      ]
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "CloudWatchLogsManagement" \
        --policy-document file:///tmp/logs-policy.json

    log_success "GitHub Actions 角色所有策略配置完成"

    # 清理临时文件
    rm -f /tmp/github-trust-policy.json /tmp/ecr-policy.json /tmp/lambda-mgmt-policy.json /tmp/passrole-policy.json /tmp/s3-mgmt-policy.json /tmp/logs-policy.json
}

# 输出配置摘要
print_summary() {
    echo ""
    log_success "============================================"
    log_success "IAM 配置完成！"
    log_success "============================================"
    echo ""

    log_info "创建的资源:"
    echo "  ✅ GitHub OIDC Provider"
    echo "  ✅ Lambda 执行角色: hr-chatbot-lambda-execution-role"
    echo "  ✅ GitHub Actions 角色: hr-chatbot-github-actions-role"
    echo ""

    LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/hr-chatbot-lambda-execution-role"
    GITHUB_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/hr-chatbot-github-actions-role"

    log_info "重要 ARN (请保存):"
    echo "  Lambda 执行角色 ARN:"
    echo "    ${LAMBDA_ROLE_ARN}"
    echo ""
    echo "  GitHub Actions 角色 ARN:"
    echo "    ${GITHUB_ROLE_ARN}"
    echo ""

    log_warning "下一步操作:"
    echo "  1. 在 GitHub 仓库中设置以下 Secrets:"
    echo "     AWS_ROLE_TO_ASSUME=${GITHUB_ROLE_ARN}"
    echo "     AWS_REGION=${AWS_REGION}"
    echo ""
    echo "  2. 运行 ./scripts/setup_secrets.sh 创建 Secrets Manager secrets"
    echo "  3. 运行 ./scripts/setup_s3.sh 创建 S3 buckets"
    echo "  4. 配置 Lambda VPC 设置（如果数据库在 VPC 中）"
    echo "  5. 部署 Lambda 函数"
    echo ""

    log_info "验证命令:"
    echo "  # 验证 Lambda 执行角色"
    echo "  aws iam get-role --role-name hr-chatbot-lambda-execution-role"
    echo ""
    echo "  # 验证 GitHub Actions 角色"
    echo "  aws iam get-role --role-name hr-chatbot-github-actions-role"
    echo ""
}

# 主函数
main() {
    log_info "开始 AWS IAM 配置..."
    echo ""

    check_aws_cli
    check_aws_credentials
    echo ""

    get_user_inputs
    echo ""

    create_github_oidc_provider
    echo ""

    create_lambda_execution_role
    echo ""

    create_github_actions_role
    echo ""

    print_summary
}

# 运行主函数
main "$@"
