import re

def build_comic_layout(image_paths: list, full_story: str, outline: list) -> list:
    """
    Organizes the generated images, panel outlines, and detailed story into a structured layout.
    """
    # Parse story segments if available
    story_sections = {}
    if full_story:
        # Split by panel markers like **Panel 1: or Panel 1:
        parts = re.split(r'\*\*Panel\s+(\d+)[^:]*:\s*([^\n*]+)\*\*', full_story, flags=re.IGNORECASE)
        if len(parts) > 1:
            i = 1
            while i < len(parts) - 1:
                p_num = int(parts[i])
                p_title = parts[i+1].strip()
                p_body = parts[i+2].strip() if i+2 < len(parts) else ""
                story_sections[p_num] = {"title": p_title, "body": p_body}
                i += 3

    layout = []
    for idx, (img_path, panel_info) in enumerate(zip(image_paths, outline), start=1):
        panel_num = panel_info.get("panel", idx)
        title = panel_info.get("title", f"Panel {panel_num}")
        scene_desc = panel_info.get("scene_description", "")
        img_prompt = panel_info.get("image_prompt", "")

        # Extract caption and narration if present in story
        story_data = story_sections.get(panel_num, {})
        body = story_data.get("body", "")

        caption_match = re.search(r'\*\*CAPTION:\*\*\s*([^\n]+)', body, re.IGNORECASE)
        narration_match = re.search(r'\*\*NARRATION:\*\*\s*([^\n]+)', body, re.IGNORECASE)
        dialogue_match = re.search(r'\*\*DIALOGUE:\*\*\s*([^\n]+)', body, re.IGNORECASE)

        caption = caption_match.group(1).strip() if caption_match else f"Whispers carried on the wind, magic stirring in the air."
        narration = narration_match.group(1).strip() if narration_match else f"{scene_desc}"
        if dialogue_match:
            narration += f" {dialogue_match.group(1).strip()}"

        full_text = f"**CAPTION:** {caption}\n**NARRATION:** {narration}\n**IMAGE PROMPT:** {img_prompt}"

        layout.append({
            "panel": panel_num,
            "title": title,
            "image_path": img_path,
            "scene_description": scene_desc,
            "caption": caption,
            "narration": narration,
            "image_prompt": img_prompt,
            "text": full_text
        })

    return layout
