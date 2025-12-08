# Docker 構建命令參考 (Apple Silicon)

**適用於**: Apple M1/M2/M3 (ARM64) 構建 AWS Lambda 鏡像 (AMD64)

---

## 重要說明

- AWS Lambda 只支援 `linux/amd64` (x86_64) 架構
- Apple Silicon 是 `linux/arm64` 架構
- **必須**使用 `--platform linux/amd64` 進行交叉編譯
- Docker Desktop 會自動使用 QEMU 處理交叉編譯

---

## File Processor Lambda

### 構建鏡像

```bash
docker build --platform linux/amd64 \
    -f Dockerfile.file-processor \
    -t hr-chatbot-file-processor:latest .
```

### 推送到 ECR

```bash
# 1. 登錄 ECR
aws-vault exec gc-playground-ting-chatbot -- \
    aws ecr get-login-password --region ap-northeast-1 | \
    docker login --username AWS --password-stdin \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com

# 2. Tag 鏡像
docker tag hr-chatbot-file-processor:latest \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:latest

# 3. 推送
docker push 593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:latest
```

---

## Backend Lambda

### 構建鏡像

```bash
docker build --platform linux/amd64 \
    -f Dockerfile.backend \
    -t hr-chatbot-backend:latest .
```

### 推送到 ECR

```bash
# 1. 登錄 ECR
aws-vault exec gc-playground-ting-chatbot -- \
    aws ecr get-login-password --region ap-northeast-1 | \
    docker login --username AWS --password-stdin \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com

# 2. Tag 鏡像
docker tag hr-chatbot-backend:latest \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:latest

# 3. 推送
docker push 593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:latest
```

### 更新 Lambda

```bash
aws-vault exec gc-playground-ting-chatbot -- aws lambda update-function-code \
    --function-name hr-chatbot-backend \
    --image-uri 593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-backend:latest \
    --region ap-northeast-1
```

---

## Frontend (App Runner)

### 構建鏡像

```bash
docker build --platform linux/amd64 \
    -f Dockerfile.frontend \
    -t hr-chatbot-frontend:latest .
```

### 推送到 ECR

```bash
# 1. 登錄 ECR
aws-vault exec gc-playground-ting-chatbot -- \
    aws ecr get-login-password --region ap-northeast-1 | \
    docker login --username AWS --password-stdin \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com

# 2. Tag 鏡像
docker tag hr-chatbot-frontend:latest \
    593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-frontend:latest

# 3. 推送
docker push 593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-frontend:latest
```

---

## 本地測試

### 測試 File Processor Lambda

```bash
docker run --rm --platform linux/amd64 \
    -e AWS_REGION=ap-northeast-1 \
    -e DB_SECRET_NAME=hr-chatbot/database \
    -e APP_SECRET_NAME=hr-chatbot/app-secrets \
    hr-chatbot-file-processor:latest \
    python -m src.lambda_handlers.file_processor
```

### 測試 Backend Lambda

```bash
docker run --rm --platform linux/amd64 \
    -p 9000:8080 \
    -e AWS_REGION=ap-northeast-1 \
    -e DB_SECRET_NAME=hr-chatbot/database \
    -e APP_SECRET_NAME=hr-chatbot/app-secrets \
    hr-chatbot-backend:latest
```

### 測試 Frontend

```bash
docker run --rm --platform linux/amd64 \
    -p 7860:7860 \
    -e API_ENDPOINT=http://localhost:8000 \
    hr-chatbot-frontend:latest
```

---

## 常見問題

### Q: 為什麼需要 `--platform linux/amd64`?

A: AWS Lambda 只支援 x86_64 架構。Apple Silicon 是 ARM64 架構,如果不指定平台,構建的鏡像無法在 Lambda 上運行,會出現錯誤:

```
exec format error
```

### Q: 交叉編譯會影響性能嗎?

A: **構建時**會稍慢 (QEMU 模擬),但**運行時**沒有影響 (在 AWS Lambda 上以原生 x86_64 運行)。

### Q: 如何驗證鏡像平台?

```bash
docker inspect hr-chatbot-file-processor:latest | grep Architecture
# 應該顯示: "Architecture": "amd64"
```

### Q: 如果忘記加 `--platform` 怎麼辦?

重新構建即可:

```bash
# 刪除錯誤的鏡像
docker rmi hr-chatbot-file-processor:latest

# 重新構建 (加上 --platform)
docker build --platform linux/amd64 \
    -f Dockerfile.file-processor \
    -t hr-chatbot-file-processor:latest .
```

---

## 構建優化

### 使用 BuildKit (推薦)

```bash
# 啟用 BuildKit (更快的構建速度)
export DOCKER_BUILDKIT=1

docker build --platform linux/amd64 \
    -f Dockerfile.file-processor \
    -t hr-chatbot-file-processor:latest .
```

### Multi-platform 構建 (進階)

如果需要同時支援多個平台:

```bash
# 創建 builder
docker buildx create --use

# 構建並推送多平台鏡像
docker buildx build --platform linux/amd64,linux/arm64 \
    -f Dockerfile.file-processor \
    -t 593713876380.dkr.ecr.ap-northeast-1.amazonaws.com/hr-chatbot-file-processor:latest \
    --push .
```

---

## 參考資料

- [Docker Multi-platform Builds](https://docs.docker.com/build/building/multi-platform/)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Apple Silicon and Docker](https://docs.docker.com/desktop/mac/apple-silicon/)

---

**維護者**: Ting Zhang
**最後更新**: 2025-12-03
