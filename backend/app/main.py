from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ALLOWED_ORIGINS

from app.api import session_auth
from app.api.admin import user_manage
from app.api.admin import data_manage
from app.api.admin import chat_manage
from app.api.admin import vectordb_manage
from app.api.shared import chat, documents, vectordb

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=list(CORS_ALLOWED_ORIGINS),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)
app.include_router(session_auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(vectordb.router)

# Admin endpoint
app.include_router(user_manage.router)
app.include_router(data_manage.router)
app.include_router(chat_manage.router)
app.include_router(vectordb_manage.router)
