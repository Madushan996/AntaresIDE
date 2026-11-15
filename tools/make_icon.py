"""Draws assets/icon.png and assets/icon.ico: an orange star glowing on navy."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent.parent


def icon(size=256):
    s = size * 4  # draw large, then shrink for smooth edges
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = s // 5
    d.rounded_rectangle((0, 0, s - 1, s - 1), radius=r, fill=(18, 26, 51, 255))
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    c = s // 2
    for k, (rad, col) in enumerate([(0.42, (194, 65, 12, 90)), (0.30, (242, 106, 46, 170)), (0.19, (255, 179, 107, 235)), (0.09, (255, 243, 224, 255))]):
        rr = int(s * rad)
        g.ellipse((c - rr, c - rr, c + rr, c + rr), fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(s // 28))
    img.alpha_composite(glow)
    # keep the rounded corners
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=r, fill=255)
    img.putalpha(Image.composite(img.getchannel("A"), Image.new("L", (s, s), 0), mask))
    return img.resize((size, size), Image.LANCZOS)


big = icon(256)
(HERE / "assets").mkdir(exist_ok=True)
big.save(HERE / "assets" / "icon.png")
big.save(HERE / "assets" / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon written")
