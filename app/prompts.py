from .models import Story

STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "logline": {"type": "string"},
        "genre": {"type": "string"},
        "tone": {"type": "string"},
        "characters": {
            "type": "array",
            "items": {"type": "object", "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "role": {"type": "string"},
                "visual_identity": {"type": "string"}
            }, "required": ["name", "description", "role", "visual_identity"]}
        },
        "panels": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["title", "logline", "genre", "tone", "characters", "panels"]
}

STORYBOARD_SCHEMA = {
    "type": "object",
    "properties": {
        "panels": {
            "type": "array",
            "items": {"type": "object", "properties": {
                "panel_number": {"type": "integer"},
                "scene": {"type": "string"},
                "camera": {"type": "string"},
                "composition": {"type": "string"},
                "characters": {"type": "array", "items": {"type": "string"}},
                "caption": {"type": "string"},
                "narration": {"type": "string"},
                "dialogue": {
                    "type": "array",
                    "items": {"type": "object", "properties": {
                        "character": {"type": "string"},
                        "text": {"type": "string"},
                        "bubble": {"type": "string"}
                    }, "required": ["character", "text", "bubble"]}
                },
                "image_prompt": {"type": "string"}
            }, "required": ["panel_number", "scene", "camera", "composition",
                            "characters", "caption", "narration", "dialogue", "image_prompt"]}
        }
    },
    "required": ["panels"]
}

def story_prompt(premise, language, genre, tone, count, has_reference, character_name=None, setting=None):
    ref = " A character reference image is attached; preserve the subject's identity consistently." if has_reference else ""
    char = f" Main character name: {character_name}." if character_name else ""
    place = f" Setting: {setting}." if setting else ""
    return f"""You are the lead writer at a premium graphic-novel studio called ComicCraft.
Create an original {count}-panel comic from this premise: {premise}
Language: {language}. Genre: {genre}. Tone: {tone}.{char}{place}{ref}
Requirements:
- Panel 1 must hook the reader; middle panels escalate; final panel provides a satisfying payoff.
- Create 2-4 memorable characters with distinct roles and consistent visual identities.
- Every panel advances the story; no filler.
- Dialogue is concise enough for speech bubbles.
- Return ONLY the JSON schema requested."""

def refine_prompt(story: Story, instruction: str, language: str):
    return f"""You are a senior comic editor. Revise the approved comic while preserving continuity.
Language: {language}
Requested change: {instruction}
Current story JSON: {story.model_dump_json()}
Keep exactly {len(story.panels)} panels. Do not silently remove established characters.
Return only the same JSON schema."""

def storyboard_prompt(story: Story, style: str, palette: str, language: str):
    return f"""You are ComicCraft's storyboard director.
Turn this approved story into a production-ready panel storyboard.
Language: {language}. Art style: {style}. Palette: {palette}.
Story: {story.model_dump_json()}
For every panel provide scene, camera, composition, characters, caption, narration,
concise dialogue, and a detailed image prompt. Preserve character identity and continuity.
Return only JSON."""

def image_prompt(panel: dict, story: Story, style: str, palette: str):
    chars = "\n".join(f"- {c.name}: {c.visual_identity}. {c.description}" for c in story.characters)
    dialogue = "\n".join(
        f'{d.get("character","")}: "{d.get("text","")}" [{d.get("bubble","speech")}]'
        for d in panel.get("dialogue", [])
    )
    return f"""Create ONE finished comic-book panel for ComicCraft.
STYLE: {style}
PALETTE: {palette}
SCENE: {panel.get("scene","")}
CAMERA: {panel.get("camera","")}
COMPOSITION: {panel.get("composition","")}
CHARACTERS:
{chars}
DIALOGUE:
{dialogue or "No dialogue"}
DIRECTOR IMAGE PROMPT: {panel.get("image_prompt","")}
Requirements: premium graphic-novel finish, expressive faces and poses, consistent character design,
cinematic lighting, polished linework, coherent background, readable speech bubbles, no watermark,
no logo, no extra characters, no unrelated text. Preserve the specified dialogue faithfully."""
