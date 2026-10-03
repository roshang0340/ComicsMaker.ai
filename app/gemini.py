import base64, json, os, time
from typing import Optional, Any
import requests
from dotenv import load_dotenv

load_dotenv()
API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.8-flash")
TEXT_FALLBACK = os.getenv("GEMINI_TEXT_FALLBACK_MODEL", "gemini-3.5-flash-lite")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
PREMIUM_IMAGE_MODEL = os.getenv("GEMINI_PREMIUM_IMAGE_MODEL", "gemini-3-pro-image")
IMAGE_FALLBACK = os.getenv("GEMINI_IMAGE_FALLBACK_MODEL", "gemini-2.5-flash-image")
_key_index = 0

def _keys():
    raw = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    keys = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
    if not keys:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return keys

def _post(url, payload, timeout=180):
    global _key_index
    keys = _keys()
    last = None
    for offset in range(len(keys)):
        key = keys[(_key_index + offset) % len(keys)]
        try:
            r = requests.post(url, headers={"Content-Type":"application/json","x-goog-api-key":key},
                              json=payload, timeout=timeout)
            if r.status_code in (429, 503) and len(keys) > 1:
                _key_index = (_key_index + 1) % len(keys)
                continue
            if not r.ok:
                raise RuntimeError(f"Gemini API {r.status_code}: {r.text[:1000]}")
            return r.json()
        except Exception as e:
            last = e
            if offset < len(keys)-1:
                _key_index = (_key_index + 1) % len(keys)
                time.sleep(.4)
    raise last or RuntimeError("Gemini request failed.")

def _text(data):
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def generate_json(prompt: str, schema: dict):
    models = [TEXT_MODEL, TEXT_FALLBACK]
    last = None
    for model in dict.fromkeys(models):
        payload = {
            "contents":[{"role":"user","parts":[{"text":prompt}]}],
            "generationConfig":{
                "temperature":0.7,
                "responseMimeType":"application/json",
                "responseJsonSchema":schema
            }
        }
        try:
            return json.loads(_text(_post(f"{API_ROOT}/models/{model}:generateContent", payload)))
        except Exception as e:
            last=e
            time.sleep(.3)
    raise RuntimeError(f"Structured Gemini generation failed: {last}")

def _interaction_image(data):
    if data.get("output_image", {}).get("data"):
        return data["output_image"]["data"]
    for step in data.get("steps", []):
        for block in step.get("content", []):
            if block.get("type") == "image" and block.get("data"):
                return block["data"]
    return None

def generate_image(prompt: str, reference_image: Optional[str]=None,
                   aspect_ratio="4:5", premium=False, image_size="1K"):
    models = [PREMIUM_IMAGE_MODEL] if premium else [IMAGE_MODEL]
    models += [IMAGE_MODEL, IMAGE_FALLBACK]
    for model in dict.fromkeys(models):
        try:
            inputs=[{"type":"text","text":prompt}]
            if reference_image:
                raw=reference_image.split(",",1)[-1]
                mime="image/png"
                if reference_image.startswith("data:image/jpeg"): mime="image/jpeg"
                elif reference_image.startswith("data:image/webp"): mime="image/webp"
                inputs.append({"type":"image","mime_type":mime,"data":raw})
            payload={
                "model":model,
                "input":inputs,
                "response_format":{
                    "type":"image","aspect_ratio":aspect_ratio,"image_size":image_size
                }
            }
            data=_post(f"{API_ROOT}/interactions", payload, timeout=300)
            img=_interaction_image(data)
            if img: return img
        except Exception:
            continue
    raise RuntimeError("Gemini image generation failed. No fallback artwork is returned as a fake success.")

def model_status():
    return {
        "provider":"Google Gemini API",
        "text_model":TEXT_MODEL,
        "image_model":IMAGE_MODEL,
        "premium_image_model":PREMIUM_IMAGE_MODEL,
        "fallback_image_model":IMAGE_FALLBACK,
        "keys_configured":len(_keys())
    }
