"""
Gradio frontend application for HR Chatbot with registration and login.
"""

import gradio as gr

from src.core.config import settings
from src.frontend.services.session import session
from src.frontend.tabs.chat_tab import (
    create_chat_tab,
    load_conversations_with_status,
    new_conversation,
    send_message,
)
from src.frontend.tabs.documents_tab import (
    create_documents_tab,
    delete_document,
    refresh_documents,
    upload_file,
)
from src.frontend.tabs.login_tab import create_login_tab, login
from src.frontend.tabs.register_tab import create_register_tab, register


def logout() -> tuple[str, gr.update, gr.update, gr.update, gr.update, gr.update, gr.update]:
    """
    Logout current user.

    Returns:
        tuple: (status message, status visibility update, tabs update, send_btn update,
                upload_btn update, new_chat_btn update, refresh_btn update)
    """
    # Clear user session
    session.reset()

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
        (
            reg_username_input,
            reg_email_input,
            reg_password_input,
            reg_confirm_password_input,
            reg_full_name_input,
            register_btn,
        ) = create_register_tab()

        # Login tab (index 1)
        login_username_input, login_password_input, login_btn = create_login_tab()

        # Chat tab (index 2)
        (
            chatbot,
            msg_input,
            send_btn,
            new_chat_btn,
            refresh_btn,
            conversation_list,
            logout_btn,
        ) = create_chat_tab()

        # Document Management tab (index 3)
        (
            file_upload,
            upload_btn,
            document_list,
            refresh_docs_btn,
            delete_doc_id,
            delete_btn,
        ) = create_documents_tab()

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
        outputs=[
            unified_status,
            unified_status,
            tabs,
            send_btn,
            upload_btn,
            new_chat_btn,
            refresh_btn,
        ],
    )

    # Event handlers - Login
    login_btn.click(
        fn=login,
        inputs=[login_username_input, login_password_input],
        outputs=[
            unified_status,
            unified_status,
            tabs,
            send_btn,
            upload_btn,
            new_chat_btn,
            refresh_btn,
        ],
    )

    # Event handlers - Logout
    logout_btn.click(
        fn=logout,
        outputs=[
            unified_status,
            unified_status,
            tabs,
            send_btn,
            upload_btn,
            new_chat_btn,
            refresh_btn,
        ],
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
    print(f"Frontend URL: http://localhost:{settings.GRADIO_PORT}")
    print(f"Backend API:  {settings.BACKEND_API_URL}")
    print(f"API Docs:     {settings.BACKEND_API_URL}/docs")
    print("=" * 60)
    print(f"\n⚠️  Make sure FastAPI backend is running on {settings.BACKEND_API_URL}\n")
    demo.launch(server_name=settings.GRADIO_HOST, server_port=settings.GRADIO_PORT)
