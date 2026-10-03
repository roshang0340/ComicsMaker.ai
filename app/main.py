import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routes import router as comic_router

ROOT = Path(__file__).resolve().parent.parent

# Ensure static folders exist
(ROOT / "static" / "panels").mkdir(parents=True, exist_ok=True)
(ROOT / "static" / "exports").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ComicCraft — AI Comic Story Creator using Gemini Models",
    description="ComicCraft is a web-based application that uses AI to generate personalized comic book stories and illustrations based on user-provided prompts.",
    version="4.0.0"
)

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")

# Include comic routes
app.include_router(comic_router)

@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "app": "ComicCraft",
        "version": "4.0.0",
        "status": "online"
    }
