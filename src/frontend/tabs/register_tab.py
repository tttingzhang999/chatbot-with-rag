"""
User registration tab component.
"""

import gradio as gr
import requests

from src.frontend.services.api_client import api
from src.frontend.services.session import session


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
        return (
            "❌ 請輸入使用者名稱",
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    if not email or not email.strip():
        return (
            "❌ 請輸入電子郵件",
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    if not password or len(password) < 6:
        return (
            "❌ 密碼至少需要 6 個字元",
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    if password != confirm_password:
        return (
            "❌ 密碼不一致",
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    try:
        # Send registration request
        response = api.register(
            username=username.strip(),
            email=email.strip(),
            password=password,
            full_name=full_name.strip() if full_name and full_name.strip() else None,
        )

        if response.status_code == 201:
            data = response.json()
            # Store user info and token
            session.set_user(
                user_id=data["user_id"],
                username=data["username"],
                email=data["email"],
                access_token=data["access_token"],
            )

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
            return (
                f"❌ {error_detail}",
                gr.update(visible=True),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

    except requests.exceptions.RequestException as e:
        return (
            f"❌ 無法連接到伺服器: {e}",
            gr.update(visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )


def create_register_tab() -> tuple:
    """
    Create registration tab with UI and event handlers.

    Returns:
        tuple: (tab components, register button) for event binding
    """
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

    return (
        reg_username_input,
        reg_email_input,
        reg_password_input,
        reg_confirm_password_input,
        reg_full_name_input,
        register_btn,
    )
