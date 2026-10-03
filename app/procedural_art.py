import math
from PIL import Image, ImageDraw

def draw_comic_panel(prompt: str, filename: str, file_path) -> str:
    width, height = 768, 512
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    p_lower = prompt.lower()

    if "forest" in p_lower:
        top_c, bot_c, accent, hero_c = (15, 28, 45), (18, 62, 38), (90, 220, 130), (230, 95, 30)
    elif "space" in p_lower:
        top_c, bot_c, accent, hero_c = (6, 6, 22), (35, 12, 58), (190, 85, 255), (56, 189, 248)
    elif "city" in p_lower:
        top_c, bot_c, accent, hero_c = (18, 22, 42), (55, 32, 28), (255, 190, 45), (245, 50, 90)
    else:
        top_c, bot_c, accent, hero_c = (20, 32, 55), (42, 58, 82), (56, 189, 248), (240, 120, 40)

    # Gradient Sky
    for y in range(height):
        ratio = y / height
        draw.line([(0, y), (width, y)], fill=(
            int(top_c[0] * (1 - ratio) + bot_c[0] * ratio),
            int(top_c[1] * (1 - ratio) + bot_c[1] * ratio),
            int(top_c[2] * (1 - ratio) + bot_c[2] * ratio)
        ))

    # Glow
    cx, cy = int(width * 0.72), int(height * 0.28)
    for rad in range(130, 0, -12):
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=accent)

    # Terrain
    seed_val = abs(hash(prompt)) % 100
    points = [(0, height)]
    for x in range(0, width + 50, 40):
        y_val = height * 0.52 + math.sin(x * 0.012 + seed_val) * 45
        points.append((x, y_val))
    points.append((width, height))
    draw.polygon(points, fill=(int(bot_c[0] * 0.65), int(bot_c[1] * 0.65), int(bot_c[2] * 0.65)))

    # Silhouettes
    for tx in [70, 160, 260, 520, 640, 710]:
        th = 130 + (abs(hash(f"{tx}{prompt}")) % 90)
        ty = int(height * 0.72)
        draw.polygon([(tx, ty - th), (tx - 38, ty), (tx + 38, ty)], fill=(10, 15, 24))

    # Foreground
    fg_points = [(0, height)]
    for x in range(0, width + 30, 30):
        y_val = height * 0.70 + math.sin(x * 0.028 + seed_val * 2) * 20
        fg_points.append((x, y_val))
    fg_points.append((width, height))
    draw.polygon(fg_points, fill=(8, 12, 18))

    # Character Figure
    hx, hy = int(width * 0.38), int(height * 0.66)
    for ar in range(45, 0, -8):
        draw.ellipse([hx - ar, hy - ar, hx + ar, hy + ar], fill=(255, 215, 120))

    if "fox" in p_lower:
        draw.polygon([(hx - 28, hy + 25), (hx + 28, hy + 25), (hx + 35, hy - 5), (hx - 35, hy - 5)], fill=hero_c)
        draw.ellipse([hx - 22, hy - 32, hx + 22, hy - 2], fill=hero_c)
        draw.polygon([(hx - 18, hy - 30), (hx - 10, hy - 48), (hx - 2, hy - 30)], fill=(40, 20, 10))
        draw.polygon([(hx + 2, hy - 30), (hx + 10, hy - 48), (hx + 18, hy - 30)], fill=(40, 20, 10))
        draw.polygon([(hx + 25, hy + 10), (hx + 75, hy - 8), (hx + 65, hy + 35), (hx + 25, hy + 25)], fill=(255, 140, 50))
    else:
        draw.ellipse([hx - 14, hy - 45, hx + 14, hy - 18], fill=hero_c)
        draw.polygon([(hx - 22, hy - 15), (hx + 22, hy - 15), (hx + 16, hy + 35), (hx - 16, hy + 35)], fill=(30, 40, 60))

    # Borders
    draw.rectangle([10, 10, width - 10, height - 10], outline=(255, 255, 255), width=4)
    draw.rectangle([14, 14, width - 14, height - 14], outline=(0, 0, 0), width=2)
    draw.rectangle([22, 22, 210, 56], fill=(220, 38, 38))
    draw.rectangle([22, 22, 210, 56], outline=(255, 255, 255), width=2)
    draw.text((32, 29), "COMICCRAFT AI", fill=(255, 255, 255))

    img.save(file_path, "PNG")
    return f"/static/panels/{filename}"
