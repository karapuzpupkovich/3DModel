import sys
import os
import math

PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part
from honeycomb_cell.config import DEFAULT_CONFIG, HoneycombConfig
from honeycomb_cell.builder import (
    _build_outer_vertices,
    make_filleted_polygon,
    make_reinforcement_face,
    get_face_angle_and_dist,
    make_centered_trapezoid_face
)

cfg = DEFAULT_CONFIG
vertices_out = _build_outer_vertices(cfg)

outer_face = make_filleted_polygon(vertices_out, cfg.corner_radius)

male_faces = []
for face_index in (0, 5):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    mf = make_centered_trapezoid_face(
        FreeCAD.Vector(0, 0, 0),
        90.0,
        cfg.male_v1,
        cfg.male_v2,
        cfg.male_w1,
        cfg.male_w2,
        0.0,
        cfg.male_tip_radius,
    )
    mf.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), alpha_deg - 90.0)
    mf.translate(face_mid)
    male_faces.append(mf)

# List fuse
outer_face_with_joints = outer_face.fuse(male_faces).removeSplitter()

print("Analyzing fused outer wire edges...")
wire = outer_face_with_joints.Wires[0]
print(f"Total edges in fused wire: {len(wire.Edges)}")

tiny_edges = []
for idx, edge in enumerate(wire.Edges):
    l = edge.Length
    c = edge.BoundBox.Center
    print(f"Edge {idx}: Length={l:.6f} mm, Center=({c.x:.2f}, {c.y:.2f})")
    if l < 0.8:
        tiny_edges.append((idx, l))

print(f"\nTiny edges (length < 0.8 mm): {len(tiny_edges)}")
for idx, l in tiny_edges:
    print(f"  Edge {idx}: Length={l:.6f} mm")
