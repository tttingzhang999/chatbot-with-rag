"""
Gradio frontend application for HR Chatbot.
"""

import requests
from datetime import datetime

import gradio as gr

# API configuration
API_BASE_URL = "http://localhost:8000"

# Global state
current_user = {"user_id": None, "username": None}
current_conversation_id = None


def login(username: str) -> tuple[str, gr.update, gr.update]:
    """
    Handle user login.

    Args:
        username: Username input

    Returns:
        tuple: (status message, login tab visibility, chat tab visibility)
    """
    if not username or not username.strip():
        return "請輸入使用者名稱", gr.update(visible=True), gr.update(visible=False)

    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username},
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            current_user["user_id"] = data["user_id"]
            current_user["username"] = data["username"]
            return (
                f"歡迎, {username}!",
                gr.update(visible=False),
                gr.update(visible=True),
            )
        else:
            return "登入失敗，請重試", gr.update(visible=True), gr.update(visible=False)

    except requests.exceptions.RequestException as e:
        return (
            f"無法連接到伺服器: {e}",
            gr.update(visible=True),
            gr.update(visible=False),
        )


def send_message(
    message: str,
    chat_history: list,
) -> tuple[list, str]:
    """
    Send message to API and get response.

    Args:
        message: User message
        chat_history: Current chat history

    Returns:
        tuple: (updated chat history, empty message box)
    """
    global current_conversation_id

    if not message or not message.strip():
        return chat_history, ""

    if not current_user["user_id"]:
        chat_history.append(("Error", "請先登入"))
        return chat_history, ""

    try:
        # Send message to API
        response = requests.post(
            f"{API_BASE_URL}/chat/message",
            json={
                "message": message,
                "conversation_id": current_conversation_id,
            },
            headers={"X-User-Id": current_user["user_id"]},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            current_conversation_id = data["conversation_id"]

            # Add to chat history
            chat_history.append((message, data["assistant_message"]["content"]))
            return chat_history, ""
        else:
            chat_history.append((message, f"Error: {response.text}"))
            return chat_history, ""

    except requests.exceptions.RequestException as e:
        chat_history.append((message, f"連接錯誤: {e}"))
        return chat_history, ""


def new_conversation() -> tuple[list, str]:
    """
    Start a new conversation.

    Returns:
        tuple: (empty chat history, status message)
    """
    global current_conversation_id
    current_conversation_id = None
    return [], "已開始新對話"


def load_conversations() -> list:
    """
    Load user's conversation history.

    Returns:
        list: List of conversations
    """
    if not current_user["user_id"]:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/chat/conversations",
            headers={"X-User-Id": current_user["user_id"]},
            timeout=5,
        )

        if response.status_code == 200:
            conversations = response.json()
            return [
                {
                    "id": conv["id"],
                    "title": conv["title"],
                    "updated": conv["updated_at"],
                    "messages": conv["message_count"],
                }
                for conv in conversations
            ]
        return []

    except requests.exceptions.RequestException:
        return []


def load_conversation_messages(conversation_id: str) -> list:
    """
    Load messages from a specific conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        list: Chat history
    """
    global current_conversation_id

    if not conversation_id or not current_user["user_id"]:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/chat/conversations/{conversation_id}",
            headers={"X-User-Id": current_user["user_id"]},
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


def upload_file(file) -> str:
    """
    Upload file to server.

    Args:
        file: Uploaded file

    Returns:
        str: Status message
    """
    if not file:
        return "請選擇檔案"

    if not current_user["user_id"]:
        return "請先登入"

    try:
        with open(file.name, "rb") as f:
            files = {"file": (file.name, f, "application/octet-stream")}
            response = requests.post(
                f"{API_BASE_URL}/upload/document",
                files=files,
                headers={"X-User-Id": current_user["user_id"]},
                timeout=30,
            )

        if response.status_code == 200:
            data = response.json()
            return f"✅ {data['message']}"
        else:
            return f"❌ 上傳失敗: {response.text}"

    except requests.exceptions.RequestException as e:
        return f"❌ 上傳錯誤: {e}"
    except Exception as e:
        return f"❌ 錯誤: {e}"


# Create Gradio interface
with gr.Blocks(title="HR Chatbot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 HR Chatbot")

    # Login tab
    with gr.Tab("登入", id="login_tab", visible=True) as login_tab:
        gr.Markdown("## 歡迎使用 HR Chatbot")
        gr.Markdown("請輸入您的使用者名稱登入")

        with gr.Row():
            username_input = gr.Textbox(
                label="使用者名稱",
                placeholder="請輸入使用者名稱",
                scale=3,
            )
            login_btn = gr.Button("登入", variant="primary", scale=1)

        login_status = gr.Textbox(label="狀態", interactive=False)

    # Chat tab
    with gr.Tab("對話", id="chat_tab", visible=False) as chat_tab:
        with gr.Row():
            # Left sidebar - Conversation history
            with gr.Column(scale=1):
                gr.Markdown("### 對話歷史")
                new_chat_btn = gr.Button("➕ 新對話", variant="primary")
                refresh_btn = gr.Button("🔄 重新整理")

                conversation_list = gr.Dataframe(
                    headers=["ID", "標題", "更新時間", "訊息數"],
                    datatype=["str", "str", "str", "number"],
                    col_count=(4, "fixed"),
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("### 文件上傳")
                file_upload = gr.File(label="選擇檔案", file_types=[".pdf", ".txt", ".docx"])
                upload_btn = gr.Button("上傳")
                upload_status = gr.Textbox(label="上傳狀態", interactive=False)

            # Main chat area
            with gr.Column(scale=3):
                gr.Markdown("### 對話")
                chatbot = gr.Chatbot(
                    label="聊天訊息",
                    height=500,
                    show_copy_button=True,
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="輸入訊息",
                        placeholder="在此輸入您的問題...",
                        scale=4,
                        lines=2,
                    )
                    send_btn = gr.Button("發送", variant="primary", scale=1)

                chat_status = gr.Textbox(label="狀態", interactive=False)

    # Event handlers
    login_btn.click(
        fn=login,
        inputs=[username_input],
        outputs=[login_status, login_tab, chat_tab],
    )

    send_btn.click(
        fn=send_message,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )

    msg_input.submit(
        fn=send_message,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input],
    )

    new_chat_btn.click(
        fn=new_conversation,
        outputs=[chatbot, chat_status],
    )

    refresh_btn.click(
        fn=load_conversations,
        outputs=[conversation_list],
    )

    upload_btn.click(
        fn=upload_file,
        inputs=[file_upload],
        outputs=[upload_status],
    )


if __name__ == "__main__":
    print("Starting Gradio frontend on http://localhost:7860")
    print("Make sure FastAPI backend is running on http://localhost:8000")
    demo.launch(server_name="0.0.0.0", server_port=7860)
