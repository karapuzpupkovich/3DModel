import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from dataclasses import replace
import FreeCAD
import Part

from honeycomb_cell.builder import _build_outer_vertices, get_face_angle_and_dist, make_filleted_polygon, make_reinforcement_face, make_centered_trapezoid_face
from honeycomb_cell.config import DEFAULT_CONFIG

cfg = DEFAULT_CONFIG
vertices_out = _build_outer_vertices(cfg)

# 1. Outer face
outer_face = make_filleted_polygon(vertices_out, cfg.corner_radius)

# 2. Inner face (void)
inner_face = outer_face.makeOffset2D(-cfg.wall_t)

print(f"Base inner_face: valid={inner_face.isValid()} wires={len(inner_face.Wires)}")

# 3. Create reinforcement faces (simple trapezoid, no 2D filleting to avoid tangent vertices)
reinf_faces = []
for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    # Use make_centered_trapezoid_face with R_base=0.0, R_tip=0.0
    rf = make_centered_trapezoid_face(
        face_mid,
        alpha_deg,
        cfg.reinforcement_v1,
        cfg.reinforcement_v2,
        cfg.reinforcement_w1,
        cfg.reinforcement_w2,
        0.0,
        0.0,
    )
    reinf_faces.append(rf)
    print(f"Reinf face {face_index}: valid={rf.isValid()}")

# 4. Cut reinforcement from inner face
inner_face_reinf = inner_face
for rf in reinf_faces:
    inner_face_reinf = inner_face_reinf.cut(rf)
inner_face_reinf = inner_face_reinf.removeSplitter()

print(f"Thickened inner_face: valid={inner_face_reinf.isValid()} Wires={len(inner_face_reinf.Wires)}")

# 5. Build cell face
cell_face = outer_face.cut(inner_face_reinf).removeSplitter()
print(f"Cell face: valid={cell_face.isValid()} Wires={len(cell_face.Wires)}")

# 6. Extrude
cell_solid = cell_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
print(f"Cell solid: valid={cell_solid.isValid()} solids={len(cell_solid.Solids)} faces={len(cell_solid.Faces)}")

# 7. Collect and apply end fillets (all outer and inner edges together)
from honeycomb_cell.builder import _collect_end_edges_for_fillet
end_edges = _collect_end_edges_for_fillet(
    cell_solid,
    cell_face.Wires[0].Edges,
    cell_face.Wires[1].Edges,
    cfg.cell_len,
)
print(f"Collected {len(end_edges)} end edges.")
try:
    cell_solid = cell_solid.makeFillet(cfg.end_fillet_r, end_edges)
    print(f"Filleted cell solid: valid={cell_solid.isValid()} solids={len(cell_solid.Solids)} faces={len(cell_solid.Faces)}")
except Exception as e:
    print(f"Fillet failed: {e}")

sys.stdout.flush()
