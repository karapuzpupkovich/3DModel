import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

from honeycomb_cell.builder import _build_outer_vertices, get_face_angle_and_dist, make_centered_trapezoid_face
from honeycomb_cell.config import DEFAULT_CONFIG

cfg = DEFAULT_CONFIG
vertices_out = _build_outer_vertices(cfg)
face_index = 2
alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5

best = None
for step in range(0, 61):
    radius = step * 0.05
    face = make_centered_trapezoid_face(
        face_mid,
        alpha_deg,
        cfg.reinforcement_v1,
        cfg.reinforcement_v2,
        cfg.reinforcement_w1,
        cfg.reinforcement_w2,
        radius,
        radius,
    )
    valid = face.isValid()
    print(f"radius={radius:.2f} valid={valid}")
    if valid:
        best = radius

print(f"best={best}")
