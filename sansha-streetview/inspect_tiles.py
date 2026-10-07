"""Create a small contact sheet for checking Tencent's tile coordinates."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SIZE = 180
sheet = Image.new("RGB", (SIZE * 8, (SIZE + 24) * 2), "white")
labels = ImageDraw.Draw(sheet)
for column in range(8):
    for row in range(2):
        filename = ROOT / "city-hall" / "tiles" / f"{column}-{row}.jpg"
        if filename.exists():
            with Image.open(filename) as image:
                sheet.paste(image.resize((SIZE, SIZE)), (column * SIZE, row * (SIZE + 24) + 24))
            labels.text((column * SIZE, row * (SIZE + 24)), f"x={column}, y={row}", fill="black")
sheet.save(ROOT / "tile-contact.jpg")
