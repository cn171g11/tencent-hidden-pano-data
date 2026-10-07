"""Download and assemble the archived Tencent cubemap faces."""

import hashlib
import io
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
FACE_NAMES = ("front", "right", "back", "left", "up", "down")
ATTEMPTS = 3
PREVIEW_SIZE = 240


def fetch_progressive_tile(settings, scene, column, row):
    chunks = []
    for level in settings["levels"]:
        query = urllib.parse.urlencode({"from": "web", "svid": scene["id"],
                                      "level": level, "x": column, "y": row})
        with urllib.request.urlopen(settings["tile_url"] + "?" + query, timeout=settings["timeout_seconds"]) as response:
            chunks.append(response.read())
    # Tencent splits a progressive JPEG across levels, rather than returning independent images.
    return b"".join(chunks)


def load_tile(settings, scene, column, row):
    directory = ROOT / scene["slug"] / "tiles"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{column}-{row}.jpg"
    for attempt in range(ATTEMPTS):
        try:
            if target.exists():
                content = target.read_bytes()
            else:
                content = fetch_progressive_tile(settings, scene, column, row)
            image = Image.open(io.BytesIO(content))
            image.load()
            if image.size != (settings["tile_size"], settings["tile_size"]):
                raise ValueError(f"Unexpected image dimensions: {image.size}")
            target.write_bytes(content)
            return column, row, image.convert("RGB"), hashlib.sha256(content).hexdigest()
        except (OSError, ValueError, urllib.error.URLError) as error:
            LOGGER.warning("scene=%s tile=%s,%s attempt=%s error=%s", scene["slug"], column, row, attempt, error)
            if attempt == ATTEMPTS - 1:
                raise
            time.sleep(attempt + 1)


def assemble_scene(settings, scene):
    count = settings["face_tiles"]
    tile_size = settings["tile_size"]
    face_size = count * tile_size
    positions = [(column, row) for column in range(count * 4) for row in range(count)]
    faces = [Image.new("RGB", (face_size, face_size)) for _ in FACE_NAMES]
    evidence = []
    with ThreadPoolExecutor(max_workers=settings["workers"]) as executor:
        requests = executor.map(lambda position: load_tile(settings, scene, *position), positions)
        for column, row, image, digest in requests:
            faces[column // count].paste(image, ((column % count) * tile_size, row * tile_size))
            evidence.append({"x": column, "y": row, "sha256": digest})
    thumbnail_url = settings["thumb_url"] + "?" + urllib.parse.urlencode({"from": "web", "svid": scene["id"], "level": 0, "x": 0, "y": 0})
    with urllib.request.urlopen(thumbnail_url, timeout=settings["timeout_seconds"]) as response:
        thumbnail_bytes = response.read()
    (ROOT / scene["slug"] / "original-thumb.jpg").write_bytes(thumbnail_bytes)
    thumbnail = Image.open(io.BytesIO(thumbnail_bytes)).convert("RGB")
    if thumbnail.width != thumbnail.height * len(FACE_NAMES):
        raise ValueError("Expected a six-face thumbnail strip")
    for index in (4, 5):
        start = index * thumbnail.height
        faces[index] = thumbnail.crop((start, 0, start + thumbnail.height, thumbnail.height)).resize((face_size, face_size))
    preview = Image.new("RGB", (PREVIEW_SIZE * len(faces), PREVIEW_SIZE + 30), "white")
    painter = ImageDraw.Draw(preview)
    for index, (name, face) in enumerate(zip(FACE_NAMES, faces)):
        face.save(ROOT / scene["slug"] / f"{name}.jpg", quality=95)
        preview.paste(face.resize((PREVIEW_SIZE, PREVIEW_SIZE)), (index * PREVIEW_SIZE, 30))
        painter.text((index * PREVIEW_SIZE, 5), name, fill="black")
    preview.save(ROOT / scene["slug"] / "preview.jpg")
    LOGGER.info("assembled=%s tiles=%s face_size=%s", scene["slug"], len(evidence), face_size)
    return dict(scene, face_size=face_size, pole_source_size=thumbnail.height, tiles=evidence)


def main():
    settings = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    completed = []
    for scene in settings["scenes"]:
        completed.append(assemble_scene(settings, scene))
        (ROOT / "manifest.json").write_text(json.dumps(completed, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
