"""
Document management tab component.
"""

from contextlib import ExitStack

import gradio as gr
import requests

from src.core.config import settings
from src.frontend.services.api_client import api
from src.frontend.services.session import session


def upload_file(files) -> tuple[str, gr.update, list]:
    """
    Upload one or multiple files to server.

    Args:
        files: Uploaded file or list of files

    Returns:
        tuple: (status message, status visibility update, updated document list)
    """
    if not files:
        return "❌ 請選擇檔案", gr.update(visible=True), load_documents()

    if not session.is_authenticated():
        return "❌ 請先登入", gr.update(visible=True), []

    # Handle both single file and multiple files
    # Gradio returns a list when file_count="multiple"
    if not isinstance(files, list):
        files = [files]

    try:
        # Prepare files for multipart upload using ExitStack for multiple context managers
        with ExitStack() as stack:
            files_to_upload = []
            for file in files:
                fh = stack.enter_context(open(file.name, "rb"))
                files_to_upload.append(("files", (file.name, fh, "application/octet-stream")))

            response = api.upload_documents(files=files_to_upload)

        if response.status_code == 200:
            data = response.json()
            # Reload documents list
            documents = load_documents()

            # Generate detailed message
            message = f"✅ {data['message']}\n\n"
            if data.get("failed", 0) > 0:
                message += "失敗的文件:\n"
                for result in data.get("results", []):
                    if result["status"] == "failed":
                        message += f"  • {result['filename']}: {result['error_message']}\n"

            return message.strip(), gr.update(visible=True), documents
        else:
            return (
                f"❌ 上傳失敗: {response.text}",
                gr.update(visible=True),
                load_documents(),
            )

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
    if not session.is_authenticated():
        return []

    try:
        response = api.get_documents()

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

    if not session.is_authenticated():
        return "❌ 請先登入", gr.update(visible=True), []

    try:
        response = api.delete_document(document_id.strip())

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


def create_documents_tab() -> tuple:
    """
    Create document management tab with UI and event handlers.

    Returns:
        tuple: (tab components) for event binding
    """
    with gr.Tab("文件管理", id=3):
        gr.Markdown("## 📄 文件管理")
        gr.Markdown("上傳文件以建立知識庫，支援 PDF、TXT、DOCX 格式")

        with gr.Row():
            # Left column - Upload section
            with gr.Column(scale=1):
                gr.Markdown("### 📤 上傳文件")
                file_upload = gr.File(
                    label="選擇檔案 (可多選)",
                    file_types=[f".{ext}" for ext in settings.SUPPORTED_FILE_TYPES],
                    file_count="multiple",
                )
                upload_btn = gr.Button("上傳", variant="primary", interactive=False)

                gr.Markdown("---")
                gr.Markdown("### ℹ️ 說明")
                gr.Markdown(
                    """
                **支援格式:**
                - PDF (.pdf)
                - 文字檔 (.txt)
                - Word 文件 (.docx)

                **多文件上傳:**
                - 可一次選擇多個文件上傳
                - 文件會按順序依次處理
                - 某個文件失敗不影響其他文件

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
                """
                )

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

    return (
        file_upload,
        upload_btn,
        document_list,
        refresh_docs_btn,
        delete_doc_id,
        delete_btn,
    )
