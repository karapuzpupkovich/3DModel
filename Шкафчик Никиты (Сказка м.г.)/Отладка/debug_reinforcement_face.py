import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

from Стандартная_ячейка.builder import _build_outer_vertices, get_face_angle_and_dist, make_centered_trapezoid_face
from Стандартная_ячейка.config import DEFAULT_CONFIG

cfg = DEFAULT_CONFIG
vertices_out = _build_outer_vertices(cfg)
face_index = 2
alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5

for radius in (cfg.reinforcement_radius, 0.0):
    reinforcement_face = make_centered_trapezoid_face(
        face_mid,
        alpha_deg,
        cfg.reinforcement_v1,
        cfg.reinforcement_v2,
        cfg.reinforcement_w1,
        cfg.reinforcement_w2,
        radius,
        radius,
    )
    reinforcement_solid = reinforcement_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
    print(f"radius={radius}")
    print(f"  face valid={reinforcement_face.isValid()} wires={len(reinforcement_face.Wires)} edges={len(reinforcement_face.Edges)}")
    print(f"  solid valid={reinforcement_solid.isValid()} solids={len(reinforcement_solid.Solids)} faces={len(reinforcement_solid.Faces)}")
    try:
        reinforcement_face.check(True)
        print("  face check=True OK")
    except Exception as exc:
        print(f"  face check=True: {exc}")
    try:
        reinforcement_solid.check(True)
        print("  solid check=True OK")
    except Exception as exc:
        print(f"  solid check=True: {exc}")
