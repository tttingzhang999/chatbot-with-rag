# AWS 部署指南

本文檔提供 HR Chatbot 系統部署到 AWS 的完整步驟。

**部署日期**: 2025-12-02
**版本**: v0.6.0
**架構**: Frontend (ECS) → API Gateway → Backend Lambda → Aurora PostgreSQL

---

## 系統架構概覽

```
┌─────────────────┐
│   Route 53      │
│ hr-chatbot      │
│ .goingcloud.ai  │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│   ALB + HTTPS   │
│  (Frontend)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐       ┌──────────────────┐
│  ECS Fargate    │       │  API Gateway     │
│  Gradio UI      │──────→│  (REST API)      │
│  Port: 7860     │       │                  │
└─────────────────┘       └────────┬─────────┘
                                   │
                                   ↓
                          ┌────────────────┐
                          │ Lambda (FastAPI)│
                          │ Backend         │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ↓              ↓              ↓
            ┌───────────┐  ┌──────────┐  ┌──────────────┐
            │  Aurora   │  │ Bedrock  │  │   Secrets    │
            │PostgreSQL │  │ Claude   │  │   Manager    │
            └───────────┘  └──────────┘  └──────────────┘
```

---

## 階段一：準備工作

### 1. 環境檢查與配置

#### 1.1 配置 AWS 憑證

```bash
# 檢查現有 AWS profiles
aws-vault list

# 使用 aws-vault 執行命令
aws-vault exec <your-profile> -- aws sts get-caller-identity

# 設置環境變數
export AWS_REGION=ap-northeast-1
export AWS_ACCOUNT_ID=$(aws-vault exec <your-profile> -- aws sts get-caller-identity --query Account --output text)
export IMAGE_TAG=v0.6.0

# 驗證
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "Region: $AWS_REGION"
```

#### 1.2 確認 .env 配置

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env，確保以下變數已設定：
# - AWS_REGION=ap-northeast-1
# - AWS_PROFILE=<your-profile>
# - DB_SECRET_NAME=hr-chatbot/database
# - APP_SECRET_NAME=hr-chatbot/app-secrets
# - ENABLE_RAG=true
```

### 2. 創建 AWS Secrets Manager Secrets

如果尚未創建，執行以下命令：

#### 2.1 資料庫憑證

```bash
aws-vault exec <your-profile> -- aws secretsmanager create-secret \
    --name hr-chatbot/database \
    --description "Database credentials for HR Chatbot" \
    --region ap-northeast-1 \
    --secret-string '{
        "username": "postgres",
        "password": "YOUR_SECURE_PASSWORD",
        "host": "YOUR_AURORA_ENDPOINT.ap-northeast-1.rds.amazonaws.com",
        "port": "5432",
        "dbname": "hr_chatbot"
    }'
```

#### 2.2 應用密鑰

```bash
# 生成 SECRET_KEY
SECRET_KEY=$(python scripts/generate_secret_key.py)

aws-vault exec <your-profile> -- aws secretsmanager create-secret \
    --name hr-chatbot/app-secrets \
    --description "Application secrets for HR Chatbot" \
    --region ap-northeast-1 \
    --secret-string "{\"SECRET_KEY\":\"$SECRET_KEY\"}"
```

### 3. 驗證資料庫連接

```bash
# 從 Secrets Manager 獲取憑證並測試連接
aws-vault exec <your-profile> -- aws secretsmanager get-secret-value \
    --secret-id hr-chatbot/database \
    --region ap-northeast-1 \
    --query SecretString --output text | jq .
```

---

## 階段二：構建並上傳 Docker 映像到 ECR

### 4. Backend Lambda 部署

#### 4.1 創建 ECR Repository

```bash
aws-vault exec <your-profile> -- aws ecr create-repository \
    --repository-name hr-chatbot-backend \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
```

#### 4.2 登入 ECR

```bash
aws-vault exec <your-profile> -- aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

#### 4.3 構建並推送 Backend 映像

```bash
# 構建映像（使用 linux/amd64 平台）
docker build --platform linux/amd64 \
    -f Dockerfile.backend \
    -t hr-chatbot-backend:$IMAGE_TAG .

# 標記映像
docker tag hr-chatbot-backend:$IMAGE_TAG \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-backend:$IMAGE_TAG

# 推送到 ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-backend:$IMAGE_TAG

# 記錄 Image URI（後續步驟需要使用）
echo "Backend Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-backend:$IMAGE_TAG"
```

**輸出示例**:
```
Backend Image URI: 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:v0.6.0
```

### 5. Frontend (Gradio) 部署

#### 5.1 創建 ECR Repository

```bash
aws-vault exec <your-profile> -- aws ecr create-repository \
    --repository-name hr-chatbot-frontend \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
```

#### 5.2 構建並推送 Frontend 映像

```bash
# 構建映像
docker build --platform linux/amd64 \
    -f Dockerfile.frontend \
    -t hr-chatbot-frontend:$IMAGE_TAG .

# 標記映像
docker tag hr-chatbot-frontend:$IMAGE_TAG \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-frontend:$IMAGE_TAG

# 推送到 ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-frontend:$IMAGE_TAG

# 記錄 Image URI
echo "Frontend Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-frontend:$IMAGE_TAG"
```

**輸出示例**:
```
Frontend Image URI: 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-frontend:v0.6.0
```

### 快捷方式（可選）

使用現有的部署腳本一次性完成：

```bash
AWS_REGION=ap-northeast-1 IMAGE_TAG=v0.6.0 ./scripts/deploy_to_ecr.sh all
```

---

## 階段三：AWS Console 網頁設定

### 6. 創建 Backend Lambda Function

#### 6.1 基本設定

1. 前往 [Lambda Console](https://ap-northeast-1.console.aws.amazon.com/lambda/home?region=ap-northeast-1#/functions)
2. 點擊 **Create function**
3. 選擇 **Container image**
4. 填寫資訊：
   - **Function name**: `hr-chatbot-backend`
   - **Container image URI**: 貼上步驟 4.3 的 Backend Image URI
   - **Architecture**: `x86_64`
5. 點擊 **Create function**

#### 6.2 配置 Lambda 設定

前往 **Configuration** 標籤：

**General configuration**:
- **Memory**: 1024 MB
- **Timeout**: 30 seconds
- **Ephemeral storage**: 512 MB（預設即可）

**Environment variables**:
```
AWS_REGION = ap-northeast-1
DB_SECRET_NAME = hr-chatbot/database
APP_SECRET_NAME = hr-chatbot/app-secrets
ENABLE_RAG = true
LLM_MODEL_ID = anthropic.claude-3-5-sonnet-20241022-v2:0
EMBEDDING_MODEL_ID = cohere.embed-multilingual-v3
```

#### 6.3 設定 IAM Role

1. 前往 **Configuration** → **Permissions**
2. 點擊 Role name 進入 IAM Console
3. 添加以下 Policies:
   - `AWSLambdaBasicExecutionRole` (已自動添加)
   - `SecretsManagerReadWrite` (讀取 Secrets Manager)
   - `AmazonBedrockFullAccess` (調用 Claude Sonnet 4)

4. 如果 Aurora 在 VPC 內，還需要：
   - `AWSLambdaVPCAccessExecutionRole`

**自定義 RDS Policy**（最小權限原則）:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-db:connect"
            ],
            "Resource": "arn:aws:rds-db:ap-northeast-1:*:dbuser:*/*"
        }
    ]
}
```

#### 6.4 設定 VPC（如果 Aurora 在 VPC 內）

1. 前往 **Configuration** → **VPC**
2. 點擊 **Edit**
3. 配置：
   - **VPC**: 選擇 Aurora 所在的 VPC
   - **Subnets**: 選擇至少 2 個私有子網（不同 AZ）
   - **Security groups**: 選擇允許訪問 Aurora 的 Security Group
     - Outbound rule: PostgreSQL (port 5432) → Aurora Security Group

4. 確保 Aurora Security Group 允許來自 Lambda Security Group 的連接：
   - Inbound rule: PostgreSQL (port 5432) ← Lambda Security Group

#### 6.5 測試 Lambda（可選）

1. 前往 **Test** 標籤
2. 創建測試事件：

```json
{
  "rawPath": "/health",
  "requestContext": {
    "http": {
      "method": "GET"
    }
  }
}
```

3. 點擊 **Test** 執行
4. 檢查 Response 和 CloudWatch Logs

### 7. 創建 API Gateway

#### 7.1 創建 HTTP API

1. 前往 [API Gateway Console](https://ap-northeast-1.console.aws.amazon.com/apigateway/main/apis?region=ap-northeast-1)
2. 點擊 **Create API**
3. 選擇 **HTTP API** → **Build**
4. 配置：
   - **API name**: `hr-chatbot-api`
   - **Integrations**:
     - 點擊 **Add integration**
     - 選擇 **Lambda**
     - 選擇 Lambda function: `hr-chatbot-backend`
     - Version: `2.0`
   - 點擊 **Next**

#### 7.2 配置 Routes

1. 保留默認路由：`ANY /{proxy+}`
2. 點擊 **Next**

#### 7.3 配置 Stages

1. Stage name: `$default` (自動部署)
2. 啟用 **Auto-deploy**
3. 點擊 **Next** → **Create**

#### 7.4 配置 CORS

1. 前往 API 詳情頁面
2. 左側選單選擇 **CORS**
3. 配置：
   - **Access-Control-Allow-Origin**: `*` (開發環境) 或指定前端域名
   - **Access-Control-Allow-Methods**: `GET, POST, PUT, DELETE, OPTIONS`
   - **Access-Control-Allow-Headers**: `content-type, authorization`
   - **Access-Control-Max-Age**: `300`
4. 點擊 **Save**

#### 7.5 記錄 API Gateway Invoke URL

在 API 詳情頁面，複製 **Invoke URL**:

```
https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com
```

**測試 API**:
```bash
curl https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/health
```

預期輸出:
```json
{"status": "healthy"}
```

### 8. 部署 Frontend (Gradio on ECS Fargate)

#### 8.1 創建 ECS Cluster

1. 前往 [ECS Console](https://ap-northeast-1.console.aws.amazon.com/ecs/v2/clusters?region=ap-northeast-1)
2. 點擊 **Create cluster**
3. 配置：
   - **Cluster name**: `hr-chatbot-cluster`
   - **Infrastructure**: AWS Fargate (serverless)
4. 點擊 **Create**

#### 8.2 創建 Task Definition

1. 左側選單選擇 **Task definitions**
2. 點擊 **Create new task definition**
3. 配置：

**Task definition family**:
- **Task definition family name**: `hr-chatbot-frontend`

**Infrastructure requirements**:
- **Launch type**: AWS Fargate
- **Operating system/Architecture**: Linux/X86_64
- **Task size**:
  - **CPU**: 0.5 vCPU
  - **Memory**: 1 GB

**Container - 1**:
- **Container name**: `frontend`
- **Image URI**: 貼上步驟 5.2 的 Frontend Image URI
- **Port mappings**:
  - **Container port**: `7860`
  - **Protocol**: TCP
  - **App protocol**: HTTP
- **Environment variables**:
  ```
  BACKEND_API_URL = https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com
  GRADIO_HOST = 0.0.0.0
  GRADIO_PORT = 7860
  ```

**Log collection** (CloudWatch Logs):
- 啟用 **Use log collection**
- 使用自動創建的 Log group

4. 點擊 **Create**

#### 8.3 創建 Application Load Balancer

1. 前往 [EC2 Console → Load Balancers](https://ap-northeast-1.console.aws.amazon.com/ec2/home?region=ap-northeast-1#LoadBalancers:)
2. 點擊 **Create load balancer**
3. 選擇 **Application Load Balancer**
4. 配置：

**Basic configuration**:
- **Load balancer name**: `hr-chatbot-frontend-alb`
- **Scheme**: Internet-facing
- **IP address type**: IPv4

**Network mapping**:
- **VPC**: 選擇你的 VPC
- **Mappings**: 選擇至少 2 個可用區域的公有子網

**Security groups**:
- 創建新的 Security Group:
  - **Name**: `hr-chatbot-alb-sg`
  - **Inbound rules**:
    - HTTP (80) from 0.0.0.0/0
    - HTTPS (443) from 0.0.0.0/0

**Listeners and routing**:
- **Listener 1**:
  - **Protocol**: HTTP
  - **Port**: 80
  - **Default action**: 創建新 Target Group
    - **Target group name**: `hr-chatbot-frontend-tg`
    - **Target type**: IP
    - **Protocol**: HTTP
    - **Port**: 7860
    - **Health check path**: `/`
    - **Health check interval**: 30 seconds

5. 點擊 **Create load balancer**

#### 8.4 創建 ECS Service

1. 回到 ECS Console → Clusters → `hr-chatbot-cluster`
2. 在 **Services** 標籤，點擊 **Create**
3. 配置：

**Environment**:
- **Compute options**: Launch type
- **Launch type**: FARGATE

**Deployment configuration**:
- **Application type**: Service
- **Task definition**: `hr-chatbot-frontend` (latest)
- **Service name**: `frontend-service`
- **Desired tasks**: 1

**Networking**:
- **VPC**: 選擇 ALB 所在的 VPC
- **Subnets**: 選擇私有子網（或公有子網，如果沒有 NAT Gateway）
- **Security group**: 創建新的
  - **Name**: `hr-chatbot-ecs-sg`
  - **Inbound rules**:
    - Custom TCP (7860) from ALB Security Group

**Load balancing**:
- **Load balancer type**: Application Load Balancer
- **Load balancer**: `hr-chatbot-frontend-alb`
- **Listener**: 80:HTTP
- **Target group**: `hr-chatbot-frontend-tg`

4. 點擊 **Create**

#### 8.5 等待部署完成

1. 在 Service 詳情頁面，查看 **Tasks** 標籤
2. 等待 Task 狀態變為 **RUNNING**
3. 檢查 Target Group 健康狀態：
   - EC2 Console → Target Groups → `hr-chatbot-frontend-tg`
   - 等待 Targets 狀態變為 **healthy**

#### 8.6 測試 ALB

複製 ALB DNS name (例如: `hr-chatbot-frontend-alb-xxxxx.ap-northeast-1.elb.amazonaws.com`)

```bash
curl http://hr-chatbot-frontend-alb-xxxxx.ap-northeast-1.elb.amazonaws.com
```

或在瀏覽器打開: `http://hr-chatbot-frontend-alb-xxxxx.ap-northeast-1.elb.amazonaws.com`

### 9. 配置 HTTPS (使用 Certificate Manager)

#### 9.1 申請 SSL 證書

1. 前往 [Certificate Manager Console](https://ap-northeast-1.console.aws.amazon.com/acm/home?region=ap-northeast-1)
2. 點擊 **Request a certificate**
3. 選擇 **Request a public certificate**
4. 配置：
   - **Fully qualified domain name**: `hr-chatbot.going.cloud`
   - **Validation method**: DNS validation
5. 點擊 **Request**

#### 9.2 驗證域名

1. 在證書詳情頁面，展開域名記錄
2. 點擊 **Create records in Route 53**
3. 確認並創建 CNAME 記錄
4. 等待證書狀態變為 **Issued**（通常需要 5-10 分鐘）

#### 9.3 添加 HTTPS Listener 到 ALB

1. 前往 EC2 Console → Load Balancers → `hr-chatbot-frontend-alb`
2. 選擇 **Listeners** 標籤
3. 點擊 **Add listener**
4. 配置：
   - **Protocol**: HTTPS
   - **Port**: 443
   - **Default actions**: Forward to `hr-chatbot-frontend-tg`
   - **Security policy**: ELBSecurityPolicy-TLS13-1-2-2021-06
   - **Default SSL/TLS certificate**: 選擇剛創建的證書
5. 點擊 **Add**

#### 9.4 配置 HTTP 到 HTTPS 重定向

1. 選擇 HTTP:80 Listener
2. 點擊 **Edit**
3. 修改 Default action:
   - **Action type**: Redirect
   - **Protocol**: HTTPS
   - **Port**: 443
   - **Status code**: 301 (Permanent redirect)
4. 點擊 **Save changes**

### 10. 配置 Route 53 域名

#### 10.1 創建 A Record

1. 前往 [Route 53 Console](https://console.aws.amazon.com/route53/v2/hostedzones)
2. 選擇 Hosted zone: `going.cloud`
3. 點擊 **Create record**
4. 配置：
   - **Record name**: `hr-chatbot`
   - **Record type**: A
   - **Alias**: 啟用
   - **Route traffic to**:
     - Alias to Application and Classic Load Balancer
     - Region: Asia Pacific (Tokyo) ap-northeast-1
     - Load balancer: 選擇 `hr-chatbot-frontend-alb`
   - **Routing policy**: Simple routing
5. 點擊 **Create records**

#### 10.2 驗證 DNS 解析

```bash
# 檢查 DNS 解析
nslookup hr-chatbot.going.cloud

# 測試 HTTPS 訪問
curl -I https://hr-chatbot.going.cloud
```

**⚠️ 重要提醒**: 不要修改或刪除現有的 Route 53 記錄！

---

## 階段四：測試與驗證

### 11. 端到端測試

#### 11.1 測試 Backend Lambda

**通過 API Gateway**:
```bash
# 健康檢查
curl https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/health

# 測試聊天 API
curl -X POST https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": "你好，請問勞保的投保薪資上限是多少？"
  }'
```

預期回應:
```json
{
  "response": "根據目前的規定，勞保的投保薪資上限是...",
  "session_id": "test-123"
}
```

#### 11.2 測試 Frontend

**瀏覽器訪問**:
```
https://hr-chatbot.going.cloud
```

**功能測試**:
1. ✅ 頁面正常載入
2. ✅ 聊天輸入框可用
3. ✅ 發送訊息後收到回應
4. ✅ 對話歷史正確顯示
5. ✅ 文件上傳功能正常（如果啟用）

#### 11.3 測試 RAG 功能

如果已上傳文檔到資料庫：

```bash
# 測試帶 RAG 的查詢
curl -X POST https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/query \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-rag-456",
    "message": "公司的特休規定是什麼？",
    "use_rag": true
  }'
```

### 12. 監控與日誌

#### 12.1 CloudWatch Logs

**Backend Lambda Logs**:
```bash
# 查看最近的日誌
aws-vault exec <your-profile> -- aws logs tail /aws/lambda/hr-chatbot-backend --follow
```

**Frontend ECS Logs**:
```bash
# 查看 Fargate 容器日誌
aws-vault exec <your-profile> -- aws logs tail /ecs/hr-chatbot-frontend --follow
```

#### 12.2 CloudWatch Metrics

前往 [CloudWatch Console](https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1) 查看：

**Lambda Metrics**:
- Invocations (請求數)
- Duration (執行時間)
- Errors (錯誤數)
- Throttles (限流數)

**API Gateway Metrics**:
- Count (請求總數)
- 4XXError (客戶端錯誤)
- 5XXError (服務端錯誤)
- Latency (延遲)

**ECS Metrics**:
- CPUUtilization (CPU 使用率)
- MemoryUtilization (記憶體使用率)

**ALB Metrics**:
- TargetResponseTime (目標回應時間)
- HealthyHostCount (健康主機數)
- RequestCount (請求數)

---

## 階段五：優化與維護

### 13. 成本優化建議

#### 13.1 Lambda 優化
- **預留併發**（Provisioned Concurrency）: 如果流量穩定，可避免冷啟動
- **ARM64 架構**: 比 x86_64 便宜 20%，但需重新構建映像
- **記憶體調整**: 根據實際使用情況調整（CloudWatch Insights 分析）

#### 13.2 Aurora 優化
- **Aurora Serverless v2**: 按需自動擴展，低流量時成本更低
- **Data API**: 考慮使用 Data API 替代持久連接
- **定期備份**: 配置自動快照保留策略

#### 13.3 ECS/Fargate 優化
- **Fargate Spot**: 非關鍵環境使用 Spot instances（最多省 70%）
- **Auto Scaling**: 根據 CPU/記憶體使用率自動擴展
- **Task 大小**: 根據實際需求調整 vCPU 和記憶體

#### 13.4 估算月度成本

假設流量（僅供參考）:
- Lambda: 100,000 次請求/月，平均執行時間 2 秒
- Fargate: 1 個 Task (0.5 vCPU, 1 GB) 持續運行
- Aurora Serverless v2: 最小 0.5 ACU
- ALB: 100 GB 數據傳輸/月

**估算**:
- Lambda: ~$5/月
- Fargate: ~$25/月
- Aurora: ~$50/月
- ALB: ~$20/月
- **總計**: ~$100/月

使用 [AWS Pricing Calculator](https://calculator.aws/) 獲取精確估算。

### 14. 安全加固

#### 14.1 網路安全

**啟用 WAF (Web Application Firewall)**:
1. 前往 WAF Console
2. 創建 Web ACL
3. 關聯到 ALB
4. 添加規則：
   - AWS Managed Rules (Core rule set)
   - Rate limiting (例如: 2000 requests/5min per IP)

**Security Group 最小權限**:
```
ALB Security Group:
  Inbound: 443 from 0.0.0.0/0
  Outbound: 7860 to ECS Security Group

ECS Security Group:
  Inbound: 7860 from ALB Security Group
  Outbound: 443 to API Gateway

Lambda Security Group (如在 VPC):
  Outbound: 5432 to Aurora Security Group
  Outbound: 443 to 0.0.0.0/0 (Bedrock API)

Aurora Security Group:
  Inbound: 5432 from Lambda Security Group
```

#### 14.2 IAM 最小權限

**Lambda Execution Role** 精簡版:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-northeast-1:*:log-group:/aws/lambda/hr-chatbot-backend:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-1:*:secret:hr-chatbot/database-*",
        "arn:aws:secretsmanager:ap-northeast-1:*:secret:hr-chatbot/app-secrets-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:ap-northeast-1::foundation-model/cohere.embed-*"
      ]
    }
  ]
}
```

#### 14.3 啟用日誌審計

**CloudTrail**:
- 記錄所有 API 調用
- 啟用管理事件和數據事件
- 保留至少 90 天

**VPC Flow Logs**:
- 記錄網路流量
- 發送到 CloudWatch Logs 或 S3

**Config**:
- 追蹤資源配置變更
- 設定合規性規則

### 15. 災難恢復計劃

#### 15.1 備份策略

**Aurora 自動備份**:
- 保留期: 7 天（建議 30 天）
- 跨區域複製: 啟用（如需要）

**ECR 映像**:
- 保留多個版本標籤（v0.6.0, v0.6.1 等）
- 定期清理舊映像

**配置備份**:
- 定期導出 CloudFormation 模板
- 將 Terraform/IaC 配置存入 Git

#### 15.2 恢復流程

**Lambda 函數回滾**:
```bash
# 更新到特定映像版本
aws lambda update-function-code \
  --function-name hr-chatbot-backend \
  --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hr-chatbot-backend:v0.5.0
```

**ECS Service 回滾**:
```bash
# 更新 Task Definition 到舊版本
aws ecs update-service \
  --cluster hr-chatbot-cluster \
  --service frontend-service \
  --task-definition hr-chatbot-frontend:3  # 指定舊的 revision
```

**資料庫恢復**:
```bash
# 從快照恢復
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier hr-chatbot-restored \
  --snapshot-identifier hr-chatbot-snapshot-20251202
```

### 16. CI/CD 自動化（未來改進）

建議使用 GitHub Actions 或 AWS CodePipeline：

**GitHub Actions 範例** (.github/workflows/deploy.yml):
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-role
          aws-region: ap-northeast-1

      - name: Login to ECR
        run: |
          aws ecr get-login-password --region ap-northeast-1 | \
          docker login --username AWS --password-stdin \
          ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-1.amazonaws.com

      - name: Build and push Backend
        run: |
          docker build --platform linux/amd64 -f Dockerfile.backend \
            -t ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:${{ github.sha }} .
          docker push ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:${{ github.sha }}

      - name: Update Lambda function
        run: |
          aws lambda update-function-code \
            --function-name hr-chatbot-backend \
            --image-uri ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:${{ github.sha }}
```

---

## 常見問題排查

### Q1: Lambda 超時錯誤

**症狀**: API 請求返回 504 Gateway Timeout

**可能原因**:
- Lambda 執行時間超過 30 秒
- 資料庫連接緩慢
- Bedrock API 調用時間過長

**解決方案**:
1. 檢查 CloudWatch Logs 確認實際執行時間
2. 優化資料庫查詢（添加索引）
3. 使用 Aurora Proxy 減少連接時間
4. 考慮異步處理長時間任務

### Q2: CORS 錯誤

**症狀**: 瀏覽器控制台顯示 CORS policy blocked

**解決方案**:
1. 確認 API Gateway CORS 配置正確
2. 檢查 Lambda response headers 包含 CORS headers
3. 確保 preflight OPTIONS 請求正常返回

### Q3: 資料庫連接失敗

**症狀**: Lambda logs 顯示 "could not connect to server"

**可能原因**:
- Lambda 不在 VPC 內
- Security Group 配置錯誤
- Secrets Manager 憑證錯誤

**解決方案**:
1. 確認 Lambda 配置在正確的 VPC 和子網
2. 檢查 Security Group 規則
3. 測試 Secrets Manager 憑證:
   ```bash
   aws secretsmanager get-secret-value --secret-id hr-chatbot/database
   ```

### Q4: ECS Task 無法啟動

**症狀**: ECS Task 狀態為 STOPPED，錯誤訊息 "CannotPullContainerError"

**可能原因**:
- ECR 映像不存在或權限不足
- Task Execution Role 缺少 ECR 權限

**解決方案**:
1. 確認映像已成功推送到 ECR
2. 檢查 Task Execution Role 包含 `AmazonECSTaskExecutionRolePolicy`
3. 查看 CloudWatch Logs 詳細錯誤訊息

### Q5: 健康檢查失敗

**症狀**: ALB Target Group 顯示 unhealthy

**可能原因**:
- 應用未在指定端口監聽
- 健康檢查路徑錯誤
- Security Group 阻擋流量

**解決方案**:
1. 確認容器正在監聽正確端口（7860）
2. 檢查健康檢查路徑（Gradio 使用 `/`）
3. 確認 ECS Security Group 允許來自 ALB 的流量

---

## 快速參考檢查清單

### 部署前檢查
- [ ] AWS 憑證已配置（aws-vault）
- [ ] .env 文件已正確設定
- [ ] Secrets Manager secrets 已創建
- [ ] Aurora PostgreSQL 已啟動並可訪問
- [ ] Docker 已安裝並運行

### ECR 映像上傳
- [ ] Backend 映像已推送到 ECR
- [ ] Frontend 映像已推送到 ECR
- [ ] 已記錄 Image URIs

### AWS 資源創建
- [ ] Backend Lambda 已創建並配置
- [ ] Lambda IAM Role 權限正確
- [ ] Lambda VPC 配置正確（如需要）
- [ ] API Gateway 已創建並測試
- [ ] ECS Cluster 已創建
- [ ] Frontend Task Definition 已創建
- [ ] ALB 已創建並配置
- [ ] ECS Service 已啟動並健康

### 域名與 HTTPS
- [ ] SSL 證書已申請並驗證
- [ ] ALB HTTPS Listener 已配置
- [ ] HTTP 到 HTTPS 重定向已啟用
- [ ] Route 53 A Record 已創建
- [ ] DNS 解析正確

### 測試驗證
- [ ] Backend API 健康檢查通過
- [ ] Frontend 頁面可訪問
- [ ] 聊天功能正常
- [ ] RAG 檢索正常（如啟用）
- [ ] CloudWatch Logs 無錯誤

---

## 支援與資源

**內部文檔**:
- [本地開發指南](./local_development.md)
- [架構文檔](../architecture.md)
- [CLAUDE.md](../CLAUDE.md)

**AWS 文檔**:
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [API Gateway HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)
- [ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Aurora PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.AuroraPostgreSQL.html)

**專案資源**:
- Google Drive: https://drive.google.com/drive/u/1/folders/1KHnvLLubLUTg5nwfR3dZKgfWanQXw7UQ

**聯絡人**:
- Project Lead: Ting Zhang
- Mentor: Micheal

---

**最後更新**: 2025-12-02
**版本**: 1.0
**維護者**: Ting Zhang
