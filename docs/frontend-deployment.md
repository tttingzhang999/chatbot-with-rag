# HR Chatbot Frontend Deployment Guide

## 架構說明

這是一個使用 **CloudFront + S3** 的現代化 React 部署架構:

```
使用者 → Route53 (DNS) → CloudFront (CDN) → S3 (靜態檔案)
         ↓
     ACM Certificate (HTTPS)
```

### 為什麼選擇 CloudFront + S3?

1. **成本更低**: 比 App Runner 便宜很多,靜態網站每月可能只需 $1-5
2. **效能更好**: CloudFront 全球 CDN,邊緣節點快取提升載入速度
3. **擴展性高**: 自動處理流量尖峰,無需擔心容量
4. **維護簡單**: 無需管理容器或伺服器
5. **適合 SPA**: React/Vue/Angular 等單頁應用的最佳實踐

## 架構元件

### 1. S3 Bucket (`ting-hr-chatbot-frontend`)
- 存放 React 建置後的靜態檔案 (`dist/`)
- 設定為私有 (透過 CloudFront OAC 存取)
- 區域: `ap-northeast-1` (Tokyo)

### 2. CloudFront Distribution
- 全球 CDN 加速內容傳遞
- 使用 Origin Access Control (OAC) 安全存取 S3
- 支援 HTTPS (使用 ACM 憑證)
- 自訂網域: `ting-hr-chatbot.goingcloud.ai`
- 快取策略:
  - `index.html`: no-cache (確保使用者總是獲得最新版本)
  - `/assets/*`: 1 年快取 (immutable)
  - 其他檔案: 1 小時快取

### 3. ACM Certificate
- SSL/TLS 憑證提供 HTTPS
- 區域: `us-east-1` (CloudFront 要求)
- DNS 驗證 (自動透過 Route53)

### 4. Route53
- A 記錄: `ting-hr-chatbot.goingcloud.ai` → CloudFront
- AAAA 記錄: IPv6 支援
- Hosted Zone: `goingcloud.ai` (Z085163319K6AHT4RRWR4)

## 部署步驟

### 首次部署

#### 步驟 1: 部署基礎設施

```bash
cd infrastructure/terraform

# 初始化 Terraform (如果還沒做過)
terraform init

# 檢查變更
terraform plan

# 部署基礎設施
terraform apply
```

Terraform 會創建:
- S3 bucket
- CloudFront distribution
- Route53 DNS 記錄
- ACM 憑證驗證

**注意**: ACM 憑證驗證可能需要 5-10 分鐘。

#### 步驟 2: 取得 CloudFront Distribution ID

```bash
terraform output cloudfront_distribution_id
```

將輸出的 Distribution ID 填入 `apps/frontend/deploy.sh` 的 `CLOUDFRONT_DISTRIBUTION_ID` 變數:

```bash
CLOUDFRONT_DISTRIBUTION_ID="E1234567890ABC"  # 你的 Distribution ID
```

#### 步驟 3: 部署 React 應用

```bash
cd ../../apps/frontend

# 執行部署腳本
./deploy.sh
```

部署腳本會:
1. 安裝 npm 依賴
2. 建置 React 應用 (`npm run build`)
3. 上傳檔案到 S3
4. 清除 CloudFront 快取

#### 步驟 4: 驗證部署

等待 2-3 分鐘讓 DNS 傳播,然後訪問:

```
https://ting-hr-chatbot.goingcloud.ai
```

### 後續更新部署

後續只需要執行步驟 3:

```bash
cd apps/frontend
./deploy.sh
```

## 部署腳本說明

`deploy.sh` 做了以下事情:

1. **安裝依賴**: `npm install`
2. **建置應用**: `npm run build` (產生 `dist/` 目錄)
3. **上傳到 S3**:
   - 靜態資源 (`/assets/*`): 1 年快取
   - `index.html`: no-cache (確保版本更新)
   - `robots.txt`: 1 小時快取
4. **清除 CloudFront 快取**: 立即生效新版本

## 故障排除

### 1. 網站顯示 403 Forbidden

**原因**: S3 bucket policy 或 CloudFront OAC 設定錯誤

**解決**:
```bash
cd infrastructure/terraform
terraform apply  # 重新套用設定
```

### 2. 路由不工作 (React Router 404)

**原因**: CloudFront 沒有正確處理 SPA 路由

**解決**: 檢查 `cloudfront.tf` 中的 `custom_error_response` 設定:
```hcl
custom_error_response {
  error_code         = 404
  response_code      = 200
  response_page_path = "/index.html"
}
```

### 3. 更新沒有生效

**原因**: CloudFront 快取

**解決**:
```bash
# 手動清除快取
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*" \
  --profile tf-gc-playground
```

或確保 `deploy.sh` 中的 `CLOUDFRONT_DISTRIBUTION_ID` 已設定。

### 4. SSL 憑證錯誤

**原因**: ACM 憑證未驗證或區域錯誤

**解決**:
- 確認 ACM 憑證在 `us-east-1` 區域
- 檢查 Route53 中的驗證記錄是否已創建
```bash
terraform output acm_certificate_arn
```

### 5. DNS 不解析

**原因**: DNS 傳播延遲

**解決**:
- 等待 5-10 分鐘
- 檢查 DNS 記錄:
```bash
dig ting-hr-chatbot.goingcloud.ai
```

## 監控與維護

### 查看 CloudFront 存取日誌

```bash
aws cloudfront get-distribution --id E1234567890ABC --profile tf-gc-playground
```

### 查看 S3 bucket 內容

```bash
aws s3 ls s3://ting-hr-chatbot-frontend/ --profile tf-gc-playground --region ap-northeast-1
```

### 估算成本

- S3 儲存: ~$0.023/GB/月
- CloudFront 傳輸: ~$0.085/GB (前 10TB)
- CloudFront 請求: ~$0.0075/10,000 次
- Route53 Hosted Zone: ~$0.50/月

**預估**: 小型應用約 $1-5/月

## 最佳實踐

1. **版本控制**: 使用 Git tag 標記每次部署
2. **環境變數**: React 建置時注入 API endpoint
3. **快取策略**: 使用檔案雜湊值 (Vite 自動處理)
4. **監控**: 啟用 CloudFront 存取日誌
5. **備份**: 定期備份 S3 bucket
6. **成本優化**: 使用 CloudFront PriceClass_200 (已設定)

## CI/CD 整合 (選用)

### GitHub Actions 範例

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: Deploy
        run: |
          cd apps/frontend
          ./deploy.sh
```

## 清理資源

如果需要刪除所有資源:

```bash
# 1. 清空 S3 bucket
aws s3 rm s3://ting-hr-chatbot-frontend --recursive --profile tf-gc-playground

# 2. 刪除 Terraform 資源
cd infrastructure/terraform
terraform destroy
```

## 重要檔案

- `infrastructure/terraform/cloudfront.tf`: CloudFront 和 S3 設定
- `infrastructure/terraform/route53.tf`: DNS 和 ACM 憑證設定
- `infrastructure/terraform/outputs.tf`: Terraform 輸出
- `apps/frontend/deploy.sh`: 部署腳本
- `apps/frontend/vite.config.ts`: Vite 建置設定

## 聯絡資訊

- Owner: TingZhang
- Project: hr-chatbot
- Retention: 2025-12-31
