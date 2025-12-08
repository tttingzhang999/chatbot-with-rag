"""
Chat conversation tab component.
"""

import gradio as gr
import requests

from src.frontend.services.api_client import api
from src.frontend.services.session import session
from src.frontend.utils.config import BOT_AVATAR_IMAGE


def send_message(
    message: str,
    chat_history: list,
) -> tuple[list, str, str, gr.update]:
    """
    Send message to API and get response.

    Args:
        message: User message
        chat_history: Current chat history in messages format

    Returns:
        tuple: (updated chat history, empty message box, status message, status visibility update)
    """
    if not message or not message.strip():
        return chat_history, "", "", gr.update(visible=False)

    if not session.is_authenticated():
        chat_history.append({"role": "assistant", "content": "請先登入"})
        return chat_history, "", "❌ 請先登入", gr.update(visible=True)

    try:
        # Send message to API
        response = api.send_message(message=message, conversation_id=session.get_conversation_id())

        if response.status_code == 200:
            data = response.json()
            session.set_conversation_id(data["conversation_id"])

            # Add to chat history in messages format
            chat_history.append({"role": "user", "content": message})
            chat_history.append(
                {"role": "assistant", "content": data["assistant_message"]["content"]}
            )
            return chat_history, "", "✅ 訊息已發送", gr.update(visible=True)
        else:
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": f"Error: {response.text}"})
            return (
                chat_history,
                "",
                f"❌ 發送失敗: {response.text}",
                gr.update(visible=True),
            )

    except requests.exceptions.RequestException as e:
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": f"連接錯誤: {e}"})
        return chat_history, "", f"❌ 連接錯誤: {e}", gr.update(visible=True)


def new_conversation() -> tuple[list, str, gr.update]:
    """
    Start a new conversation.

    Returns:
        tuple: (empty chat history, status message, status visibility update)
    """
    session.clear_conversation()
    return [], "✅ 已開始新對話", gr.update(visible=True)


def load_conversations() -> list:
    """
    Load user's conversation history.

    Returns:
        list: List of conversations
    """
    if not session.is_authenticated():
        return []

    try:
        response = api.get_conversations()

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
        list: Chat history in messages format
    """
    if not conversation_id or not session.is_authenticated():
        return []

    try:
        response = api.get_conversation(conversation_id)

        if response.status_code == 200:
            data = response.json()
            session.set_conversation_id(conversation_id)

            # Convert to messages format
            messages = data["messages"]
            chat_history = [
                {
                    "role": msg.get("role", "user" if i % 2 == 0 else "assistant"),
                    "content": msg["content"],
                }
                for i, msg in enumerate(messages)
            ]

            return chat_history
        return []

    except requests.exceptions.RequestException:
        return []


def create_chat_tab() -> tuple:
    """
    Create chat tab with UI and event handlers.

    Returns:
        tuple: (tab components) for event binding
    """
    with gr.Tab("對話", id=2), gr.Row():
        # Left sidebar - User info and conversation history
        with gr.Column(scale=1):
            gr.Markdown("### 👤 使用者資訊")
            gr.Markdown("未登入")
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
                type="messages",
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

    return (
        chatbot,
        msg_input,
        send_btn,
        new_chat_btn,
        refresh_btn,
        conversation_list,
        logout_btn,
    )
