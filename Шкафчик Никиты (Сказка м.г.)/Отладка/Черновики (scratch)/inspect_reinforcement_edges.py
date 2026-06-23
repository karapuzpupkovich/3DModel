import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

import math

from honeycomb_cell.builder import _build_outer_vertices, create_honeycomb_cell_shape, get_face_angle_and_dist
from honeycomb_cell.config import DEFAULT_CONFIG


cfg = DEFAULT_CONFIG
shape, report = create_honeycomb_cell_shape(cfg, enable_perforation=False, log=print)
print(f"valid={report.valid} solids={len(shape.Solids)} faces={len(shape.Faces)}")
vertices = _build_outer_vertices(cfg)

for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    alpha_rad = math.radians(alpha_deg)
    tangent = FreeCAD.Vector(-math.sin(alpha_rad), math.cos(alpha_rad), 0)
    normal = FreeCAD.Vector(math.cos(alpha_rad), math.sin(alpha_rad), 0)
    face_mid = (vertices[face_index] + vertices[(face_index + 1) % 6]) * 0.5

    print(f"face {face_index} reinforcement-zone longitudinal edges:")
    candidates = []
    for edge in shape.Edges:
        p1 = edge.Vertex1.Point
        p2 = edge.Vertex2.Point
        if not (
            (abs(p1.z) < 0.01 and abs(p2.z - cfg.cell_len) < 0.01)
            or (abs(p2.z) < 0.01 and abs(p1.z - cfg.cell_len) < 0.01)
        ):
            continue
        if FreeCAD.Vector(p1.x - p2.x, p1.y - p2.y, 0).Length > 0.01:
            continue

        midpoint = (p1 + p2) * 0.5
        rel = midpoint - FreeCAD.Vector(face_mid.x, face_mid.y, midpoint.z)
        u = rel.dot(tangent)
        v = rel.dot(normal)
        if cfg.reinforcement_v2 - 0.6 <= v <= 0.6 and abs(u) <= cfg.reinforcement_w1 / 2.0 + 2.0:
            curve = getattr(edge, "Curve", None)
            curve_name = type(curve).__name__ if curve is not None else "None"
            candidates.append((round(u, 3), round(v, 3), round(edge.Length, 3), curve_name))

    for item in sorted(candidates):
        print(f"  u={item[0]:>7} v={item[1]:>7} len={item[2]:>7} curve={item[3]}")