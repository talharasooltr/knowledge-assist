import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import user_manage
from app.api.admin import data_manage
from app.api.admin import chat_manage
from app.api.admin import vectordb_manage
from app.api.admin import admin_auth
from app.api.user import chat_manage as user_chat_manage
from app.api.user import data_manage as user_data_manage
from app.api.user import vectordb_manage as user_vectordb_manage
from app.api.user import user_manage as user_user_manage
from app.api.user import user_auth

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:3000",
		"http://localhost:3001",
		"http://127.0.0.1:3000",
		"http://127.0.0.1:3001",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Admin endpoint
app.include_router(user_manage.router)
app.include_router(data_manage.router)
app.include_router(chat_manage.router)
app.include_router(vectordb_manage.router)
app.include_router(admin_auth.router)

# User endpoint
app.include_router(user_chat_manage.router)
app.include_router(user_data_manage.router)
app.include_router(user_vectordb_manage.router)
app.include_router(user_user_manage.router)
app.include_router(user_auth.router)
