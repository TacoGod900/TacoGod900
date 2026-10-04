"""Builds assets/banner.png: Armin (left) + "Henryk 16 the coder" + Annie (right).

Drop your art in as assets/armin.png and assets/annie.png (PNG or JPG, any size),
then run:  python3 assets/make_banner.py
If an art file is missing, that side is simply left blank.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
W, H = 1400, 480
BG = (255, 255, 255)
INK = (20, 20, 20)
FONT = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
FONT_FALLBACK = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"


def load_art(name: str, slot_w: int, slot_h: int):
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HERE / f"{name}.{ext}"
        if p.exists():
            img = Image.open(p).convert("RGBA")
            img.thumbnail((slot_w, slot_h), Image.LANCZOS)
            return img
    return None


def font(size: int):
    for path in (FONT, FONT_FALLBACK):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


canvas = Image.new("RGBA", (W, H), BG + (255,))
draw = ImageDraw.Draw(canvas)

slot_w, slot_h = 430, H - 20
left = load_art("armin", slot_w, slot_h)
right = load_art("annie", slot_w, slot_h)
if left:
    canvas.alpha_composite(left, (40, H - left.height))
if right:
    canvas.alpha_composite(right, (W - right.width - 40, H - right.height))

# Stacked serif title in the middle, like the original.
lines = [("Henryk", 150), ("16 the", 120), ("coder", 120)]
total_h = sum(font(s).getbbox(t)[3] for t, s in lines) + 12 * (len(lines) - 1)
y = (H - total_h) // 2
cx = W // 2
for text, size in lines:
    f = font(size)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = cx - tw // 2 - bbox[0]
    draw.text((x, y - bbox[1]), text, font=f, fill=INK)
    if text == "Henryk":
        # small four-point sparkle above the H, like the "Alim✦" mark
        sx, sy, r = x + tw + 6, y + 8, 14
        draw.polygon([(sx, sy - r), (sx + 4, sy - 4), (sx + r, sy), (sx + 4, sy + 4),
                      (sx, sy + r), (sx - 4, sy + 4), (sx - r, sy), (sx - 4, sy - 4)], fill=INK)
    y += th + 12

canvas.convert("RGB").save(HERE / "banner.png", optimize=True)
print("wrote", HERE / "banner.png", "| armin:", bool(left), "| annie:", bool(right))
