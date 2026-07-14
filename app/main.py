# app/main.py
from fastapi import FastAPI
from app.routers import chat, health

app = FastAPI(title="Student GPT Engine", version="1.0.0")
app.include_router(chat.router)
app.include_router(health.router)