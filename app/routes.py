import os, traceback, time
from pathlib import Path
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional

from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf
from .history import get_history, save_comic_to_history, get_comic_by_id, delete_comic_from_history, clear_all_history

ROOT = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=ROOT / "templates")

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str
    character_name: Optional[str] = "Hero"
    setting: Optional[str] = "Forest"
    tone: Optional[str] = "Dramatic"
    style: Optional[str] = "Realistic"
    panel_count: Optional[int] = Field(default=3, ge=1, le=8)

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": get_history()
    })

@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(""),
    setting: str = Form("forest"),
    tone: str = Form("dramatic"),
    style: str = Form("comic book"),
    panel_count: int = Form(3)
):
    try:
        char_name = character_name.strip() or "Hero"
        panel_count = max(1, min(int(panel_count), 8))

        full_prompt = (
            f"{prompt.strip()}\n"
            f"The main character is {char_name}.\n"
            f"The setting is {setting}.\n"
            f"The tone is {tone}. The art style is {style}."
        )

        # Step 1: Generate distinct panel outlines
        outline = generate_outline(full_prompt, panel_count=panel_count)

        # Step 2: Generate unique story narration & dialogue
        full_story = generate_story(outline)

        # Step 3: Generate panel images sequentially to avoid Hugging Face concurrency throttling
        images = []
        for i, panel in enumerate(outline, 1):
            img_prompt = panel.get("image_prompt", f"{char_name} in {setting}, {style} style")
            print(f"Generating Hugging Face image for Panel {i}/{len(outline)}: {img_prompt[:60]}...")
            img_path = generate_image(img_prompt)
            images.append(img_path)
            # Short pause to prevent API rate-limit collision
            if i < len(outline):
                time.sleep(1.0)

        # Step 4: Build Comic Layout
        layout = build_comic_layout(images, full_story, outline)

        # Step 5: Export to PDF
        title = f"Comic - {char_name}"
        pdf_path = save_pdf(layout, title)

        # Step 6: Save to History automatically
        comic_id = f"comic_{int(time.time() * 1000)}"
        save_comic_to_history({
            "id": comic_id,
            "title": title,
            "prompt": prompt,
            "character_name": char_name,
            "setting": setting,
            "tone": tone,
            "style": style,
            "panel_count": len(layout),
            "cover_image": layout[0].get("image_path") if layout else "",
            "pdf_path": pdf_path,
            "layout": layout
        })

        return templates.TemplateResponse("comic_preview.html", {
            "request": request,
            "comic_id": comic_id,
            "layout": layout,
            "pdf_path": pdf_path,
            "title": title,
            "panel_count": len(layout)
        })
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comic/{comic_id}", response_class=HTMLResponse)
async def view_saved_comic(request: Request, comic_id: str):
    comic = get_comic_by_id(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found in history")
    
    return templates.TemplateResponse("comic_preview.html", {
        "request": request,
        "comic_id": comic.get("id"),
        "layout": comic.get("layout", []),
        "pdf_path": comic.get("pdf_path", ""),
        "title": comic.get("title", "Saved Comic"),
        "panel_count": comic.get("panel_count", len(comic.get("layout", [])))
    })

# API Routes for History
@router.get("/api/history")
async def api_get_history():
    return {"history": get_history()}

@router.delete("/api/history/{comic_id}")
async def api_delete_comic(comic_id: str):
    success = delete_comic_from_history(comic_id)
    return {"success": success}

@router.delete("/api/history/clear/all")
async def api_clear_history():
    clear_all_history()
    return {"success": True}

@router.post("/generate-comic/json")
async def generate_comic_json(req: PromptRequest):
    try:
        char_name = (req.character_name or "Hero").strip()
        panel_count = max(1, min(int(req.panel_count or 3), 8))
        full_prompt = (
            f"{req.prompt.strip()}\n"
            f"The main character is {char_name}.\n"
            f"The setting is {req.setting}.\n"
            f"The tone is {req.tone}. The art style is {req.style}."
        )

        outline = generate_outline(full_prompt, panel_count=panel_count)
        full_story = generate_story(outline)
        
        images = []
        for panel in outline:
            images.append(generate_image(panel.get("image_prompt", "")))
            time.sleep(1.0)

        layout = build_comic_layout(images, full_story, outline)
        title = f"Comic - {char_name}"
        pdf_path = save_pdf(layout, title)

        comic_id = f"comic_{int(time.time() * 1000)}"
        save_comic_to_history({
            "id": comic_id,
            "title": title,
            "prompt": req.prompt,
            "character_name": char_name,
            "setting": req.setting,
            "tone": req.tone,
            "style": req.style,
            "panel_count": len(layout),
            "cover_image": layout[0].get("image_path") if layout else "",
            "pdf_path": pdf_path,
            "layout": layout
        })

        return {
            "status": "success",
            "comic_id": comic_id,
            "panel_count": len(layout),
            "layout": layout,
            "pdf_path": pdf_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_path: Optional[str] = ""):
    return templates.TemplateResponse("export_success.html", {
        "request": request,
        "pdf_path": pdf_path
    })

@router.get("/test-image")
@router.post("/test-image")
async def test_image(prompt: str = "A futuristic city at sunset, sci-fi, cinematic, comic art style"):
    try:
        image_path = generate_image(prompt)
        return {"message": "Image generated successfully", "path": image_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
