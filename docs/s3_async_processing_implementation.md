# S3 異步文件處理實施指南

**實施日期**: 2025-12-03
**狀態**: 部分完成 (代碼已準備,待部署)

---

## 已完成的改進

### ✅ 階段 1.1: 創建 S3 Bucket

```bash
# S3 Bucket 詳情
Bucket Name: hr-chatbot-documents-ap-northeast-1
Region: ap-northeast-1
Features:
  - ✅ Versioning Enabled
  - ✅ Encryption Enabled (AES256)
  - ✅ Public Access Blocked
```

### ✅ 階段 1.2: 創建 S3 Gateway VPC Endpoint

```bash
# VPC Endpoint 詳情
Endpoint ID: vpce-0cf009c1828a3e53c
Type: Gateway (免費!)
Service: com.amazonaws.ap-northeast-1.s3
VPC: vpc-096e9a11b215affa3
Route Table: rtb-0a2c110b3e52d0983
```

### ✅ 階段 1.3: 更新 Lambda IAM Role

已在 IAM Console 為 `hr-chatbot-lambda-role` 添加 inline policy `hr-chatbot-s3-access`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::hr-chatbot-documents-ap-northeast-1",
                "arn:aws:s3:::hr-chatbot-documents-ap-northeast-1/*"
            ]
        }
    ]
}
```

### ✅ 階段 1.4: 創建 File Processor Lambda 代碼

**新文件**:
- `src/lambda_handlers/__init__.py`
- `src/lambda_handlers/file_processor.py`
- `Dockerfile.file-processor`

**功能**:
- 接收 S3 PutObject 事件
- 下載文件到 `/tmp`
- 調用現有的 `DocumentProcessor` 進行處理
- 更新數據庫狀態

### ✅ 階段 1.5: 更新 Backend Lambda 上傳邏輯

**修改文件**: `src/api/routes/upload.py`

**新增功能**:
- 環境變數控制: `USE_S3=true` 時上傳到 S3
- S3 模式: 上傳到 `s3://hr-chatbot-documents-ap-northeast-1/uploads/`
- 本地模式: 保持原有邏輯用於開發

**環境變數**:
```bash
USE_S3=true                                           # 啟用 S3 上傳
S3_BUCKET=hr-chatbot-documents-ap-northeast-1         # S3 Bucket 名稱
```

---

## 待完成的步驟

### ⏳ 階段 1.6: 構建並部署 File Processor Lambda

#### 1.6.1 創建 ECR Repository (如果不存在)

```bash
aws-vault exec gc-playground-ting-chatbot -- aws ecr create-repository \
    --repository-name hr-chatbot-file-processor \
    --region ap-northeast-1 \
    --image-scanning-configuration scanOnPush=true
```

#### 1.6.2 構建 Docker 鏡像

```bash
# 構建鏡像 (指定 AMD64 平台,適用於 Apple Silicon)
docker build --platform linux/amd64 \
    -f Dockerfile.file-processor \
    -t hr-chatbot-file-processor:latest .

# 測試本地運行 (可選)
docker run --rm --platform linux/amd64 \
    -e AWS_REGION=ap-northeast-1 \
    -e DB_SECRET_NAME=hr-chatbot/database \
    -e APP_SECRET_NAME=hr-chatbot/app-secrets \
    hr-chatbot-file-processor:latest \
    python -m src.lambda_handlers.file_processor
```

**重要**:
- `--platform linux/amd64` 是必須的,因為 AWS Lambda 只支援 x86_64 架構
- Apple Silicon (M1/M2/M3) 是 ARM64 架構,需要交叉編譯
- Docker Desktop 會自動處理交叉編譯 (使用 QEMU)

#### 1.6.3 推送到 ECR

```bash
# 登錄 ECR
aws-vault exec gc-playground-ting-chatbot -- \
    aws ecr get-login-password --region ap-northeast-1 | \
    docker login --username AWS --password-stdin \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com

# Tag 鏡像
docker tag hr-chatbot-file-processor:latest \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:latest

# 推送
docker push 593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:latest
```

#### 1.6.4 創建 Lambda 函數

```bash
aws-vault exec gc-playground-ting-chatbot -- aws lambda create-function \
    --function-name hr-chatbot-file-processor \
    --package-type Image \
    --code ImageUri=593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:latest \
    --role arn:aws:iam::593713876380:role/hr-chatbot-lambda-role \
    --timeout 300 \
    --memory-size 2048 \
    --environment "Variables={
        DB_SECRET_NAME=hr-chatbot/database,
        APP_SECRET_NAME=hr-chatbot/app-secrets,
        LLM_MODEL_ID=amazon.nova-pro-v1:0,
        EMBEDDING_MODEL_ID=cohere.embed-v4:0
    }" \
    --vpc-config SubnetIds=subnet-0815a8642250d1459,subnet-0b7dc9e7411b5bec4,SecurityGroupIds=sg-0dfc84b0acf5f5565 \
    --region ap-northeast-1
```

### ⏳ 階段 1.7: 設定 S3 Event 觸發 Lambda

#### 1.7.1 添加 Lambda 權限給 S3

```bash
aws-vault exec gc-playground-ting-chatbot -- aws lambda add-permission \
    --function-name hr-chatbot-file-processor \
    --statement-id s3-trigger-permission \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::hr-chatbot-documents-ap-northeast-1 \
    --region ap-northeast-1
```

#### 1.7.2 設定 S3 Event Notification

```bash
aws-vault exec gc-playground-ting-chatbot -- aws s3api put-bucket-notification-configuration \
    --bucket hr-chatbot-documents-ap-northeast-1 \
    --notification-configuration '{
        "LambdaFunctionConfigurations": [{
            "LambdaFunctionArn": "arn:aws:lambda:ap-northeast-1:593713876380:function:hr-chatbot-file-processor",
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [{
                        "Name": "prefix",
                        "Value": "uploads/"
                    }]
                }
            }
        }]
    }'
```

### ⏳ 階段 1.8: 測試完整文件處理流程

#### 1.8.1 更新 Backend Lambda 環境變數

```bash
aws-vault exec gc-playground-ting-chatbot -- aws lambda update-function-configuration \
    --function-name hr-chatbot-backend \
    --environment "Variables={
        DB_SECRET_NAME=hr-chatbot/database,
        APP_SECRET_NAME=hr-chatbot/app-secrets,
        ENABLE_RAG=true,
        LLM_MODEL_ID=amazon.nova-pro-v1:0,
        EMBEDDING_MODEL_ID=cohere.embed-v4:0,
        USE_S3=true,
        S3_BUCKET=hr-chatbot-documents-ap-northeast-1
    }"
```

#### 1.8.2 測試文件上傳

1. 通過 API Gateway 上傳測試文件:
   ```bash
   curl -X POST https://8lvsiaz5nl.execute-api.ap-northeast-1.amazonaws.com/upload/document \
       -H "Authorization: Bearer $TOKEN" \
       -F "files=@test-document.pdf"
   ```

2. 檢查 S3 Bucket:
   ```bash
   aws-vault exec gc-playground-ting-chatbot -- \
       aws s3 ls s3://hr-chatbot-documents-ap-northeast-1/uploads/
   ```

3. 檢查 File Processor Lambda Logs:
   ```bash
   aws-vault exec gc-playground-ting-chatbot -- \
       aws logs tail /aws/lambda/hr-chatbot-file-processor --follow
   ```

4. 驗證數據庫記錄:
   - 檢查 `documents` 表狀態變為 `completed`
   - 檢查 `document_chunks` 表有對應的 chunks

---

## 架構變更總結

### 舊架構 (同步處理)

```
User → API Gateway → Backend Lambda
                         │
                         │ ① 存到 /tmp (臨時)
                         │ ② 解析 + Embedding (耗時)
                         │ ③ 存入 Aurora
                         │
                         └─→ 回應用戶 (慢，30-60秒)
```

**問題**:
- ❌ 用戶等待時間長
- ❌ 大文件可能超時
- ❌ 文件在 /tmp，Lambda 回收後消失

### 新架構 (異步處理)

```
User → API Gateway → Backend Lambda
                         │
                         │ ① 上傳到 S3 (快速)
                         └─→ 回應用戶 "上傳成功" (2-3秒)

S3 PutObject Event
    │
    └─→ File Processor Lambda
            │
            │ ② 從 S3 讀取
            │ ③ 解析 + Embedding
            │ ④ 存入 Aurora
            │ ⑤ 更新狀態
            └─→ 完成 (背景處理)
```

**優點**:
- ✅ 用戶快速得到回應
- ✅ 支援大文件處理
- ✅ 文件持久保存在 S3
- ✅ 處理失敗可重試

---

## 成本影響

### 新增成本

| 項目 | 月成本 | 說明 |
|------|--------|------|
| S3 存儲 | ~$1 | 假設 10GB 文件 |
| S3 請求 | ~$0.1 | 少量 PUT/GET 請求 |
| File Processor Lambda | ~$3 | 額外的處理時間 |
| S3 Gateway Endpoint | $0 | **免費!** |
| **總計** | **~$4/月** | 微小增加 |

**原有成本**: ~$75/月
**新成本**: ~$79/月
**增加**: $4/月 (5.3% 增加)

---

## 回滾計劃

如果新架構出現問題，可以快速回滾:

1. 更新 Backend Lambda 環境變數:
   ```bash
   USE_S3=false
   ```

2. 系統自動恢復到本地 `/tmp` 處理模式

3. 移除 S3 Event Notification:
   ```bash
   aws s3api put-bucket-notification-configuration \
       --bucket hr-chatbot-documents-ap-northeast-1 \
       --notification-configuration '{}'
   ```

---

## 監控建議

### CloudWatch Metrics

1. **File Processor Lambda**:
   - Duration (處理時間)
   - Error count and rate
   - Concurrent executions
   - Throttles

2. **S3 Bucket**:
   - NumberOfObjects
   - BucketSizeBytes
   - 4xxErrors, 5xxErrors

### CloudWatch Logs

```bash
# Backend Lambda
aws logs tail /aws/lambda/hr-chatbot-backend --follow

# File Processor Lambda
aws logs tail /aws/lambda/hr-chatbot-file-processor --follow
```

### CloudWatch Alarms (建議設置)

```bash
# File Processor 錯誤率 > 5%
aws cloudwatch put-metric-alarm \
    --alarm-name file-processor-high-error-rate \
    --alarm-description "File Processor Lambda error rate exceeds 5%" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Average \
    --period 300 \
    --threshold 0.05 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=hr-chatbot-file-processor
```

---

## 參考資料

- [AWS Lambda with S3 Events](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html)
- [S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)
- [Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [VPC Endpoints for S3](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html)

---

**維護者**: Ting Zhang
**最後更新**: 2025-12-03
**下一步**: 執行階段 1.6-1.8
