"""
FastAPI main application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, chat, upload

# Create FastAPI app
app = FastAPI(
    title="HR Chatbot API",
    description="API for HR Chatbot with RAG capabilities",
    version="0.0.1",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(upload.router)


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {
        "message": "HR Chatbot API",
        "version": "0.0.1",
        "docs": "/docs",
    }


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
