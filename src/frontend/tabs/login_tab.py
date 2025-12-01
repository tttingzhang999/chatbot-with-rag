"""
User login tab component.
"""

import gradio as gr
import requests

from src.frontend.services.api_client import api
from src.frontend.services.session import session


def login(
    username: str, password: str
) -> tuple[gr.update, gr.update, gr.update, gr.update, gr.update, gr.update]:
    """
    Handle user login.

    Args:
        username: Username
        password: Password

    Returns:
        tuple: (status update, tabs update, send_btn update,
                upload_btn update, new_chat_btn update, refresh_btn update)
    """
    # Validation
    if not username or not username.strip():
        return (
            gr.update(value="❌ 請輸入使用者名稱", visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    if not password:
        return (
            gr.update(value="❌ 請輸入密碼", visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )

    try:
        response = api.login(username=username.strip(), password=password)

        if response.status_code == 200:
            data = response.json()
            # Store user info and token
            session.set_user(
                user_id=data["user_id"],
                username=data["username"],
                email=data["email"],
                access_token=data["access_token"],
            )

            return (
                gr.update(value=f"✅ 歡迎回來, {username}!", visible=True),  # Status with visibility
                gr.update(selected=2),  # Switch to chat tab (index 2)
                gr.update(interactive=True),  # Enable send_btn
                gr.update(interactive=True),  # Enable upload_btn
                gr.update(interactive=True),  # Enable new_chat_btn
                gr.update(interactive=True),  # Enable refresh_btn
            )
        else:
            error_detail = response.json().get("detail", "登入失敗")
            return (
                gr.update(value=f"❌ {error_detail}", visible=True),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

    except requests.exceptions.RequestException as e:
        return (
            gr.update(value=f"❌ 無法連接到伺服器: {e}", visible=True),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
        )


def create_login_tab() -> tuple:
    """
    Create login tab with UI and event handlers.

    Returns:
        tuple: (tab components, login button) for event binding
    """
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

    return login_username_input, login_password_input, login_btn
