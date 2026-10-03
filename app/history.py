import os, json, time
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = ROOT / "static" / "history.json"

def _ensure_file():
    if not HISTORY_FILE.exists():
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def get_history() -> List[Dict]:
    _ensure_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_comic_to_history(comic_data: Dict) -> Dict:
    _ensure_file()
    history = get_history()
    
    # Ensure unique ID and timestamp
    comic_id = comic_data.get("id") or f"comic_{int(time.time() * 1000)}"
    comic_data["id"] = comic_id
    if "created_at" not in comic_data:
        comic_data["created_at"] = time.strftime("%b %d, %Y • %I:%M %p")

    # Add to beginning of history list (newest first)
    # Check if already exists by id
    history = [c for c in history if c.get("id") != comic_id]
    history.insert(0, comic_data)

    # Save to disk
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return comic_data

def get_comic_by_id(comic_id: str) -> Optional[Dict]:
    history = get_history()
    for comic in history:
        if comic.get("id") == comic_id:
            return comic
    return None

def delete_comic_from_history(comic_id: str) -> bool:
    _ensure_file()
    history = get_history()
    new_history = [c for c in history if c.get("id") != comic_id]
    
    if len(new_history) != len(history):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(new_history, f, indent=2, ensure_ascii=False)
        return True
    return False

def clear_all_history() -> bool:
    _ensure_file()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    return True
