# HR Chatbot with RAG

一個具備 RAG（Retrieval-Augmented Generation）功能的智能客服系統。

## 快速導航

### 🚀 快速開始

```bash
# 1. 複製環境變數範本
cp .env.example .env

# 2. 產生 SECRET_KEY 並設定 .env
python scripts/generate_secret_key.py

# 3. 初始化資料庫
./scripts/init_db.sh

# 4. 啟動後端（Terminal 1）
./scripts/start_backend.sh

# 5. 啟動前端（Terminal 2）
./scripts/start_frontend.sh

# 6. 存取應用
# 前端: http://localhost:7860
# API文件: http://localhost:8000/docs
```

### 📝 常用指令

| 功能           | 指令                                               |
| -------------- | -------------------------------------------------- |
| 建立資料庫遷移 | `uv run alembic revision --autogenerate -m "說明"` |
| 套用資料庫遷移 | `uv run alembic upgrade head`                      |
| 程式碼檢查     | `ruff check .`                                     |
| 自動修復       | `ruff check --fix .`                               |
| 格式化程式碼   | `ruff format .`                                    |
| 執行測試       | `pytest`                                           |

### 📚 重要文件

- [本地開發指南](docs/local_development.md) - 詳細的本地開發說明
- [環境變數設定](#環境變數設定) - 完整的環境變數說明
- [開發指令](#開發指令) - 所有開發相關指令
- [專案進度](#專案進度) - 目前開發進度

---

## 目錄

- [專案目標](#專案目標)
- [核心學習目標](#核心學習目標)
- [技術架構](#技術架構)
- [核心功能](#核心功能)
- [技術棧](#技術棧)
- [開發環境設定](#開發環境設定)
- [環境變數設定](#環境變數設定)
- [開發指令](#開發指令)
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
Amazon Route 53 (DNS: *.going.cloud)
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

| 功能            | GCP                           | AWS (本專案使用)             |
| --------------- | ----------------------------- | ---------------------------- |
| 關聯式資料庫    | Cloud SQL                     | Aurora PostgreSQL Serverless |
| 物件儲存        | Cloud Storage                 | S3                           |
| Serverless 運算 | Cloud Functions               | Lambda                       |
| 容器註冊表      | Artifact Registry             | ECR                          |
| API 管理        | API Gateway / Cloud Endpoints | API Gateway                  |
| 密鑰管理        | Secret Manager                | Secrets Manager              |
| DNS             | Cloud DNS                     | Route 53                     |
| 憑證管理        | Certificate Manager           | Certificate Manager          |
| AI/ML 平台      | Vertex AI                     | Bedrock                      |

## 核心功能

### 1. 使用者認證系統 ✅

**已實作功能**:

- JWT-based 認證機制
- 使用者註冊與登入
- 密碼安全儲存（bcrypt hashing）
- Token 管理與驗證

**技術實作**:

- FastAPI 認證依賴注入
- SQLAlchemy ORM
- python-jose 與 passlib

### 2. 多輪對話系統 ✅

**已實作功能**:

- 整合 AWS Bedrock Claude Sonnet 4
- 多輪對話與上下文管理
- 對話歷史儲存與檢索
- HR 專屬 system prompts
- 支援 RAG 增強回應

**技術實作**:

- LangChain 框架整合
- 對話歷史資料庫儲存
- Context window 管理（可設定歷史輪數）
- 專業的 HR Chatbot 角色設定

### 3. 文件處理系統 ⏳

**已實作**:

- 多檔案上傳支援（PDF、DOCX、TXT、DOC）
- 基本文件解析（pypdf、python-docx）
- 文件分段（chunking）策略
- 文件資料庫儲存

**待完成**:

- Embedding 生成（Cohere Embed v4）
- BM25 索引建立
- S3 儲存整合（生產環境）
- Lambda 觸發處理流程

**技術要點**:

- 所有前處理透過程式碼自動化
- PostgreSQL + pgvector 儲存向量資料
- 配置化的 chunk size 與 overlap

### 4. 文件檢索系統（RAG）⏳

**目標**: 建構 Hybrid Search 功能，找到最佳的 RAG Hyperparameters

**規劃實作**:

- **Semantic Search**: 使用向量相似度（Cosine Similarity）
- **BM25**: 基於 TFIDF 的關鍵字搜尋
- **Hybrid Search**: 結合兩種方法（可調整比例）

**Hyperparameters 調整方向**:

- Chunk size（預設 512 字元）
- Overlap size（預設 128 字元）
- Top-K chunks（預設 10）
- Semantic vs BM25 比例（預設 0.5）
- Relevance threshold（預設 0.3）

**目前狀態**:

- ✅ 建立基礎架構（retrieval_service.py）
- ⏳ 待整合 embedding 模型
- ⏳ 待實作搜尋演算法

### 5. Gradio 前端界面 ✅

**已實作功能**:

- 現代化登入界面（含註冊/登入切換）
- 即時對話界面
- 對話歷史側邊欄
- 多檔案上傳功能
- 錯誤處理與使用者回饋
- 自訂品牌樣式（bot avatar）

**技術特點**:

- RESTful API 整合
- 非同步請求處理
- Session 管理
- 響應式設計

## 技術棧

### 後端框架

- **Web 框架**: FastAPI (高效能 async Python web framework)
- **ASGI 伺服器**: Uvicorn
- **ORM**: SQLAlchemy 2.0
- **資料庫遷移**: Alembic
- **RAG 框架**: LangChain (已整合)
- **驗證與授權**: JWT (python-jose) + bcrypt (passlib)

### 前端

- **UI 框架**: Gradio 4.x
- **API 通訊**: HTTP/REST
- **樣式**: 自訂 CSS + Gradio Blocks

### AI/ML 服務

- **LLM**: Claude 3.5 Sonnet (Amazon Bedrock)
  - Model ID: `anthropic.claude-3-5-sonnet-20240620-v1:0`
- **Embedding**: Cohere Embed v4 (Amazon Bedrock) - 待整合
  - Model ID: `cohere.embed-v4:0`
  - 維度: 1536

### 資料庫

- **本地開發**: PostgreSQL 14+
- **生產環境**: Aurora PostgreSQL Serverless
- **向量擴充**: pgvector
- **資料處理**: pypdf, python-docx

### AWS 服務

- **運算**: Lambda (Container Image from ECR)
- **儲存**: S3 (documents), Aurora PostgreSQL (vectors + metadata)
- **AI/ML**: Bedrock (Claude, Cohere)
- **網路**: API Gateway, Route 53, Certificate Manager
- **安全**: Secrets Manager, IAM

### 開發工具

- **套件管理**: uv (快速 Python 套件管理器)
- **程式碼品質**:
  - Linter: ruff
  - Formatter: ruff format
  - Git hooks: pre-commit
- **測試**: pytest (含 pytest-asyncio, pytest-cov)
- **AWS 認證**: aws-vault (本地開發)
- **容器化**: Docker + ECR

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

複製 `.env.example` 並重新命名為 `.env`（請勿提交至版本控制）：

```bash
cp .env.example .env
```

#### 必要環境變數

以下為**必須設定**的環境變數：

| 變數名稱       | 說明                      | 範例值                                                     | 如何產生                  |
| -------------- | ------------------------- | ---------------------------------------------------------- | ------------------------- |
| `SECRET_KEY`   | JWT token 簽署金鑰        | `a1b2c3d4e5f6...`                                          | `openssl rand -hex 32`    |
| `DATABASE_URL` | PostgreSQL 資料庫連線字串 | `postgresql://postgres:password@localhost:5432/hr_chatbot` | 參考 `scripts/init_db.sh` |

#### AWS 相關環境變數（需使用 Bedrock 時）

| 變數名稱          | 說明                         | 預設值      | 備註                        |
| ----------------- | ---------------------------- | ----------- | --------------------------- |
| `AWS_REGION`      | AWS 服務區域                 | `us-east-1` | 使用 Bedrock 時必填         |
| `AWS_PROFILE`     | AWS 設定檔名稱               | -           | 本地開發用 aws-vault 時需要 |
| `DB_SECRET_NAME`  | AWS Secrets Manager 金鑰名稱 | -           | 僅生產環境需要              |
| `DOCUMENT_BUCKET` | S3 儲存桶名稱                | -           | 僅生產環境需要              |

#### 可選環境變數（有預設值）

<details>
<summary>點擊展開查看所有可選環境變數</summary>

**應用程式設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `APP_NAME` | 應用程式名稱 | `HR Chatbot` |
| `DEBUG` | 除錯模式 | `false` |

**伺服器設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `UVICORN_HOST` | FastAPI 伺服器主機 | `0.0.0.0` |
| `UVICORN_PORT` | FastAPI 伺服器埠號 | `8000` |
| `UVICORN_RELOAD` | 自動重新載入 | `false` |
| `GRADIO_HOST` | Gradio 前端主機 | `0.0.0.0` |
| `GRADIO_PORT` | Gradio 前端埠號 | `7860` |

**API 設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `API_TITLE` | API 標題 | `HR Chatbot API` |
| `API_DESCRIPTION` | API 描述 | `API for HR Chatbot with RAG capabilities` |
| `API_VERSION` | API 版本 | `0.3.0` |
| `CORS_ORIGINS` | CORS 允許來源 | `*` |

**檔案上傳設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `UPLOAD_DIR` | 本地上傳目錄 | `uploads` |
| `SUPPORTED_FILE_TYPES` | 支援的檔案類型 | `pdf,txt,docx,doc` |

**前端設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `BACKEND_API_URL` | 後端 API 網址 | `http://localhost:8000` |
| `ASSETS_DIR` | 前端資源目錄 | `assets` |
| `BOT_AVATAR_FILENAME` | 機器人頭像檔名 | `bot_avatar.png` |

**HTTP 設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `HTTP_TIMEOUT_DEFAULT` | 預設 HTTP 超時（秒） | `30` |
| `HTTP_TIMEOUT_UPLOAD` | 上傳超時（秒） | `30` |
| `HTTP_TIMEOUT_SHORT` | 快速請求超時（秒） | `30` |

**資料庫查詢限制**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `CONVERSATION_HISTORY_LIMIT` | 對話歷史最大筆數 | `50` |
| `USER_CONVERSATIONS_LIMIT` | 使用者對話列表最大筆數 | `20` |

**Bedrock 模型設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `LLM_MODEL_ID` | LLM 模型 ID | `anthropic.claude-3-5-sonnet-20240620-v1:0` |
| `EMBEDDING_MODEL_ID` | Embedding 模型 ID | `cohere.embed-v4:0` |

**LLM 參數**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `LLM_TEMPERATURE` | 採樣溫度（0.0-1.0） | `0.7` |
| `LLM_TOP_P` | Nucleus 採樣參數 | `0.9` |
| `LLM_MAX_TOKENS` | 最大回應 tokens 數 | `2048` |
| `MAX_CONVERSATION_HISTORY` | 包含在上下文的對話輪數 | `10` |

**RAG 設定**
| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `ENABLE_RAG` | 啟用 RAG 功能 | `false` |
| `CHUNK_SIZE` | 文件分段大小（字元） | `512` |
| `CHUNK_OVERLAP` | 分段重疊大小（字元） | `128` |
| `TOP_K_CHUNKS` | 檢索的文件片段數量 | `10` |
| `SEMANTIC_SEARCH_RATIO` | 語義搜尋比例（0.0-1.0） | `0.5` |
| `RELEVANCE_THRESHOLD` | 相關度閾值（0.0-1.0） | `0.3` |
| `EMBEDDING_DIMENSION` | Embedding 向量維度 | `1536` |

</details>

## 開發指令

### 快速開始（本地開發）

適合初次使用或不需要 AWS Bedrock 功能的開發：

```bash
# 1. 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，設定 SECRET_KEY 和 DATABASE_URL

# 2. 產生 SECRET_KEY（複製輸出結果到 .env）
python scripts/generate_secret_key.py

# 3. 初始化資料庫
./scripts/init_db.sh

# 4. 啟動後端 API (Terminal 1)
./scripts/start_backend.sh
# 或: python -m uvicorn src.main:app --reload

# 5. 啟動前端界面 (Terminal 2)
./scripts/start_frontend.sh
# 或: python src/app.py

# 6. 測試 API（選用）
python scripts/test_api.py
```

**存取應用程式**：

- 🌐 前端界面: http://localhost:7860
- 📚 API 文件: http://localhost:8000/docs
- 🔧 OpenAPI JSON: http://localhost:8000/openapi.json

### 使用 AWS Bedrock

```bash
# 1. 設定 AWS Vault
aws-vault add <your-profile-name>

# 2. 在 .env 中設定 AWS_PROFILE 和 AWS_REGION
# AWS_PROFILE=<your-profile-name>
# AWS_REGION=us-east-1

# 3. 使用 AWS Vault 啟動後端
./scripts/start_backend_with_aws.sh
# 或: aws-vault exec <profile> -- python -m uvicorn src.main:app --reload

# 4. 測試文件處理（有上傳文件後）
python scripts/test_basic_processing.py

# 5. 測試 RAG 功能（有上傳文件後）
python scripts/test_rag.py
```

### 資料庫遷移（Database Migrations）

```bash
# 查看目前資料庫版本
uv run alembic current

# 查看遷移歷史
uv run alembic history

# 建立新的遷移（自動偵測模型變更）
uv run alembic revision --autogenerate -m "描述變更內容"

# 套用所有待執行的遷移
uv run alembic upgrade head

# 回退到上一個版本
uv run alembic downgrade -1

# 回退到特定版本
uv run alembic downgrade <revision_id>
```

### 程式碼品質檢查

```bash
# 執行 linting 檢查
ruff check .

# 自動修復 linting 問題
ruff check --fix .

# 格式化程式碼
ruff format .

# 執行所有 pre-commit hooks
pre-commit run --all-files

# 執行測試
pytest
```

### AWS 雲端部署

詳細部署步驟請參考 [部署文件](docs/deployment.md)（待建立）

## 參考資源

- [LangChain 文件](https://python.langchain.com/)
- [LlamaIndex 文件](https://docs.llamaindex.ai/)
- [Amazon Bedrock 開發者指南](https://docs.aws.amazon.com/bedrock/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [RAG 最佳實踐](https://www.pinecone.io/learn/retrieval-augmented-generation/)

## 聯絡方式

專案負責人: Ting Zhang [tingzhang@going.cloud](mailto:tingzhang@going.cloud)
