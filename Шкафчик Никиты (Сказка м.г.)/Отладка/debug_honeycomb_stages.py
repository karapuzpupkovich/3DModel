import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

from Стандартная_ячейка.builder import (
    _build_outer_vertices,
    _collect_end_edges_for_fillet,
    get_face_angle_and_dist,
    make_centered_trapezoid_face,
    make_female_cutter_face,
    make_filleted_polygon,
)
from Стандартная_ячейка.config import DEFAULT_CONFIG

cfg = DEFAULT_CONFIG
vertices_out = _build_outer_vertices(cfg)


def report(label, shape):
    print(f"{label}: valid={shape.isValid()} type={shape.ShapeType} solids={len(shape.Solids)} faces={len(shape.Faces)}")
    if not shape.isValid():
        try:
            shape.check(True)
        except Exception as exc:
            print(f"  check(True): {exc}")


outer_face = make_filleted_polygon(vertices_out, cfg.corner_radius)
inner_face = outer_face.makeOffset2D(-cfg.wall_t)
cell_face = outer_face.cut(inner_face).removeSplitter()
cell_solid = cell_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
report("Stage1 shell", cell_solid)

end_edges = _collect_end_edges_for_fillet(cell_solid, cell_face.Wires[0].Edges, cell_face.Wires[1].Edges, cfg.cell_len)
cell_solid = cell_solid.makeFillet(cfg.end_fillet_r, end_edges)
report("Stage2 end fillet", cell_solid)

for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    reinforcement = make_centered_trapezoid_face(
        face_mid,
        alpha_deg,
        cfg.reinforcement_v1,
        cfg.reinforcement_v2,
        cfg.reinforcement_w1,
        cfg.reinforcement_w2,
        cfg.reinforcement_radius,
        cfg.reinforcement_radius,
    ).extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
    cell_solid = cell_solid.fuse(reinforcement).removeSplitter()
report("Stage3 reinforcement", cell_solid)

for face_index in (0, 5):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    male_face = make_centered_trapezoid_face(
        FreeCAD.Vector(0, 0, 0),
        90.0,
        cfg.male_v1,
        cfg.male_v2,
        cfg.male_w1,
        cfg.male_w2,
        0.0,
        cfg.male_tip_radius,
    )
    male_solid = male_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
    start_box = Part.makeBox(100.0, 100.0, 100.0)
    start_box.translate(FreeCAD.Vector(-50.0, -50.0, -100.0))
    start_box.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 45.0)
    start_box.translate(FreeCAD.Vector(0, 0, cfg.end_fillet_r))
    end_box = Part.makeBox(100.0, 100.0, 100.0)
    end_box.translate(FreeCAD.Vector(-50.0, -50.0, 0.0))
    end_box.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -45.0)
    end_box.translate(FreeCAD.Vector(0, 0, cfg.cell_len - cfg.end_fillet_r))
    male_solid = male_solid.cut(start_box).cut(end_box)
    male_solid.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), alpha_deg - 90.0)
    male_solid.translate(face_mid)
    cell_solid = cell_solid.fuse(male_solid).removeSplitter()
report("Stage4 male joints", cell_solid)

for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    female_face = make_female_cutter_face(face_mid, alpha_deg, cfg)
    female_solid = female_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
    cell_solid = cell_solid.cut(female_solid).removeSplitter()
report("Stage5 female grooves", cell_solid)
