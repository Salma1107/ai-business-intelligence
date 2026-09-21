import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import CORS_ALLOWED_ORIGINS
from backend.db.connection import ensure_users_table
from backend.routers import auth, chat, agents, data

app = FastAPI(
    title="AI for Business Intelligence — API",
    description="Backend exposant les agents IA (SQL, Analytics, Forecast, Report) "
                 "via une interface de chat conversationnel.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    ensure_users_table()


app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(data.router)


@app.get("/")
def root():
    return {"status": "API AI for Business Intelligence — en ligne"}
