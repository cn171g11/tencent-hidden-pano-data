"""Export equirectangular panoramas and a self-contained offline viewer."""
import base64
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
WIDTH = 4096
HEIGHT = WIDTH // 2
FACE_NAMES = ("front", "right", "back", "left", "up", "down")


def project_panorama(scene):
    faces = [np.asarray(Image.open(ROOT / scene["slug"] / f"{name}.jpg")) for name in FACE_NAMES]
    longitude = (np.arange(WIDTH) + 0.5) / WIDTH * np.pi * 2 - np.pi
    panorama = np.empty((HEIGHT, WIDTH, 3), dtype=np.uint8)
    for row in range(HEIGHT):
        latitude = np.pi / 2 - (row + 0.5) / HEIGHT * np.pi
        horizontal = np.cos(latitude)
        direction_x = horizontal * np.sin(longitude)
        direction_y = np.full(WIDTH, np.sin(latitude))
        direction_z = horizontal * np.cos(longitude)
        axes = np.argmax(np.stack([np.abs(direction_z), np.abs(direction_x), np.abs(direction_y)]), axis=0)
        selectors = [(axes == 0) & (direction_z >= 0), (axes == 1) & (direction_x >= 0),
                     (axes == 0) & (direction_z < 0), (axes == 1) & (direction_x < 0),
                     (axes == 2) & (direction_y >= 0), (axes == 2) & (direction_y < 0)]
        coordinates = [(direction_x, -direction_y, direction_z), (-direction_z, -direction_y, direction_x),
                       (-direction_x, -direction_y, -direction_z), (direction_z, -direction_y, -direction_x),
                       (direction_x, direction_z, direction_y), (direction_x, -direction_z, -direction_y)]
        for face, selected, (horizontal_axis, vertical_axis, divisor) in zip(faces, selectors, coordinates):
            if not np.any(selected):
                continue
            columns = np.clip(((horizontal_axis[selected] / divisor[selected] + 1) * 0.5 * (face.shape[1] - 1)).astype(int), 0, face.shape[1] - 1)
            rows = np.clip(((vertical_axis[selected] / divisor[selected] + 1) * 0.5 * (face.shape[0] - 1)).astype(int), 0, face.shape[0] - 1)
            panorama[row, selected] = face[rows, columns]
    target = ROOT / scene["slug"] / "panorama-4096.jpg"
    Image.fromarray(panorama).save(target, quality=94)
    return dict(scene, image="data:image/jpeg;base64," + base64.b64encode(target.read_bytes()).decode("ascii"))


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    scenes = [project_panorama(scene) for scene in manifest]
    template = (ROOT / "viewer-template.html").read_text(encoding="utf-8")
    (ROOT / "三沙街景-离线查看.html").write_text(template.replace("__SCENES__", json.dumps(scenes, ensure_ascii=False)), encoding="utf-8")


if __name__ == "__main__":
    main()
