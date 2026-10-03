import os, re, time, io
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageEnhance
import urllib3
import requests
import httpx

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global SSL patch for proxy environments
orig_request = requests.Session.request
def patched_request(self, method, url, *args, **kwargs):
    kwargs['verify'] = False
    return orig_request(self, method, url, *args, **kwargs)
requests.Session.request = patched_request

orig_httpx_init = httpx.Client.__init__
def patched_httpx_init(self, *args, **kwargs):
    kwargs['verify'] = False
    orig_httpx_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_httpx_init

from huggingface_hub import InferenceClient

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
STATIC_PANELS = ROOT / "static" / "panels"
STATIC_PANELS.mkdir(parents=True, exist_ok=True)

# Curated high-resolution thematic scenes for auto-fallback
THEMATIC_SCENES = {
    "school": [
        "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=1024&q=80",
        "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=1024&q=80",
        "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=1024&q=80",
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1024&q=80",
        "https://images.unsplash.com/photo-1577896851231-70ef18881754?w=1024&q=80"
    ],
    "forest": [
        "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1024&q=80",
        "https://images.unsplash.com/photo-1511497584788-87676104235f?w=1024&q=80",
        "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=1024&q=80",
        "https://images.unsplash.com/photo-1476820865390-c52aeebb9891?w=1024&q=80"
    ],
    "cave": [
        "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1024&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1024&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1024&q=80"
    ],
    "space": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1024&q=80",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1024&q=80",
        "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1024&q=80"
    ],
    "city": [
        "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?w=1024&q=80",
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1024&q=80",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1024&q=80"
    ]
}

def sanitize_filename(prompt: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', prompt).strip().replace(' ', '_')
    timestamp = int(time.time() * 1000)
    return f"panel_{timestamp}_{cleaned[:25]}.png"

def _apply_comic_styling(image_bytes: bytes, file_path: Path, prompt: str):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((768, 512), Image.Resampling.LANCZOS)
    
    enhancer_color = ImageEnhance.Color(img)
    img = enhancer_color.enhance(1.25)
    enhancer_con = ImageEnhance.Contrast(img)
    img = enhancer_con.enhance(1.15)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle([6, 6, 762, 506], outline=(255, 255, 255), width=4)
    draw.rectangle([10, 10, 758, 502], outline=(0, 0, 0), width=2)
    
    draw.rectangle([18, 18, 160, 48], fill=(220, 38, 38))
    draw.rectangle([18, 18, 160, 48], outline=(255, 255, 255), width=2)
    draw.text((28, 25), "COMICCRAFT AI", fill=(255, 255, 255))
    
    img.save(file_path, "PNG")

def generate_image(prompt: str, filename: str = None) -> str:
    """
    Generates a comic illustration using Hugging Face FLUX models (Nscale & fal-ai with FLUX.1-schnell and FLUX.1-dev).
    """
    if not filename:
        filename = sanitize_filename(prompt)
    elif not filename.endswith(".png") and not filename.endswith(".jpg"):
        filename = f"{filename}.png"

    file_path = STATIC_PANELS / filename
    
    raw_tokens = os.getenv("HF_TOKEN", "") or os.getenv("HUGGINGFACE_API_KEY", "")
    tokens = [t.strip() for t in raw_tokens.replace("\n", ",").split(",") if t.strip().startswith("hf_")]

    clean_p = prompt.replace("Comic book art,", "").replace("Comic book illustration,", "").strip()
    enhanced_prompt = f"{clean_p}, comic book art style, vibrant colors, clear dynamic linework, highly detailed graphic novel illustration"

    # Multi-provider & multi-model cascade (includes both FLUX.1-schnell and FLUX.1-dev)
    configurations = [
        ("nscale", "black-forest-labs/FLUX.1-schnell"),
        ("fal-ai", "black-forest-labs/FLUX.1-dev"),
        ("fal-ai", "black-forest-labs/FLUX.1-schnell"),
        ("auto", "black-forest-labs/FLUX.1-schnell"),
        ("auto", "black-forest-labs/FLUX.1-dev")
    ]

    for token in tokens:
        for provider, model_name in configurations:
            try:
                client = InferenceClient(provider=provider, api_key=token, timeout=50)
                pil_image = client.text_to_image(
                    prompt=enhanced_prompt,
                    model=model_name
                )
                if pil_image:
                    pil_image.save(file_path, "PNG")
                    print(f"Hugging Face SUCCESS ({provider}/{model_name}) -> {filename}")
                    return f"/static/panels/{filename}"
            except Exception as e:
                # If account is depleted, try next token or fallback
                if "402" in str(e) or "depleted" in str(e).lower():
                    break
                continue

    # Secondary: Thematic Auto-Fallback (Scene-tailored high-res visual)
    p_lower = prompt.lower()
    chosen_category = "forest"
    if any(k in p_lower for k in ["school", "study", "exam", "student", "class", "library", "college"]):
        chosen_category = "school"
    elif any(k in p_lower for k in ["space", "cosmos", "star", "planet", "galaxy"]):
        chosen_category = "space"
    elif any(k in p_lower for k in ["city", "street", "building", "cyber", "urban"]):
        chosen_category = "city"
    elif any(k in p_lower for k in ["cave", "cavern", "crystal", "underground"]):
        chosen_category = "cave"

    urls = THEMATIC_SCENES.get(chosen_category, THEMATIC_SCENES["forest"])
    idx = abs(hash(prompt)) % len(urls)
    target_url = urls[idx]

    try:
        r = requests.get(target_url, verify=False, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.content) > 5000:
            _apply_comic_styling(r.content, file_path, prompt)
            print(f"Auto-Fallback Comic Scene ({chosen_category}) -> {filename}")
            return f"/static/panels/{filename}"
    except Exception as e:
        print(f"Thematic fallback error: {e}")

    # Tertiary: Procedural illustration engine
    from .procedural_art import draw_comic_panel
    return draw_comic_panel(prompt, filename, file_path)
