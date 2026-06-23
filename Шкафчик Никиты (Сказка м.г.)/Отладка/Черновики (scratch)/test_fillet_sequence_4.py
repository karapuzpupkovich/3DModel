import sys, os
PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part
import math
from honeycomb_cell.config import DEFAULT_CONFIG, HoneycombConfig

def get_face_angle_and_dist(index: int, config: HoneycombConfig):
    theta_0 = math.degrees(math.atan2(config.a_out - config.b_out, config.r_out))
    if index == 0: return theta_0, config.a_out * math.cos(math.radians(theta_0))
    if index == 1: return 90.0, config.r_out
    if index == 2: return 180.0 - theta_0, config.a_out * math.cos(math.radians(theta_0))
    if index == 3: return 180.0 + theta_0, config.a_out * math.cos(math.radians(theta_0))
    if index == 4: return 270.0, config.r_out
    if index == 5: return 360.0 - theta_0, config.a_out * math.cos(math.radians(theta_0))
    raise IndexError(f"Index error: {index}")

def make_filleted_polygon_with_radii(vertices, radii):
    count = len(vertices)
    p_in = [None] * count
    p_out = [None] * count
    arcs = [None] * count
    for index, vertex in enumerate(vertices):
        radius = radii[index]
        if radius > 0.01:
            prev_vertex = vertices[(index - 1) % count]
            next_vertex = vertices[(index + 1) % count]
            tangent_1 = (prev_vertex - vertex).normalize()
            tangent_2 = (next_vertex - vertex).normalize()
            dot_value = max(-1.0, min(1.0, tangent_1.dot(tangent_2)))
            theta = math.acos(dot_value)
            half_theta = theta / 2.0
            distance = radius / math.sin(half_theta)
            cotangent = 1.0 / math.tan(half_theta)
            bisector = (tangent_1 + tangent_2).normalize()
            p_in[index] = vertex + tangent_1 * (radius * cotangent)
            p_out[index] = vertex + tangent_2 * (radius * cotangent)
            pivot = vertex + bisector * (distance - radius)
            arcs[index] = Part.Arc(p_in[index], pivot, p_out[index]).toShape()
        else:
            p_in[index] = vertex
            p_out[index] = vertex
            arcs[index] = None
    edges = []
    for index in range(count):
        if arcs[index] is not None:
            edges.append(arcs[index])
        line_start = p_out[index]
        line_end = p_in[(index + 1) % count]
        if (line_start - line_end).Length > 1e-5:
            edges.append(Part.makeLine(line_start, line_end))
    return Part.Wire(edges)

def make_centered_trapezoid_face(mid, alpha_deg, v1, v2, w1, w2, r_base=0.0, r_tip=0.0):
    alpha = math.radians(alpha_deg)
    normal = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    tangent = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    max_radius = 0.49 * min(abs(v2 - v1), w1, w2)
    r_base = min(r_base, max_radius)
    r_tip = min(r_tip, max_radius)
    p1 = mid - tangent * (w1 / 2.0) + normal * v1
    p2 = mid - tangent * (w2 / 2.0) + normal * v2
    p3 = mid + tangent * (w2 / 2.0) + normal * v2
    p4 = mid + tangent * (w1 / 2.0) + normal * v1
    return Part.Face(make_filleted_polygon_with_radii([p1, p2, p3, p4], [r_base, r_tip, r_tip, r_base]))

def make_female_cutter_face(mid, alpha_deg, config):
    alpha = math.radians(alpha_deg)
    normal = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    tangent = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    p1 = mid - tangent * (config.female_w_base / 2.0 + config.female_wing_offset) + normal * config.female_outer_offset
    p2 = mid - tangent * (config.female_w_base / 2.0) + normal * 0.0
    p3 = mid - tangent * (config.female_w_tip / 2.0) + normal * (-config.female_depth)
    p4 = mid + tangent * (config.female_w_tip / 2.0) + normal * (-config.female_depth)
    p5 = mid + tangent * (config.female_w_base / 2.0) + normal * 0.0
    p6 = mid + tangent * (config.female_w_base / 2.0 + config.female_wing_offset) + normal * config.female_outer_offset
    vertices = [p1, p2, p3, p4, p5, p6]
    radii = [0.0, config.female_entry_radius, 0.0, 0.0, config.female_entry_radius, 0.0]
    return Part.Face(make_filleted_polygon_with_radii(vertices, radii))

cfg = DEFAULT_CONFIG
cfg_test = HoneycombConfig(
    reinforcement_root_radius=1.2,
    reinforcement_tip_radius=1.2,
    reinforcement_edge_fillet=0.0
)

print("Starting test_fillet_sequence_4...")
# 1. 2D profile with reinforcement and male joints integrated
vertices_out = [
    FreeCAD.Vector(cfg.a_out, 0, 0),
    FreeCAD.Vector(cfg.b_out, cfg.r_out, 0),
    FreeCAD.Vector(-cfg.b_out, cfg.r_out, 0),
    FreeCAD.Vector(-cfg.a_out, 0, 0),
    FreeCAD.Vector(-cfg.b_out, -cfg.r_out, 0),
    FreeCAD.Vector(cfg.b_out, -cfg.r_out, 0),
]

outer_face = Part.Face(make_filleted_polygon_with_radii(vertices_out, [cfg.corner_radius]*6))
inner_face = outer_face.makeOffset2D(-cfg.wall_t)

# Create reinforcement faces in 2D
reinf_faces = []
for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    rf = make_centered_trapezoid_face(
        face_mid,
        alpha_deg,
        cfg_test.reinforcement_v1,
        cfg_test.reinforcement_v2,
        cfg_test.reinforcement_w1,
        cfg_test.reinforcement_w2,
        cfg_test.reinforcement_root_radius,
        cfg_test.reinforcement_tip_radius
    )
    reinf_faces.append(rf)

inner_face_reinf = inner_face
for rf in reinf_faces:
    inner_face_reinf = inner_face_reinf.cut(rf)
inner_face_reinf = inner_face_reinf.removeSplitter()

# Integrate male joints in 2D
male_faces = []
for face_index in (0, 5):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    mf = make_centered_trapezoid_face(
        face_mid,
        alpha_deg,
        cfg.male_v1,
        cfg.male_v2,
        cfg.male_w1,
        cfg.male_w2,
        0.0,
        cfg.male_tip_radius
    )
    male_faces.append(mf)

outer_face_with_joints = outer_face
for mf in male_faces:
    outer_face_with_joints = outer_face_with_joints.fuse(mf)
outer_face_with_joints = outer_face_with_joints.removeSplitter()

cell_face = outer_face_with_joints.cut(inner_face_reinf).removeSplitter()
print(f"Step 1: Cell Face type={cell_face.ShapeType}, isValid={cell_face.isValid()}")

cell_solid = cell_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
print(f"Step 2: Extruded cell solid type={cell_solid.ShapeType}, isValid={cell_solid.isValid()}")

# 3. Apply end fillets on the flat-ended solid
end_edges = []
for edge in cell_solid.Edges:
    p1 = edge.Vertex1.Point
    p2 = edge.Vertex2.Point
    if abs(p1.z - p2.z) < 10.0:
        if (p1.z <= 0.01 and p2.z <= 0.01) or (p1.z >= cfg.cell_len - 0.01 and p2.z >= cfg.cell_len - 0.01):
            end_edges.append(edge)

print(f"Collected {len(end_edges)} end edges. Attempting makeFillet...")
try:
    cell_solid = cell_solid.makeFillet(cfg.end_fillet_r, end_edges)
    print("Fillet SUCCESS! Solid isValid:", cell_solid.isValid())
except Exception as e:
    print("Fillet FAILED:", e)
    sys.exit(1)

# 4. Apply 45-degree end cuts to male joints in place
for face_index in (0, 5):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    
    start_box = Part.makeBox(100.0, 100.0, 100.0)
    start_box.translate(FreeCAD.Vector(-50.0, -50.0, -100.0))
    start_box.rotate(FreeCAD.Vector(0, 2.2, 0.0), FreeCAD.Vector(1, 0, 0), 45.0)

    end_box = Part.makeBox(100.0, 100.0, 100.0)
    end_box.translate(FreeCAD.Vector(-50.0, -50.0, 0.0))
    end_box.rotate(FreeCAD.Vector(0, 2.2, cfg.cell_len), FreeCAD.Vector(1, 0, 0), -45.0)

    for box in (start_box, end_box):
        box.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), alpha_deg - 90.0)
        box.translate(face_mid)
        cell_solid = cell_solid.cut(box).removeSplitter()

print("Applied 45-degree end cuts. Solid isValid:", cell_solid.isValid())

# 5. Cut female grooves
for face_index in (2, 3):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    female_face = make_female_cutter_face(face_mid, alpha_deg, cfg)
    female_solid = female_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
    cell_solid = cell_solid.cut(female_solid).removeSplitter()

print("Cut female grooves. Final Solid isValid:", cell_solid.isValid())
