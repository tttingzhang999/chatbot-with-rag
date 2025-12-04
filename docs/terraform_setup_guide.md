# Terraform Setup Guide for HR Chatbot

## 概述

本專案的 Terraform 配置完全依照 `architecture_improvement_plan.md` 和 `aurora_deployment_guide.md` 設計，支援從**當前架構（Public Subnet）**到**理想架構（Private Subnet）**的平滑遷移。

**建立日期**: 2025-12-04
**Region**: ap-northeast-1 (Tokyo)

---

## 架構特點

### 1. 模組化設計

所有基礎設施分為 6 個獨立模組：

| 模組 | 功能 | 對應文檔章節 |
|------|------|-------------|
| `networking` | VPC, Subnets, Security Groups, VPC Endpoints | 架構改進計畫 - 階段 2 |
| `database` | Aurora PostgreSQL Serverless v2 + pgvector | Aurora 部署指南 |
| `storage` | S3 文件儲存 + Gateway Endpoint | 階段 1: 檔案處理改進 |
| `security` | IAM Roles, Secrets Manager | 安全最佳實踐 |
| `lambda` | Backend + File Processor | 階段 1: 異步處理 |
| `api-gateway` | HTTP API | API 入口 |

### 2. 環境隔離

三個獨立環境，各有不同的配置：

| 環境 | VPC CIDR | 架構類型 | Aurora Public | 用途 |
|------|----------|----------|---------------|------|
| **dev** | 10.0.0.0/24 | Public Subnet | Yes | 本地開發測試 |
| **staging** | 10.1.0.0/24 | Private Subnet | No | 預生產測試 |
| **prod** | 10.2.0.0/24 | Private Subnet | No | 生產環境 |

### 3. 架構遷移路徑

符合 `architecture_improvement_plan.md` 的三階段遷移：

```
階段 1 (Dev): Public Subnets
  ├─ use_private_subnets = false
  ├─ aurora_publicly_accessible = true
  ├─ create_internet_gateway = true
  └─ developer_ip_cidr = "YOUR_IP/32"

階段 2 (Staging): Private Subnets
  ├─ use_private_subnets = true
  ├─ aurora_publicly_accessible = false
  ├─ create_internet_gateway = false
  └─ developer_ip_cidr = ""

階段 3 (Prod): Ideal Architecture
  ├─ use_private_subnets = true
  ├─ aurora_publicly_accessible = false
  ├─ enable_deletion_protection = true
  ├─ enable_performance_insights = true
  └─ custom_domain_name = "api.going.cloud" (可選)
```

---

## 檔案結構說明

### 根目錄檔案

| 檔案 | 說明 |
|------|------|
| `main.tf` | 編排所有模組，定義資源依賴關係 |
| `variables.tf` | 全域變數定義 |
| `outputs.tf` | 全域輸出（API endpoint, Aurora endpoint 等）|
| `providers.tf` | AWS provider 配置 |
| `versions.tf` | Terraform 版本約束 |
| `README.md` | 完整使用文檔 |
| `QUICK_START.md` | 快速開始指南 |
| `.gitignore` | Git 忽略規則 |

### 模組詳解

#### `modules/networking/`
實現 `architecture_improvement_plan.md` 網路架構：

**資源**:
- VPC (DNS support + DNS hostnames enabled)
- 2 Subnets (跨 AZ: 1a, 1c)
- Internet Gateway (條件式，基於 `use_private_subnets`)
- Security Group (PostgreSQL 5432, HTTPS 443)
- VPC Endpoints:
  - Secrets Manager (Interface) ~$7.5/月
  - Bedrock Runtime (Interface) ~$7.5/月
  - **S3 (Gateway - 免費)** ✅

**關鍵變數**:
- `use_private_subnets`: 控制 Public/Private 架構
- `create_internet_gateway`: 自動決定是否需要 IGW
- `developer_ip_cidr`: Dev 環境本地訪問

#### `modules/database/`
實現 Aurora PostgreSQL Serverless v2 部署：

**資源**:
- Aurora Cluster (PostgreSQL 17.6)
- Aurora Instance (db.serverless)
- DB Subnet Group
- 自動生成密碼 (32 字元)

**關鍵配置**:
```hcl
min_capacity = 0.5 ACU  # Dev/Staging
max_capacity = 2.0 ACU  # Dev/Staging
max_capacity = 4.0 ACU  # Production

publicly_accessible = true   # Dev only
publicly_accessible = false  # Staging/Prod

skip_final_snapshot = true   # Dev/Staging
skip_final_snapshot = false  # Production
```

**成本估算**:
- 0.5 ACU × 730h × $0.12 = ~$44/月

#### `modules/storage/`
實現階段 1 改進：檔案持久化存儲

**改進前 (Current)**:
```
文件存在 Lambda /tmp → Lambda 回收後消失 ❌
```

**改進後 (Terraform)**:
```
文件存在 S3 → 持久化 + 可重新處理 ✅
```

**資源**:
- S3 Bucket (加密、版本控制、阻止公開訪問)
- Lifecycle Policy (可選，成本優化)

#### `modules/security/`
實現最小權限原則：

**Secrets Manager**:
- `hr-chatbot/database`: Aurora 憑證
- `hr-chatbot/app-secrets`: JWT secret key

**IAM Roles**:
1. **Backend Lambda Role**:
   - VPC Access
   - Secrets Manager Read
   - Bedrock Invoke (Nova Pro, Cohere Embed)
   - **S3 Upload only** (uploads/ prefix)
   - CloudWatch Logs Write

2. **File Processor Lambda Role**:
   - VPC Access
   - Secrets Manager Read
   - Bedrock Invoke (Cohere Embed only)
   - **S3 Read only**
   - CloudWatch Logs Write

#### `modules/lambda/`
實現階段 1 核心改進：異步文件處理

**改進前 (Synchronous)**:
```
User Upload → Backend Lambda
                │
                ├─ 存 /tmp
                ├─ 解析文件
                ├─ Chunking
                ├─ Embedding
                └─ 存 Aurora

⏱️ 用戶等待 30-60 秒
```

**改進後 (Asynchronous)**:
```
User Upload → Backend Lambda → 上傳 S3 → 回應 "Processing..."
                                  ↓
                            S3 Event Trigger
                                  ↓
                        File Processor Lambda
                                  ├─ 讀取 S3
                                  ├─ 解析
                                  ├─ Chunking
                                  ├─ Embedding
                                  └─ 存 Aurora

⚡ 用戶立即得到回應（幾秒）
```

**資源**:
- Backend Lambda (container image)
- File Processor Lambda (container image)
- S3 Event Notification
- Lambda Permissions

#### `modules/api-gateway/`
HTTP API Gateway (比 REST API 便宜 3.5 倍)

**路由**:
- `GET /health`: 健康檢查
- `POST /chat`: 多輪對話
- `POST /query`: RAG 查詢
- `POST /upload`: 文件上傳
- `GET /documents`: 列出文件

**功能**:
- CORS 配置
- Throttling (100 burst, 50 req/s)
- CloudWatch 訪問日誌
- 可選自定義域名 (Route53 + ACM)

---

## 成本對比

### 當前手動部署
根據 `aurora_deployment_guide.md`:
- Aurora Serverless v2: ~$44/月
- VPC Endpoints (2): ~$15/月
- Lambda: ~$5/月
- App Runner: ~$10/月
- API Gateway: ~$1/月
- **總計: ~$75/月**

### Terraform 部署後
根據 `architecture_improvement_plan.md`:
- Aurora Serverless v2: ~$44/月
- VPC Endpoints (2 Interface + **1 Gateway**): ~$15/月
- Lambda (Backend + **File Processor**): ~$8/月
- S3: ~$1/月 (新增)
- API Gateway: ~$1/月
- **總計: ~$69/月**

**節省**: $6/月，但獲得：
- ✅ 文件持久化
- ✅ 異步處理
- ✅ 更好的用戶體驗
- ✅ 可重新處理失敗的文件

---

## 部署流程

### 前置作業

1. **創建 ECR Repositories**:
   ```bash
   aws ecr create-repository --repository-name hr-chatbot-backend --region ap-northeast-1
   aws ecr create-repository --repository-name hr-chatbot-file-processor --region ap-northeast-1
   ```

2. **構建並推送 Docker Images**:
   ```bash
   # Backend
   docker build -t hr-chatbot-backend -f Dockerfile.backend .
   docker tag hr-chatbot-backend:latest $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:dev
   docker push $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:dev

   # File Processor
   docker build -t hr-chatbot-file-processor -f Dockerfile.file-processor .
   docker tag hr-chatbot-file-processor:latest $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:dev
   docker push $ACCOUNT_ID.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:dev
   ```

3. **創建 Terraform State Backend**:
   ```bash
   # S3 Bucket
   aws s3api create-bucket \
       --bucket hr-chatbot-terraform-state-dev \
       --region ap-northeast-1 \
       --create-bucket-configuration LocationConstraint=ap-northeast-1

   # Enable versioning
   aws s3api put-bucket-versioning \
       --bucket hr-chatbot-terraform-state-dev \
       --versioning-configuration Status=Enabled

   # DynamoDB for locking
   aws dynamodb create-table \
       --table-name hr-chatbot-terraform-locks-dev \
       --attribute-definitions AttributeName=LockID,AttributeType=S \
       --key-schema AttributeName=LockID,KeyType=HASH \
       --billing-mode PAY_PER_REQUEST \
       --region ap-northeast-1
   ```

### 部署步驟

```bash
cd terraform

# 1. 複製環境配置
cp environments/dev/backend.tf .

# 2. 更新 tfvars 中的開發者 IP
# 編輯 environments/dev/terraform.tfvars:
#   developer_ip_cidr = "YOUR_IP/32"

# 3. 初始化 Terraform
terraform init

# 4. 預覽變更
terraform plan -var-file=environments/dev/terraform.tfvars

# 5. 部署
terraform apply -var-file=environments/dev/terraform.tfvars
```

### 部署後配置

1. **安裝 pgvector Extension**:
   ```bash
   terraform output aurora_cluster_endpoint
   psql -h <endpoint> -U postgres -d hr_chatbot -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

2. **執行資料庫遷移**:
   ```bash
   cd ..  # 回到專案根目錄
   uv run alembic upgrade head
   ```

3. **測試 API**:
   ```bash
   curl $(terraform output -raw api_gateway_endpoint)/health
   ```

---

## 架構遷移指南

### 從 Public 遷移到 Private Subnet

**場景**: Dev 環境測試完成，準備部署到 Staging

1. **更新 tfvars**:
   ```hcl
   # environments/staging/terraform.tfvars
   use_private_subnets = true
   aurora_publicly_accessible = false
   developer_ip_cidr = ""
   ```

2. **預覽變更**:
   ```bash
   terraform plan -var-file=environments/staging/terraform.tfvars
   ```

   會看到：
   - ⚠️ Subnet 修改 (public → private)
   - ⚠️ Internet Gateway 移除
   - ⚠️ Aurora 修改 (publicly accessible → private)
   - ✅ VPC Endpoints 保持不變

3. **部署**:
   ```bash
   terraform apply -var-file=environments/staging/terraform.tfvars
   ```

4. **驗證**:
   ```bash
   # Lambda 應該仍能連接 Aurora (通過 VPC Endpoint)
   aws logs tail /aws/lambda/hr-chatbot-backend --follow
   ```

---

## 與現有部署的差異

### 已實現的改進

根據 `architecture_improvement_plan.md`:

| 改進項目 | 優先級 | Terraform 狀態 |
|---------|--------|---------------|
| S3 持久化存儲 | 🔴 高 | ✅ 完成 |
| 獨立 File Processor Lambda | 🔴 高 | ✅ 完成 |
| S3 VPC Gateway Endpoint | 🔴 高 | ✅ 完成 |
| Private Subnet 支援 | 🟡 中 | ✅ 完成 (可配置) |
| Aurora Private Only | 🟡 中 | ✅ 完成 (可配置) |
| 自定義域名 | 🟢 低 | ✅ 完成 (可選) |

### 手動部署 vs Terraform

| 項目 | 手動部署 | Terraform |
|------|---------|-----------|
| VPC 配置 | ✅ | ✅ |
| Aurora Cluster | ✅ | ✅ |
| VPC Endpoints | ✅ (2個) | ✅ (3個，多了 S3) |
| Backend Lambda | ✅ | ✅ |
| File Processor | ❌ | ✅ **新增** |
| S3 文件存儲 | ❌ | ✅ **新增** |
| S3 Event Trigger | ❌ | ✅ **新增** |
| 異步處理 | ❌ | ✅ **新增** |
| 環境隔離 | ❌ | ✅ **新增** |
| 基礎設施即代碼 | ❌ | ✅ **新增** |

---

## 最佳實踐

### 1. 環境管理

```bash
# Dev: 快速迭代
terraform apply -var-file=environments/dev/terraform.tfvars -auto-approve

# Staging: 測試遷移
terraform plan -var-file=environments/staging/terraform.tfvars
terraform apply -var-file=environments/staging/terraform.tfvars

# Prod: 謹慎部署
terraform plan -var-file=environments/prod/terraform.tfvars -out=prod.tfplan
# 審查 plan
terraform apply prod.tfplan
```

### 2. State 管理

```bash
# 查看當前 state
terraform state list

# 查看特定資源
terraform state show module.database.aws_rds_cluster.main

# 移除資源（謹慎使用）
terraform state rm module.networking.aws_internet_gateway.main[0]
```

### 3. 密碼輪換

```bash
# Terraform 會在每次 apply 時保持密碼不變
# 若需手動輪換，可以：
terraform taint module.database.random_password.db_password
terraform apply
```

### 4. 成本監控

```bash
# 使用 AWS Cost Explorer 或設定 Budget
aws budgets create-budget \
    --account-id $ACCOUNT_ID \
    --budget '{
        "BudgetName": "hr-chatbot-dev-budget",
        "BudgetLimit": {"Amount": "100", "Unit": "USD"},
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST"
    }'
```

---

## 故障排除

### Lambda Init Timeout

**症狀**: Lambda 函數初始化超時

**檢查**:
```bash
# 確認 VPC Endpoints 已創建
terraform state show module.networking.aws_vpc_endpoint.secretsmanager
terraform state show module.networking.aws_vpc_endpoint.bedrock_runtime

# 確認 Security Group 允許 HTTPS
terraform state show module.networking.aws_vpc_security_group_ingress_rule.https_self
```

### Aurora 無法連接

**症狀**: 本地無法連接 Aurora

**檢查**:
```bash
# 1. 確認 publicly_accessible
terraform output | grep publicly_accessible

# 2. 確認開發者 IP
curl ifconfig.me
# 比對 environments/dev/terraform.tfvars 中的 developer_ip_cidr

# 3. 重新 apply
terraform apply -var-file=environments/dev/terraform.tfvars
```

### S3 Event 未觸發

**症狀**: 上傳檔案後 File Processor 未執行

**檢查**:
```bash
# 1. 確認 S3 notification 配置
aws s3api get-bucket-notification-configuration \
    --bucket hr-chatbot-documents-ap-northeast-1

# 2. 確認 Lambda permission
aws lambda get-policy --function-name hr-chatbot-file-processor

# 3. 查看 Lambda logs
aws logs tail /aws/lambda/hr-chatbot-file-processor --follow

# 4. 手動測試
aws s3 cp test.pdf s3://hr-chatbot-documents-ap-northeast-1/uploads/
```

---

## 下一步

1. **CI/CD 整合**: 將 Terraform 部署加入 GitHub Actions
2. **自定義域名**: 申請 ACM 憑證，配置 Route53
3. **監控告警**: 設定 CloudWatch Alarms
4. **備份策略**: 配置 Aurora 自動備份和快照
5. **災難恢復**: 設定跨區域複製（如需要）

---

## 參考資源

- [架構改進計畫](./architecture_improvement_plan.md)
- [Aurora 部署指南](./aurora_deployment_guide.md)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

**維護者**: Ting Zhang
**建立日期**: 2025-12-04
**最後更新**: 2025-12-04
