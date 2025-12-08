# Authentication & User Management Guide

本文件說明新的用戶管理與認證系統。

## 概述

系統現在使用完整的用戶帳號管理，包含：

- ✅ 用戶註冊（username + email + password）
- ✅ 密碼加密（bcrypt）
- ✅ JWT Token 認證
- ✅ 用戶資料庫表

## 環境設定

### 必須參數

`.env` 檔案現在需要 **2 個必須參數**：

```bash
# 1. Secret Key (用於 JWT 簽名)
SECRET_KEY=your-secret-key-here

# 2. Database URL
DATABASE_URL=postgresql://postgres:password@localhost:5432/hr_chatbot
```

### 生成 SECRET_KEY

```bash
# 方法 1: 使用 Python 腳本
python scripts/generate_secret_key.py

# 方法 2: 使用 openssl
openssl rand -hex 32

# 方法 3: 使用 Python 直接生成
python -c "import secrets; print(secrets.token_hex(32))"
```

### 快速設定

```bash
# 使用最小配置範本
cp .env.minimal .env

# 或使用完整配置範本
cp .env.example .env

# 編輯 .env（至少要設定 SECRET_KEY 和 DATABASE_URL）
nano .env
```

## 資料庫變更

### 新增 users 表

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_is_active ON users(is_active);
```

### 更新 conversations 表

`user_id` 欄位從 `VARCHAR(255)` 改為 `UUID`，並關聯到 `users.id`：

```sql
ALTER TABLE conversations
ALTER COLUMN user_id TYPE UUID USING user_id::uuid,
ADD CONSTRAINT fk_conversations_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### 執行遷移

```bash
# 如果已有舊資料庫，建議重建
dropdb hr_chatbot
createdb hr_chatbot

# 初始化新的資料庫
./scripts/init_db.sh

# 或使用 Alembic 遷移
alembic revision --autogenerate -m "Add users table and update conversations"
alembic upgrade head
```

## API 端點

### 1. 註冊新用戶

**POST** `/auth/register`

**Request Body:**

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe" // optional
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Status Codes:**

- `201 Created`: 註冊成功
- `400 Bad Request`: 用戶名或 email 已存在

### 2. 登入

**POST** `/auth/login`

**Request Body:**

```json
{
  "username": "john_doe",
  "password": "SecurePassword123"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Status Codes:**

- `200 OK`: 登入成功
- `401 Unauthorized`: 用戶名或密碼錯誤

### 3. 使用 Token 存取受保護端點

所有需要認證的端點現在使用 **Bearer Token** 認證：

```bash
# 舊方式（已移除）
curl -H "X-User-Id: john_doe" http://localhost:8000/chat/conversations

# 新方式（使用 JWT Token）
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:8000/chat/conversations
```

## 認證流程

### 完整流程圖

```
┌─────────────┐
│   使用者     │
└──────┬──────┘
       │
       │ 1. POST /auth/register (or /auth/login)
       ↓
┌─────────────────────┐
│  FastAPI Backend    │
│  - 驗證資料          │
│  - 創建用戶 (註冊)   │
│  - 驗證密碼 (登入)   │
│  - 生成 JWT Token   │
└──────┬──────────────┘
       │
       │ 2. Return access_token
       ↓
┌─────────────┐
│   使用者     │
│ (儲存 token) │
└──────┬──────┘
       │
       │ 3. POST /chat/message
       │    Authorization: Bearer <token>
       ↓
┌─────────────────────┐
│  FastAPI Backend    │
│  - 驗證 JWT Token   │
│  - 從 token 取得    │
│    user_id         │
│  - 查詢 User 資料   │
│  - 執行操作         │
└─────────────────────┘
```

### JWT Token 內容

Token 包含：

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000", // user_id
  "exp": 1234567890 // expiration timestamp
}
```

**Token 有效期**: 預設 7 天（可在 `.env` 設定 `ACCESS_TOKEN_EXPIRE_MINUTES`）

## 安全性

### 密碼處理

- ✅ 使用 **bcrypt** 加密密碼
- ✅ 密碼絕不以明文儲存
- ✅ 驗證時使用 `passlib` 的安全比對

### JWT Token

- ✅ 使用 **HS256** 演算法簽名
- ✅ Token 包含過期時間
- ✅ SECRET_KEY 必須保密
- ✅ Token 在 request header 傳遞（不在 URL）

### 最佳實踐

1. **SECRET_KEY 管理**
   - ❌ 不要提交到 git
   - ❌ 不要使用範例值
   - ✅ 每個環境使用不同的 key
   - ✅ 定期輪換（至少每年一次）

2. **密碼要求**（建議在前端實作）
   - 最少 8 字元
   - 包含大小寫字母、數字、特殊字元
   - 不使用常見密碼

3. **Token 管理**
   - 使用 HTTPS 傳輸
   - 不要在 localStorage 儲存敏感資訊
   - 實作 token refresh 機制（未來）

## 程式碼範例

### Python (Backend)

#### 驗證當前使用者

```python
from src.api.deps import CurrentUser
from src.models import User

@router.get("/me")
def get_current_user_info(current_user: CurrentUser) -> dict:
    return {
        "user_id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
```

### JavaScript (Frontend - Gradio 或 Nuxt3)

#### 註冊

```javascript
async function register(username, email, password) {
  const response = await fetch("http://localhost:8000/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });

  if (response.ok) {
    const data = await response.json();
    // 儲存 token
    localStorage.setItem("access_token", data.access_token);
    return data;
  } else {
    throw new Error("Registration failed");
  }
}
```

#### 登入

```javascript
async function login(username, password) {
  const response = await fetch("http://localhost:8000/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (response.ok) {
    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    return data;
  } else {
    throw new Error("Login failed");
  }
}
```

#### 使用 Token 呼叫 API

```javascript
async function sendMessage(message) {
  const token = localStorage.getItem("access_token");

  const response = await fetch("http://localhost:8000/chat/message", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });

  return response.json();
}
```

## 測試

### 手動測試

```bash
# 1. 註冊用戶
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123456"
  }'

# 儲存返回的 access_token

# 2. 登入
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test123456"
  }'

# 3. 使用 token 存取受保護端點
TOKEN="your-access-token-here"

curl http://localhost:8000/chat/conversations \
  -H "Authorization: Bearer $TOKEN"

# 4. 發送訊息
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Hello!"}'
```

### 使用 API 文件測試

1. 啟動後端: `./scripts/start_backend.sh`
2. 開啟 http://localhost:8000/docs
3. 使用 "Authorize" 按鈕輸入 token
4. 測試各個端點

## 遷移指南

### 從舊系統遷移

如果你已經有使用舊的簡易認證系統：

#### 步驟 1: 備份資料

```bash
pg_dump hr_chatbot > backup.sql
```

#### 步驟 2: 重建資料庫

```bash
dropdb hr_chatbot
createdb hr_chatbot
./scripts/init_db.sh
```

#### 步驟 3: 更新前端程式碼

**Gradio** (`src/app.py`):

- 移除 `X-User-Id` header
- 改用 `Authorization: Bearer <token>` header
- 更新登入流程（username + password）
- 儲存 `access_token`

**範例修改**（需要手動更新 `src/app.py`）:

```python
# 舊的登入
def login(username):
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username}
    )
    current_user["user_id"] = response.json()["user_id"]

# 新的登入
def login(username, password):
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    data = response.json()
    current_user["access_token"] = data["access_token"]

# 舊的 API 呼叫
response = requests.post(
    f"{API_BASE_URL}/chat/message",
    headers={"X-User-Id": current_user["user_id"]},
    json={"message": message}
)

# 新的 API 呼叫
response = requests.post(
    f"{API_BASE_URL}/chat/message",
    headers={"Authorization": f"Bearer {current_user['access_token']}"},
    json={"message": message}
)
```

## 故障排除

### 錯誤: ValidationError for SECRET_KEY

**原因**: `.env` 缺少 `SECRET_KEY`

**解決**:

```bash
python scripts/generate_secret_key.py
# 將生成的 key 加入 .env
```

### 錯誤: 401 Unauthorized

**原因**: Token 無效或過期

**解決**:

1. 確認 token 格式正確: `Bearer <token>`
2. 重新登入獲取新 token
3. 檢查 token 是否過期

### 錯誤: User not found

**原因**: Token 中的 user_id 在資料庫中不存在

**解決**:

1. 重新註冊或登入
2. 檢查資料庫是否正確遷移

### 錯誤: 400 Username already registered

**原因**: 用戶名已被使用

**解決**: 使用不同的用戶名

## 相關文件

- [API Documentation](http://localhost:8000/docs) - 互動式 API 文件
- [Database Schema](./database_schema.md) - 資料庫結構
- [Local Development Guide](./local_development.md) - 本地開發指南
