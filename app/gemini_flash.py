import os, json, re, time, requests, urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

orig_request = requests.Session.request
def patched_request(self, method, url, *args, **kwargs):
    kwargs['verify'] = False
    return orig_request(self, method, url, *args, **kwargs)
requests.Session.request = patched_request

load_dotenv()

def generate_outline(user_prompt: str, panel_count: int = 3) -> list:
    """
    Generates a dynamic panel_count comic layout tailored specifically to the user's prompt.
    """
    panel_count = max(1, min(int(panel_count), 8))

    prompt = f"""You are a professional comic book creator.
Generate a strictly formatted JSON array containing exactly {panel_count} distinct comic panels for this story:

STORY: "{user_prompt}"

Requirements:
- Match the theme and setting of the story exactly.
- Each panel must show a progressive chapter with unique actions, unique character expressions, and evolving environments.
- "image_prompt" must be very descriptive, cinematic, and distinct for each panel (specifying camera angle, character actions, background details, and comic style).

Respond ONLY with this valid JSON array of {panel_count} objects without markdown:
[
  {{
    "panel": 1,
    "title": "The Preparation",
    "scene_description": "Detailed scene description matching the story.",
    "image_prompt": "Comic book art, wide angle shot of characters in the setting, vibrant colors, detailed artwork"
  }}
]"""

    raw_keys = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    keys = [x.strip() for x in raw_keys.replace("\n", ",").split(",") if x.strip()]
    output_text = ""

    for key in keys:
        for model_name in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                r = requests.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.7}
                    },
                    verify=False,
                    timeout=15
                )
                if r.ok:
                    data = r.json()
                    output_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    break
            except Exception:
                continue
        if output_text:
            break

    # Parse output JSON
    if output_text:
        cleaned = output_text
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            panel_data = json.loads(cleaned)
            if isinstance(panel_data, list) and len(panel_data) > 0:
                for idx, p in enumerate(panel_data[:panel_count], 1):
                    p["panel"] = idx
                return panel_data[:panel_count]
        except Exception:
            pass

    # Dynamic context-aware narrative generation tailored to the user's prompt
    main_idea = user_prompt.split('\n')[0].strip()
    char_match = re.search(r'main character is ([^.\n]+)', user_prompt, re.IGNORECASE)
    setting_match = re.search(r'setting is ([^.\n]+)', user_prompt, re.IGNORECASE)
    style_match = re.search(r'art style is ([^.\n]+)', user_prompt, re.IGNORECASE)

    hero = char_match.group(1).strip() if char_match else "Our protagonist"
    setting = setting_match.group(1).strip() if setting_match else "the scene"
    style = style_match.group(1).strip() if style_match else "comic book"

    # Contextual beat patterns
    story_beats = [
        (
            f"The Journey Begins",
            f"{hero} steps into {setting}, ready to face the upcoming challenge: {main_idea}.",
            f"Comic book art, wide establishing shot of {hero} in {setting}, beginning the quest for {main_idea}, detailed illustration, {style} style"
        ),
        (
            f"Into the Challenge",
            f"Hard work and dedication take over as {hero} tackles complex problems and pushes through the difficulties.",
            f"Comic book art, medium shot of {hero} working hard and strategizing in {setting}, intense focus, glowing ambient lighting, {style} style"
        ),
        (
            f"The Turning Point",
            f"A breakthrough moment occurs where all the effort and preparation begin to show clear results.",
            f"Comic book art, dynamic close up of {hero} with an inspired expression, eureka moment, vivid colors, {style} style"
        ),
        (
            f"The Climax",
            f"The ultimate test arrives—testing every bit of skill, knowledge, and courage.",
            f"Comic book art, dramatic high-stakes action scene of {hero} in {setting}, cinematic tension, expressive linework, {style} style"
        ),
        (
            f"Victory and Celebration",
            f"Success achieved! {hero} stands proud, celebrating the triumph of hard work and determination.",
            f"Comic book art, joyful victory shot of {hero} celebrating success in {setting}, golden lighting, vibrant colors, {style} style"
        ),
        (
            f"Looking Ahead",
            f"With confidence soaring, new horizons and future opportunities open up for {hero}.",
            f"Comic book art, inspiring wide shot of {hero} looking toward a bright future, beautiful scenery, {style} style"
        )
    ]

    outline = []
    for i in range(panel_count):
        if i == panel_count - 1 and panel_count > 1:
            title, desc, img_prompt = story_beats[4] # Victory beat
        else:
            title, desc, img_prompt = story_beats[i % len(story_beats)]

        outline.append({
            "panel": i + 1,
            "title": title,
            "scene_description": desc,
            "image_prompt": img_prompt
        })

    return outline
