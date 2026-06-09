import math
import os
import struct
from typing import Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


Point3D = Tuple[float, float, float]
Triangle = Tuple[Point3D, Point3D, Point3D]


def _parse_ascii_stl(text: str) -> List[Triangle]:
    triangles: List[Triangle] = []
    vertices: List[Point3D] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("vertex "):
            continue
        _, x_str, y_str, z_str = line.split()
        vertices.append((float(x_str), float(y_str), float(z_str)))
        if len(vertices) == 3:
            triangles.append((vertices[0], vertices[1], vertices[2]))
            vertices = []
    return triangles


def _parse_binary_stl(data: bytes) -> List[Triangle]:
    triangles: List[Triangle] = []
    count = struct.unpack("<I", data[80:84])[0]
    offset = 84
    for _ in range(count):
        offset += 12  # skip stored normal
        vertices: List[Point3D] = []
        for _ in range(3):
            x, y, z = struct.unpack("<fff", data[offset:offset + 12])
            vertices.append((x, y, z))
            offset += 12
        triangles.append((vertices[0], vertices[1], vertices[2]))
        offset += 2  # attribute byte count
    return triangles


def load_stl(path: str) -> List[Triangle]:
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:5].lower() == b"solid" and b"facet normal" in data[:512]:
        try:
            return _parse_ascii_stl(data.decode("utf-8", errors="ignore"))
        except Exception:
            pass
    return _parse_binary_stl(data)


def rotate_point(point: Point3D, rot_z_deg: float = 0.0, rot_x_deg: float = 0.0, rot_y_deg: float = 0.0) -> Point3D:
    x, y, z = point
    if rot_z_deg:
        angle = math.radians(rot_z_deg)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        x, y = x * cos_a - y * sin_a, x * sin_a + y * cos_a
    if rot_x_deg:
        angle = math.radians(rot_x_deg)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        y, z = y * cos_a - z * sin_a, y * sin_a + z * cos_a
    if rot_y_deg:
        angle = math.radians(rot_y_deg)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        x, z = x * cos_a + z * sin_a, -x * sin_a + z * cos_a
    return (x, y, z)


def project_triangle(triangle: Triangle, *, rot_z_deg: float = 0.0, rot_x_deg: float = 0.0, rot_y_deg: float = 0.0) -> Tuple[List[Point3D], float]:
    rotated = [rotate_point(point, rot_z_deg=rot_z_deg, rot_x_deg=rot_x_deg, rot_y_deg=rot_y_deg) for point in triangle]
    depth = sum(point[2] for point in rotated) / 3.0
    return rotated, depth


def _triangle_normal(triangle: Sequence[Point3D]) -> Point3D:
    ax, ay, az = triangle[0]
    bx, by, bz = triangle[1]
    cx, cy, cz = triangle[2]
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    return (
        uy * vz - uz * vy,
        uz * vx - ux * vz,
        ux * vy - uy * vx,
    )


def render_view(draw: ImageDraw.ImageDraw, triangles: Sequence[Triangle], box: Tuple[int, int, int, int], title: str, *, rot_z_deg: float = 0.0, rot_x_deg: float = 0.0, rot_y_deg: float = 0.0) -> None:
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    transformed = [project_triangle(triangle, rot_z_deg=rot_z_deg, rot_x_deg=rot_x_deg, rot_y_deg=rot_y_deg) for triangle in triangles]

    min_x = min(point[0] for rotated, _ in transformed for point in rotated)
    max_x = max(point[0] for rotated, _ in transformed for point in rotated)
    min_y = min(point[1] for rotated, _ in transformed for point in rotated)
    max_y = max(point[1] for rotated, _ in transformed for point in rotated)

    scale = min((width - 50) / max(max_x - min_x, 1e-6), (height - 80) / max(max_y - min_y, 1e-6))
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    screen_cx = x0 + width / 2.0
    screen_cy = y0 + height / 2.0 + 10

    font = ImageFont.load_default()
    draw.rectangle(box, fill=(250, 250, 250), outline=(210, 210, 210), width=1)
    draw.text((x0 + 12, y0 + 10), title, fill=(20, 20, 20), font=font)

    for rotated, depth in sorted(transformed, key=lambda item: item[1]):
        normal = _triangle_normal(rotated)
        normal_length = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) or 1.0
        light = abs(normal[2]) / normal_length
        shade = int(130 + 90 * light)
        points_2d = []
        for px, py, _ in rotated:
            sx = screen_cx + (px - center_x) * scale
            sy = screen_cy - (py - center_y) * scale
            points_2d.append((sx, sy))
        draw.polygon(points_2d, fill=(shade, shade, shade), outline=(65, 65, 65))


def render_stl_views(stl_path: str, output_path: str) -> None:
    triangles = load_stl(stl_path)
    image = Image.new("RGB", (1800, 1400), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    render_view(draw, triangles, (40, 40, 860, 680), "Isometric", rot_z_deg=45.0, rot_x_deg=35.264)
    render_view(draw, triangles, (940, 40, 1760, 680), "Front", rot_x_deg=90.0)
    render_view(draw, triangles, (40, 720, 860, 1360), "Side", rot_y_deg=90.0, rot_x_deg=90.0)
    render_view(draw, triangles, (940, 720, 1760, 1360), "Top", rot_z_deg=0.0, rot_x_deg=0.0)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)


if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.dirname(__file__))
    stl_path = os.path.join(project_dir, "honeycomb_cell", "output", "HoneycombCell.stl")
    output_path = os.path.join(project_dir, "honeycomb_cell", "output", "HoneycombCell_views.png")
    render_stl_views(stl_path, output_path)
    print(output_path)
