import os, io, re, time
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STATIC_EXPORTS = ROOT / "static" / "exports"
STATIC_EXPORTS.mkdir(parents=True, exist_ok=True)

def _wrap_text(pdf, text, x, y, max_width_chars=78, leading=14, font="Helvetica", size=9):
    pdf.setFont(font, size)
    for paragraph in str(text or "").split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if len(candidate) > max_width_chars and line:
                pdf.drawString(x, y, line)
                y -= leading
                line = word
            else:
                line = candidate
        if line:
            pdf.drawString(x, y, line)
            y -= leading
        y -= 2
    return y

def save_pdf(layout: list, title: str = "ComicCraft Story") -> str:
    """
    Compiles the comic panels into a beautifully formatted, professional comic PDF file.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip().replace(' ', '_') or "Comic"
    filename = f"comic_{clean_title}_{timestamp}.pdf"
    file_path = STATIC_EXPORTS / filename

    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    W, H = A4
    pdf.setTitle(title)

    for panel in layout:
        p_num = panel.get("panel", 1)
        p_title = panel.get("title", f"Panel {p_num}")
        img_path = panel.get("image_path", "")
        desc = panel.get("scene_description", "")
        caption = panel.get("caption", "")
        narration = panel.get("narration", "")

        # 1. Page Background (Clean soft slate)
        pdf.setFillColorRGB(0.97, 0.98, 0.99)
        pdf.rect(0, 0, W, H, fill=1, stroke=0)

        # 2. Top Banner (Vibrant comic blue with shadow)
        pdf.setFillColorRGB(0.08, 0.35, 0.75)
        pdf.rect(0, H - 46, W, 46, fill=1, stroke=0)
        
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(32, H - 30, f"Panel {p_num}: {p_title}")

        # 3. Comic Artwork Placement
        disk_img_path = None
        if img_path.startswith("/static/"):
            disk_img_path = ROOT / img_path.lstrip("/")
        elif os.path.exists(img_path):
            disk_img_path = Path(img_path)

        # Calculate optimal image frame
        max_img_w = W - 64
        max_img_h = H * 0.50 # 50% of page height
        img_y = H - 54

        if disk_img_path and disk_img_path.exists():
            try:
                pil_img = Image.open(str(disk_img_path)).convert("RGB")
                iw, ih = pil_img.size
                scale = min(max_img_w / iw, max_img_h / ih)
                dw, dh = iw * scale, ih * scale
                x = (W - dw) / 2
                img_y = H - 58 - dh

                # Comic image double border
                pdf.setFillColorRGB(0, 0, 0)
                pdf.rect(x - 3, img_y - 3, dw + 6, dh + 6, fill=1, stroke=0)
                pdf.setStrokeColorRGB(0.9, 0.9, 0.9)
                pdf.setLineWidth(1)
                pdf.rect(x - 1, img_y - 1, dw + 2, dh + 2, fill=0, stroke=1)
                
                pdf.drawImage(ImageReader(pil_img), x, img_y, dw, dh, preserveAspectRatio=True, mask="auto")
            except Exception as e:
                pdf.drawString(32, H - 100, f"[Image rendering error: {e}]")
                img_y = H - 200

        # 4. Narrative Card (Positioned directly below the artwork)
        card_margin_x = 30
        card_w = W - (card_margin_x * 2)
        card_top = img_y - 16
        card_h = max(card_top - 36, 160)

        # White content card with rounded border
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setStrokeColorRGB(0.82, 0.86, 0.92)
        pdf.setLineWidth(1.5)
        pdf.roundRect(card_margin_x, 36, card_w, card_h, 8, fill=1, stroke=1)

        # Text stream inside the card
        text_x = card_margin_x + 18
        text_y = card_top - 20

        # Scene description (italics)
        if desc:
            pdf.setFillColorRGB(0.4, 0.45, 0.52)
            text_y = _wrap_text(pdf, f"Scene: {desc}", text_x, text_y, 76, 13, "Helvetica-Oblique", 9) - 8

        # Decorative separator
        pdf.setStrokeColorRGB(0.9, 0.92, 0.95)
        pdf.setLineWidth(1)
        pdf.line(text_x, text_y + 4, text_x + card_w - 36, text_y + 4)
        text_y -= 8

        # Caption
        if caption:
            pdf.setFillColorRGB(0.08, 0.35, 0.75)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(text_x, text_y, "CAPTION:")
            pdf.setFillColorRGB(0.18, 0.22, 0.28)
            text_y = _wrap_text(pdf, caption, text_x + 72, text_y, 64, 13, "Helvetica", 9) - 6

        # Narration & Dialogue
        if narration:
            pdf.setFillColorRGB(0.08, 0.35, 0.75)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(text_x, text_y, "NARRATION:")
            pdf.setFillColorRGB(0.18, 0.22, 0.28)
            text_y = _wrap_text(pdf, narration, text_x + 84, text_y, 62, 13, "Helvetica", 9) - 6

        # Footer page indicator
        pdf.setFillColorRGB(0.55, 0.6, 0.68)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(card_margin_x + 10, 20, f"ComicCraft Studio • Page {p_num} of {len(layout)}")

        pdf.showPage()

    pdf.save()
    return f"/static/exports/{filename}"
