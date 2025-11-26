"""
Gradio frontend application for HR Chatbot with registration and login.
"""

from pathlib import Path

import gradio as gr
import requests

# Paths / configuration
API_BASE_URL = "http://localhost:8000"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BOT_AVATAR_PATH = ASSETS_DIR / "bot_avatar.png"
BOT_AVATAR_IMAGE = str(BOT_AVATAR_PATH) if BOT_AVATAR_PATH.exists() else None

# Global state
current_user = {
    "user_id": None,
    "username": None,
    "email": None,
    "access_token": None,
}
current_conversation_id = None


def get_auth_headers() -> dict:
    """Get authorization headers with JWT token."""
    if current_user["access_token"]:
        return {"Authorization": f"Bearer {current_user['access_token']}"}
    return {}


def register(
    username: str, email: str, password: str, confirm_password: str, full_name: str
) -> tuple[str, gr.update, gr.update, gr.update, gr.update, gr.update, gr.update]:
    """
    Handle user registration.

    Args:
        username: Username
        email: Email address
        password: Password
        confirm_password: Password confirmation
        full_name: Full name (optional)

    Returns:
        tuple: (status message, status visibility update, tabs update, send_btn update,
                upload_btn update, new_chat_btn update, refresh_btn update)
    """
    # Validation
    if not username or not username.strip():
        return "❌ 請輸入使用者名稱", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    if not email or not email.strip():
        return "❌ 請輸入電子郵件", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    if not password or len(password) < 6:
        return "❌ 密碼至少需要 6 個字元", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    if password != confirm_password:
        return "❌ 密碼不一致", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    try:
        # Prepare request data
        register_data = {
            "username": username.strip(),
            "email": email.strip(),
            "password": password,
        }

        if full_name and full_name.strip():
            register_data["full_name"] = full_name.strip()

        # Send registration request
        response = requests.post(
            f"{API_BASE_URL}/auth/register", json=register_data, timeout=5
        )

        if response.status_code == 201:
            data = response.json()
            # Store user info and token
            current_user["user_id"] = data["user_id"]
            current_user["username"] = data["username"]
            current_user["email"] = data["email"]
            current_user["access_token"] = data["access_token"]

            return (
                f"✅ 註冊成功！歡迎, {username}!",
                gr.update(visible=True),  # Show status
                gr.update(selected=2),  # Switch to chat tab (index 2)
                gr.update(interactive=True),  # Enable send_btn
                gr.update(interactive=True),  # Enable upload_btn (in doc management tab)
                gr.update(interactive=True),  # Enable new_chat_btn
                gr.update(interactive=True),  # Enable refresh_btn
            )
        else:
            error_detail = response.json().get("detail", "註冊失敗")
            return f"❌ {error_detail}", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    except requests.exceptions.RequestException as e:
        return f"❌ 無法連接到伺服器: {e}", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()


def login(username: str, password: str) -> tuple[str, gr.update, gr.update, gr.update, gr.update, gr.update, gr.update]:
    """
    Handle user login.

    Args:
        username: Username
        password: Password

    Returns:
        tuple: (status message, status visibility update, tabs update, send_btn update,
                upload_btn update, new_chat_btn update, refresh_btn update)
    """
    # Validation
    if not username or not username.strip():
        return "❌ 請輸入使用者名稱", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    if not password:
        return "❌ 請輸入密碼", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username.strip(), "password": password},
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            # Store user info and token
            current_user["user_id"] = data["user_id"]
            current_user["username"] = data["username"]
            current_user["email"] = data["email"]
            current_user["access_token"] = data["access_token"]

            return (
                f"✅ 歡迎回來, {username}!",
                gr.update(visible=True),  # Show status
                gr.update(selected=2),  # Switch to chat tab (index 2)
                gr.update(interactive=True),  # Enable send_btn
                gr.update(interactive=True),  # Enable upload_btn
                gr.update(interactive=True),  # Enable new_chat_btn
                gr.update(interactive=True),  # Enable refresh_btn
            )
        else:
            error_detail = response.json().get("detail", "登入失敗")
            return f"❌ {error_detail}", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    except requests.exceptions.RequestException as e:
        return f"❌ 無法連接到伺服器: {e}", gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()


def send_message(
    message: str,
    chat_history: list,
) -> tuple[list, str, str, gr.update]:
    """
    Send message to API and get response.

    Args:
        message: User message
        chat_history: Current chat history

    Returns:
        tuple: (updated chat history, empty message box, status message, status visibility update)
    """
    global current_conversation_id

    if not message or not message.strip():
        return chat_history, "", "", gr.update(visible=False)

    if not current_user["access_token"]:
        chat_history.append(("Error", "請先登入"))
        return chat_history, "", "❌ 請先登入", gr.update(visible=True)

    try:
        # Send message to API
        response = requests.post(
            f"{API_BASE_URL}/chat/message",
            json={
                "message": message,
                "conversation_id": current_conversation_id,
            },
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            current_conversation_id = data["conversation_id"]

            # Add to chat history
            chat_history.append((message, data["assistant_message"]["content"]))
            return chat_history, "", "✅ 訊息已發送", gr.update(visible=True)
        else:
            chat_history.append((message, f"Error: {response.text}"))
            return chat_history, "", f"❌ 發送失敗: {response.text}", gr.update(visible=True)

    except requests.exceptions.RequestException as e:
        chat_history.append((message, f"連接錯誤: {e}"))
        return chat_history, "", f"❌ 連接錯誤: {e}", gr.update(visible=True)


def new_conversation() -> tuple[list, str, gr.update]:
    """
    Start a new conversation.

    Returns:
        tuple: (empty chat history, status message, status visibility update)
    """
    global current_conversation_id
    current_conversation_id = None
    return [], "✅ 已開始新對話", gr.update(visible=True)


def load_conversations() -> list:
    """
    Load user's conversation history.

    Returns:
        list: List of conversations
    """
    if not current_user["access_token"]:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/chat/conversations",
            headers=get_auth_headers(),
            timeout=5,
        )

        if response.status_code == 200:
            conversations = response.json()
            return [
                [
                    conv["id"],
                    conv["title"],
                    conv["updated_at"],
                    conv["message_count"],
                ]
                for conv in conversations
            ]
        return []

    except requests.exceptions.RequestException:
        return []


def load_conversations_with_status():
    """
    Load conversations with loading status feedback.

    Returns:
        tuple: (conversation_list, status update)
    """
    try:
        conversations = load_conversations()
        if conversations:
            return conversations, gr.update(value="✅ 對話歷史已載入", visible=True)
        return [], gr.update(value="ℹ️ 目前沒有對話歷史", visible=True)
    except Exception as e:
        return [], gr.update(value=f"❌ 載入失敗: {str(e)}", visible=True)


def load_conversation_messages(conversation_id: str) -> list:
    """
    Load messages from a specific conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        list: Chat history
    """
    global current_conversation_id

    if not conversation_id or not current_user["access_token"]:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/chat/conversations/{conversation_id}",
            headers=get_auth_headers(),
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            current_conversation_id = conversation_id

            # Convert to chat history format
            chat_history = []
            messages = data["messages"]

            for i in range(0, len(messages) - 1, 2):
                if i + 1 < len(messages):
                    user_msg = messages[i]["content"]
                    assistant_msg = messages[i + 1]["content"]
                    chat_history.append((user_msg, assistant_msg))

            return chat_history
        return []

    except requests.exceptions.RequestException:
        return []


def upload_file(file) -> tuple[str, gr.update, list]:
    """
    Upload file to server.

    Args:
        file: Uploaded file

    Returns:
        tuple: (status message, status visibility update, updated document list)
    """
    if not file:
        return "❌ 請選擇檔案", gr.update(visible=True), load_documents()

    if not current_user["access_token"]:
        return "❌ 請先登入", gr.update(visible=True), []

    try:
        with open(file.name, "rb") as f:
            files = {"file": (file.name, f, "application/octet-stream")}
            response = requests.post(
                f"{API_BASE_URL}/upload/document",
                files=files,
                headers=get_auth_headers(),
                timeout=30,
            )

        if response.status_code == 200:
            data = response.json()
            # Reload documents list
            documents = load_documents()
            return f"✅ {data['message']}", gr.update(visible=True), documents
        else:
            return f"❌ 上傳失敗: {response.text}", gr.update(visible=True), load_documents()

    except requests.exceptions.RequestException as e:
        return f"❌ 上傳錯誤: {e}", gr.update(visible=True), load_documents()
    except Exception as e:
        return f"❌ 錯誤: {e}", gr.update(visible=True), load_documents()


def load_documents() -> list:
    """
    Load user's uploaded documents.

    Returns:
        list: List of documents
    """
    if not current_user["access_token"]:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/upload/documents",
            headers=get_auth_headers(),
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])

            # Format for display
            return [
                [
                    doc["id"],
                    doc["file_name"],
                    doc["file_type"],
                    f"{doc['file_size'] / 1024:.1f} KB",
                    doc["status"],
                    doc["chunk_count"],
                    doc["upload_date"],
                ]
                for doc in documents
            ]
        return []

    except requests.exceptions.RequestException:
        return []


def delete_document(document_id: str) -> tuple[str, gr.update, list]:
    """
    Delete a document.

    Args:
        document_id: Document ID

    Returns:
        tuple: (status message, status visibility update, updated document list)
    """
    if not document_id or not document_id.strip():
        return "❌ 請輸入文件ID", gr.update(visible=True), load_documents()

    if not current_user["access_token"]:
        return "❌ 請先登入", gr.update(visible=True), []

    try:
        response = requests.delete(
            f"{API_BASE_URL}/upload/documents/{document_id.strip()}",
            headers=get_auth_headers(),
            timeout=5,
        )

        if response.status_code == 200:
            documents = load_documents()
            return "✅ 文件已刪除", gr.update(visible=True), documents
        else:
            error_detail = response.json().get("detail", "刪除失敗")
            return f"❌ {error_detail}", gr.update(visible=True), load_documents()

    except requests.exceptions.RequestException as e:
        return f"❌ 刪除錯誤: {e}", gr.update(visible=True), load_documents()


def refresh_documents() -> list:
    """
    Refresh documents list.

    Returns:
        list: Updated document list
    """
    return load_documents()


def logout() -> tuple[str, gr.update, gr.update, gr.update, gr.update, gr.update, gr.update]:
    """
    Logout current user.

    Returns:
        tuple: (status message, status visibility update, tabs update, send_btn update,
                upload_btn update, new_chat_btn update, refresh_btn update)
    """
    global current_conversation_id

    # Clear user session
    current_user["user_id"] = None
    current_user["username"] = None
    current_user["email"] = None
    current_user["access_token"] = None
    current_conversation_id = None

    return (
        "✅ 已登出",
        gr.update(visible=True),  # Show status
        gr.update(selected=1),  # Switch to login tab (index 1)
        gr.update(interactive=False),  # Disable send_btn
        gr.update(interactive=False),  # Disable upload_btn
        gr.update(interactive=False),  # Disable new_chat_btn
        gr.update(interactive=False),  # Disable refresh_btn
    )


# Create Gradio interface
with gr.Blocks(title="HR Chatbot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 HR Chatbot with RAG")

    # Unified status display (visible across all tabs)
    unified_status = gr.Textbox(
        label="狀態",
        interactive=False,
        visible=False,
        container=True,
    )

    # Create tabs with controlled selection
    with gr.Tabs(selected=0) as tabs:
        # Register tab (index 0)
        with gr.Tab("註冊", id=0):
            gr.Markdown("## 📝 使用者註冊")
            gr.Markdown("建立新帳號以開始使用 HR Chatbot")

            with gr.Column():
                reg_username_input = gr.Textbox(
                    label="使用者名稱 *",
                    placeholder="請輸入使用者名稱",
                )
                reg_email_input = gr.Textbox(
                    label="電子郵件 *",
                    placeholder="your.email@example.com",
                )
                reg_full_name_input = gr.Textbox(
                    label="全名 (選填)",
                    placeholder="請輸入您的全名",
                )
                reg_password_input = gr.Textbox(
                    label="密碼 *",
                    placeholder="至少 6 個字元",
                    type="password",
                )
                reg_confirm_password_input = gr.Textbox(
                    label="確認密碼 *",
                    placeholder="再次輸入密碼",
                    type="password",
                )

                register_btn = gr.Button("註冊", variant="primary", size="lg")

                gr.Markdown("---")
                gr.Markdown("_已有帳號？請切換到「登入」分頁_")

        # Login tab (index 1)
        with gr.Tab("登入", id=1):
            gr.Markdown("## 🔐 使用者登入")
            gr.Markdown("使用您的帳號登入")

            with gr.Column():
                login_username_input = gr.Textbox(
                    label="使用者名稱",
                    placeholder="請輸入使用者名稱",
                )
                login_password_input = gr.Textbox(
                    label="密碼",
                    placeholder="請輸入密碼",
                    type="password",
                )

                login_btn = gr.Button("登入", variant="primary", size="lg")

                gr.Markdown("---")
                gr.Markdown("_還沒有帳號？請切換到「註冊」分頁_")

        # Chat tab (index 2)
        with gr.Tab("對話", id=2):
            with gr.Row():
                # Left sidebar - User info and conversation history
                with gr.Column(scale=1):
                    gr.Markdown("### 👤 使用者資訊")
                    user_info = gr.Markdown("未登入")
                    logout_btn = gr.Button("登出", variant="secondary")

                    gr.Markdown("---")
                    gr.Markdown("### 💬 對話歷史")
                    new_chat_btn = gr.Button("新對話", variant="primary", interactive=False)
                    refresh_btn = gr.Button("載入", interactive=False)

                    conversation_list = gr.Dataframe(
                        headers=["ID", "標題", "更新時間", "訊息數"],
                        datatype=["str", "str", "str", "number"],
                        col_count=(4, "fixed"),
                        interactive=False,
                        wrap=True,
                    )

                # Main chat area
                with gr.Column(scale=3):
                    gr.Markdown("### 💭 對話")
                    chatbot = gr.Chatbot(
                        label="聊天訊息",
                        height=500,
                        type="tuples",
                        show_copy_button=True,
                        avatar_images=(None, BOT_AVATAR_IMAGE),
                    )

                    with gr.Row():
                        msg_input = gr.Textbox(
                            label="輸入訊息",
                            placeholder="在此輸入您的問題...",
                            scale=4,
                            lines=2,
                        )
                        send_btn = gr.Button("發送 ✉️", variant="primary", scale=1, interactive=False)

        # Document Management tab (index 3)
        with gr.Tab("文件管理", id=3):
            gr.Markdown("## 📄 文件管理")
            gr.Markdown("上傳文件以建立知識庫，支援 PDF、TXT、DOCX 格式")

            with gr.Row():
                # Left column - Upload section
                with gr.Column(scale=1):
                    gr.Markdown("### 📤 上傳文件")
                    file_upload = gr.File(
                        label="選擇檔案",
                        file_types=[".pdf", ".txt", ".docx"],
                    )
                    upload_btn = gr.Button("上傳", variant="primary", interactive=False)

                    gr.Markdown("---")
                    gr.Markdown("### ℹ️ 說明")
                    gr.Markdown("""
                    **支援格式:**
                    - PDF (.pdf)
                    - 文字檔 (.txt)
                    - Word 文件 (.docx)

                    **處理流程:**
                    1. 上傳文件
                    2. 自動提取文字
                    3. 切分文字塊 (chunk)
                    4. 生成 embeddings
                    5. 建立 BM25 索引
                    6. 存入向量資料庫

                    **狀態說明:**
                    - `pending`: 等待處理
                    - `processing`: 處理中
                    - `completed`: 處理完成
                    - `failed`: 處理失敗
                    """)

                # Right column - Document list
                with gr.Column(scale=2):
                    gr.Markdown("### 📋 已上傳文件")

                    refresh_docs_btn = gr.Button("🔄 重新整理列表", variant="secondary")

                    document_list = gr.Dataframe(
                        headers=["ID", "檔案名稱", "類型", "大小", "狀態", "chunks", "上傳時間"],
                        datatype=["str", "str", "str", "str", "str", "number", "str"],
                        col_count=(7, "fixed"),
                        interactive=False,
                        wrap=True,
                    )

                    gr.Markdown("### 🗑️ 刪除文件")
                    with gr.Row():
                        delete_doc_id = gr.Textbox(
                            label="文件 ID",
                            placeholder="請輸入要刪除的文件 ID",
                            scale=3,
                        )
                        delete_btn = gr.Button("刪除", variant="stop", scale=1)

    # Event handlers - Register
    register_btn.click(
        fn=register,
        inputs=[
            reg_username_input,
            reg_email_input,
            reg_password_input,
            reg_confirm_password_input,
            reg_full_name_input,
        ],
        outputs=[unified_status, unified_status, tabs, send_btn, upload_btn, new_chat_btn, refresh_btn],
    )

    # Event handlers - Login
    login_btn.click(
        fn=login,
        inputs=[login_username_input, login_password_input],
        outputs=[unified_status, unified_status, tabs, send_btn, upload_btn, new_chat_btn, refresh_btn],
    )

    # Event handlers - Logout
    logout_btn.click(
        fn=logout,
        outputs=[unified_status, unified_status, tabs, send_btn, upload_btn, new_chat_btn, refresh_btn],
    )

    # Event handlers - Chat
    send_btn.click(
        fn=send_message,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input, unified_status, unified_status],
    )

    msg_input.submit(
        fn=send_message,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input, unified_status, unified_status],
    )

    new_chat_btn.click(
        fn=new_conversation,
        outputs=[chatbot, unified_status, unified_status],
    )

    refresh_btn.click(
        fn=load_conversations_with_status,
        outputs=[conversation_list, unified_status],
    )

    # Event handlers - Document Management
    upload_btn.click(
        fn=upload_file,
        inputs=[file_upload],
        outputs=[unified_status, unified_status, document_list],
    )

    refresh_docs_btn.click(
        fn=refresh_documents,
        outputs=[document_list],
    )

    delete_btn.click(
        fn=delete_document,
        inputs=[delete_doc_id],
        outputs=[unified_status, unified_status, document_list],
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting HR Chatbot Gradio Frontend")
    print("=" * 60)
    print("Frontend URL: http://localhost:7860")
    print("Backend API:  http://localhost:8000")
    print("API Docs:     http://localhost:8000/docs")
    print("=" * 60)
    print("\n⚠️  Make sure FastAPI backend is running on port 8000\n")
    demo.launch(server_name="0.0.0.0", server_port=7860)
