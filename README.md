# HR Chatbot with RAG

一個具備 RAG（Retrieval-Augmented Generation）功能的 HR 智能客服系統。

**專案時程**: 2025年11月 - 2025年12月底

**相關資源**: [Google Drive](https://drive.google.com/drive/u/1/folders/1KHnvLLubLUTg5nwfR3dZKgfWanQXw7UQ)

## 目錄

- [專案目標](#專案目標)
- [核心學習目標](#核心學習目標)
- [技術架構](#技術架構)
- [核心功能](#核心功能)
- [技術棧](#技術棧)
- [開發環境設定](#開發環境設定)
- [RAG 基礎概念](#rag-基礎概念)
- [專案進度](#專案進度)
- [開發規範](#開發規範)

## 專案目標

建構一個基於 AWS 服務的 HR Chatbot，具備以下特點：

- 多輪對話能力，能理解上下文
- 使用 RAG 技術提供準確的文件檢索
- 採用 Hybrid Search (Semantic Search + BM25) 提升檢索品質
- 完整的 AWS 雲端部署架構
- 生產級程式碼品質標準

## 核心學習目標

透過此專案，掌握以下三大核心能力：

1. **AWS 基本操作** - 從 GCP 遷移到 AWS，理解兩者差異與 AWS 服務特性
2. **程式開發** - 建立小型專案規模的開發規範與架構
3. **GenAI 基礎知識** - 理解 RAG、Embedding、LLM 等生成式 AI 核心概念

## 技術架構

### 系統架構圖

```
用戶 (HTTPS)
  ↓
Amazon Route 53 (DNS: *.goingcloud.ai)
  ↓
Amazon API Gateway (SSL via ACM)
  ↓
AWS Lambda (Container Image from ECR)
  ├─ Amazon Aurora PostgreSQL Serverless (pgvector)
  ├─ Amazon S3 (Raw Documents)
  ├─ Amazon Bedrock
  │   ├─ Claude Sonnet 4 (LLM)
  │   └─ Cohere Embed v4 (Embedding)
  └─ AWS Secrets Manager
```

### RAG 處理流程

```
文件處理流程:
Raw Documents (S3) → Lambda Trigger → Chunking → Embedding → PostgreSQL (pgvector + BM25)

查詢流程:
User Question → Embedding → Hybrid Search (Semantic + BM25) → Retrieved Chunks → LLM (Claude Sonnet 4) → Answer
```

### AWS 服務架構

#### 資料儲存與管理
- **Amazon Aurora PostgreSQL Serverless** - 主要資料庫，儲存處理後的文件與向量資料
- **Amazon S3** - 儲存原始文件（Raw Data）
- **AWS Secrets Manager** - 管理資料庫連線金鑰與敏感資訊

#### AI/ML 服務
- **Amazon Bedrock**
  - **Claude Sonnet 4** - 用於多輪對話的 LLM 模型
  - **Cohere Embed v4** - 用於文件 Embedding 的模型

#### 運算與部署
- **AWS Lambda** - 執行文件前處理與 Chatbot 後端邏輯（Container Image 方式）
- **Amazon ECR** - 儲存 Docker 映像檔
- **AWS IAM** - 權限管理與角色設定

#### 網路與對外服務
- **Amazon API Gateway** - 建立 REST API，提供 `/chat`、`/query` 等路由
- **AWS Certificate Manager** - SSL 憑證管理
- **Amazon Route 53** - DNS 管理，設定自訂網域（.goingcloud.ai）

#### 開發工具
- **AWS Vault** - 本地開發時的 AWS credentials 管理工具

### AWS vs GCP 服務對照

| 功能 | GCP | AWS (本專案使用) |
|------|-----|------------------|
| 關聯式資料庫 | Cloud SQL | Aurora PostgreSQL Serverless |
| 物件儲存 | Cloud Storage | S3 |
| Serverless 運算 | Cloud Functions | Lambda |
| 容器註冊表 | Artifact Registry | ECR |
| API 管理 | API Gateway / Cloud Endpoints | API Gateway |
| 密鑰管理 | Secret Manager | Secrets Manager |
| DNS | Cloud DNS | Route 53 |
| 憑證管理 | Certificate Manager | Certificate Manager |
| AI/ML 平台 | Vertex AI | Bedrock |

## 核心功能

### 1. 文件處理（Document Processing）

**目標**: 讓文件可以透過 BM25 (TFIDF) 與 Semantic Search 進行搜尋

**處理流程**:
1. 文件上傳至 S3
2. 觸發 Lambda 進行前處理
   - Chunking（文件分段）
   - 生成 Embeddings（使用 Cohere Embed v4）
   - 建立 BM25 索引資料
3. 儲存至 Aurora PostgreSQL（使用 pgvector plugin）

**技術要點**:
- 所有前處理必須透過程式碼自動化完成
- 使用 pgvector plugin 儲存向量資料
- 密鑰管理透過 AWS Secrets Manager

### 2. 文件檢索（Document Retrieval）

**目標**: 建構 Hybrid Search 功能，找到最佳的 RAG Hyperparameters

**搜尋策略**:
- **Semantic Search**: 使用向量相似度（Cosine Similarity）
- **BM25**: 基於 TFIDF 的關鍵字搜尋
- **Hybrid Search**: 結合兩種方法（例如：10 個 chunks 中，5 個來自 Semantic Search，5 個來自 BM25）

**Hyperparameters 調整**:
- Chunk size（分段大小）
- Overlap size（重疊大小）
- Retrieved chunks 數量
- Semantic vs BM25 的比例

### 3. 多輪對話（Multi-turn Conversation）

**目標**: 建構可以多輪對話的 Chatbot，能繼承上下文內容

**技術實作**:
- 使用 Claude Sonnet 4 作為 LLM
- System Prompt 設計
- User Prompt 設計
- Context Engineering（對話歷史管理）

### 4. 前端界面（Frontend）

**技術選擇**: Gradio

**功能需求**:
- 登入畫面
- 對話界面
- 文件上傳功能（待確認）

## 技術棧

### 核心框架
- **RAG 框架**: LangChain / LlamaIndex（待選擇）
- **前端**: Gradio
- **部署**: Docker + AWS Lambda (Container Image)

### AI/ML
- **LLM**: Claude Sonnet 4 (Amazon Bedrock)
- **Embedding**: Cohere Embed v4 (Amazon Bedrock)
- **向量資料庫**: PostgreSQL + pgvector

### 開發工具
- **套件管理**: uv
- **程式碼品質**: ruff (linting)
- **Git Hooks**: pre-commit
- **AWS CLI**: AWS Vault

## 開發環境設定

### 前置需求

- Python 3.11+
- Docker
- AWS CLI
- AWS Vault
- uv (Python package manager)

### 本地開發設定

```bash
# 1. 安裝 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 建立虛擬環境並安裝套件
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# 3. 設定 pre-commit hooks
pre-commit install

# 4. 設定 AWS Vault
aws-vault add <profile-name>
aws-vault exec <profile-name> -- aws s3 ls
```

### 環境變數設定

建立 `.env` 檔案（請勿提交至版本控制）：

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=<your-profile>

# Database
DB_SECRET_NAME=<secret-manager-name>

# S3
DOCUMENT_BUCKET=<s3-bucket-name>

# Bedrock Models
LLM_MODEL_ID=anthropic.claude-sonnet-4
EMBEDDING_MODEL_ID=cohere.embed-v4
```

## RAG 基礎概念

### 核心技術

- **Documents → Indexing** - 文件索引化流程
- **Embeddings** - 將文字轉換為向量表示
- **Chunking（切片）** - 文件分段策略
  - Chunk Size - 每段文字的大小
  - Overlapping chunks - 段落間的重疊部分
- **Semantic Search** - 語義搜尋
  - Cosine Similarity - 計算向量相似度的方法
- **Hybrid Search** - 結合多種搜尋方法
  - Semantic Search + BM25
- **Self-Reflective RAG**
  - Graded Reranking - 分級重新排序
  - Adaptive RAG - 自適應 RAG

### 技術名詞

- **BM25** - Best Matching 25，資訊檢索的排序函數
- **TFIDF** - Term Frequency-Inverse Document Frequency
- **pgvector** - PostgreSQL 的向量資料庫擴充
- **Cosine Similarity** - 餘弦相似度，用於計算向量相似性

## 專案進度

### Phase 0: 基礎架構 ✅ (已完成)
- [x] 設定本地開發環境（uv, pre-commit, ruff）
- [x] 設計資料庫 schema (PostgreSQL + pgvector)
- [x] 建立 SQLAlchemy models
- [x] 配置 Alembic 資料庫遷移
- [x] 建立 FastAPI 後端架構
- [x] 開發 Gradio 前端界面
- [x] 實作基本登入功能
- [x] 實作多輪對話與歷史記錄
- [x] 建立本地開發環境文件

### Phase 1: 環境準備與 AWS 熟悉
- [x] 設定 AWS Vault
- [x] 建立 AWS 帳號權限與 IAM 設定
- [x] 熟悉各 AWS 服務的基本操作

### Phase 2: 文件處理 Pipeline
- [ ] 設計 Chunking 策略
- [ ] 實作 S3 → Lambda 觸發機制
- [ ] 整合 Cohere Embed v4 進行 Embedding
- [ ] 建立 Aurora PostgreSQL 資料庫與 pgvector
- [ ] 實作 BM25 索引建立

### Phase 3: 檢索系統
- [ ] 實作 Semantic Search
- [ ] 實作 BM25 搜尋
- [ ] 建立 Hybrid Search 機制
- [ ] 使用 Validation Set 進行 Hyperparameter 調整
- [ ] 使用 Test Set 驗證成效

### Phase 4: 對話系統
- [x] 整合 Claude Sonnet 4（目前使用 echo 回應）
- [x] 實作 Prompt Engineering
- [ ] 實作 Context 管理優化
- [ ] 測試對話品質

### Phase 5: 前端與部署
- [x] 開發 Gradio 前端界面（本地版）
- [x] 實作登入功能（簡易版）
- [ ] Docker 容器化
- [ ] 部署至 AWS（Lambda + API Gateway）
- [ ] 設定 SSL 與自訂網域
- [ ] 整體測試

### Phase 6: 成果整理
- [ ] 撰寫技術報告
- [ ] 繪製架構圖與流程圖
- [ ] 整理實驗數據與分析
- [ ] 準備成果分享

## 開發規範

### 程式碼品質

- 使用 **ruff** 進行 linting
- 使用 **pre-commit** hooks 確保程式碼品質
- 遵循 PEP 8 編碼規範
- 適當的註解與文件字串

### Git 工作流程

```bash
# 1. 建立功能分支
git checkout -b feature/your-feature-name

# 2. 開發並提交
git add .
git commit -m "feat: add document processing pipeline"

# 3. 推送至遠端
git push origin feature/your-feature-name

# 4. 建立 Merge Request
```

### 提交訊息規範

使用 Conventional Commits 格式：

```
feat: 新功能
fix: 錯誤修復
docs: 文件更新
refactor: 重構
test: 測試相關
chore: 雜項（依賴更新等）
```

### 成本控制原則

1. 使用 AWS 服務前評估用量與費用
2. 優先在本地環境測試
3. 使用 Serverless 服務（Lambda, Aurora Serverless）以降低成本
4. 注意不要影響既有資源（特別是 Route 53）

## 部署指南

### 本地開發 (推薦開始方式)

快速啟動本地開發環境（不需 AWS 服務）：

```bash
# 1. 初始化資料庫
./scripts/init_db.sh

# 2. 啟動後端 (Terminal 1)
./scripts/start_backend.sh

# 3. 啟動前端 (Terminal 2)
./scripts/start_frontend.sh

# 4. 測試 API
python scripts/test_api.py
```

存取應用程式：
- 前端界面: http://localhost:7860
- API 文件: http://localhost:8000/docs

詳細說明請參考 [本地開發指南](docs/local_development.md)

### 生產環境測試（含 AWS 服務）

```bash
# 執行文件處理測試
python -m src.document_processor

# 執行檢索測試
python -m src.retrieval
```

### Docker 建置

```bash
# 建置 Docker 映像
docker build -t hr-chatbot:latest .

# 本地測試
docker run -p 8080:8080 hr-chatbot:latest

# 推送至 ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag hr-chatbot:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/hr-chatbot:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/hr-chatbot:latest
```

### AWS 部署

詳細部署步驟請參考 [部署文件](docs/deployment.md)（待建立）

## 資料集

- **Validation Set**: 用來調整 Hyperparameters
- **Test Set**: 用於最終評分與成效驗證

資料集內容與格式請參考 `data/README.md`（待建立）

## 開發建議

1. ✅ **尋求協助**: 有問題隨時找主管、Mentor、其他同事
2. ✅ **善用工具**: 可以使用任何 AI 開發工具輔助
3. ✅ **先本地後雲端**: 先把各個部件在 local 跑通，再上 AWS
4. ⚠️ **成本意識**: 使用 AWS 服務前注意預估用量與費用
5. ⚠️ **資源隔離**: 切勿影響既有其他人的相關 Resource（特別是 Route 53）

## 參考資源

- [LangChain 文件](https://python.langchain.com/)
- [LlamaIndex 文件](https://docs.llamaindex.ai/)
- [Amazon Bedrock 開發者指南](https://docs.aws.amazon.com/bedrock/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [RAG 最佳實踐](https://www.pinecone.io/learn/retrieval-augmented-generation/)

## License

Internal Project - All Rights Reserved

## 聯絡方式

專案負責人: Ting Zhang
Mentor: Micheal

---

**最後更新**: 2025-11-25
