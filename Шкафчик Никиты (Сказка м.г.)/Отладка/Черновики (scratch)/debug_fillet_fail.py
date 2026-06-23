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
    make_centered_trapezoid_face,
    _collect_end_edges_for_fillet
)

cfg = DEFAULT_CONFIG
vertices_out = _build_outer_vertices(cfg)

# Stage 1
outer_face = make_filleted_polygon(vertices_out, cfg.corner_radius)
inner_face = outer_face.makeOffset2D(-cfg.wall_t)

reinf_faces = []
for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    rf = make_reinforcement_face(face_mid, alpha_deg, cfg)
    reinf_faces.append(rf)

inner_face_reinf = inner_face
for rf in reinf_faces:
    inner_face_reinf = inner_face_reinf.cut(rf)
inner_face_reinf = inner_face_reinf.removeSplitter()

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

outer_face_with_joints = outer_face.fuse(male_faces).removeSplitter()
cell_face = outer_face_with_joints.cut(inner_face_reinf).removeSplitter()
cell_solid = cell_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))

print(f"Solid faces: {len(cell_solid.Faces)}, Solid edges: {len(cell_solid.Edges)}")
print(f"cell_face wires count: {len(cell_face.Wires)}")
print(f"cell_face Wire 0 edges count: {len(cell_face.Wires[0].Edges)}")
print(f"cell_face Wire 1 edges count: {len(cell_face.Wires[1].Edges)}")

end_edges = _collect_end_edges_for_fillet(
    cell_solid,
    cell_face.Wires[0].Edges,
    cell_face.Wires[1].Edges,
    cfg.cell_len,
)
print(f"Collected end edges: {len(end_edges)}")

try:
    cell_solid_filleted = cell_solid.makeFillet(cfg.end_fillet_r, end_edges)
    print("Fillet SUCCESS! Filleted solid isValid:", cell_solid_filleted.isValid())
except Exception as e:
    print("Fillet FAILED:", e)
