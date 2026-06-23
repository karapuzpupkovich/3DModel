import sys
import os
import math

PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part
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

def _collect_end_edges_for_fillet(solid, outer_edges, inner_edges, cell_len):
    end_edges = []
    for edge in solid.Edges:
        points = [e.Point for e in (edge.Vertex1, edge.Vertex2)]
        p1, p2 = points[0], points[1]
        if not (
            (abs(p1.z) < 0.01 and abs(p2.z) < 0.01)
            or (abs(p1.z - cell_len) < 0.01 and abs(p2.z - cell_len) < 0.01)
        ):
            continue
        v1_xy = FreeCAD.Vector(p1.x, p1.y, 0)
        v2_xy = FreeCAD.Vector(p2.x, p2.y, 0)
        matched = False
        for source_edge in list(outer_edges) + list(inner_edges):
            d1_f = (v1_xy - source_edge.Vertex1.Point).Length
            d2_f = (v2_xy - source_edge.Vertex2.Point).Length
            d1_r = (v1_xy - source_edge.Vertex2.Point).Length
            d2_r = (v2_xy - source_edge.Vertex1.Point).Length
            if (d1_f < 0.01 and d2_f < 0.01) or (d1_r < 0.01 and d2_r < 0.01):
                matched = True
                break
        if matched:
            end_edges.append(edge)
    return end_edges

cfg = DEFAULT_CONFIG
print("Testing integrated male joint 2D sequencing...")

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
        cfg.reinforcement_v1,
        cfg.reinforcement_v2,
        cfg.reinforcement_w1,
        cfg.reinforcement_w2,
        0.0,
        0.0
    )
    reinf_faces.append(rf)

inner_face_reinf = inner_face
for rf in reinf_faces:
    inner_face_reinf = inner_face_reinf.cut(rf)
inner_face_reinf = inner_face_reinf.removeSplitter()

# Now create male joints in 2D
male_faces = []
for face_index in (0, 5):
    alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
    # Build male joint face in local coordinates first
    mf = make_centered_trapezoid_face(
        FreeCAD.Vector(0, 0, 0),
        90.0,
        cfg.male_v1,
        cfg.male_v2,
        cfg.male_w1,
        cfg.male_w2,
        0.0,
        cfg.male_tip_radius
    )
    # Rotate and translate
    mf.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), alpha_deg - 90.0)
    mf.translate(face_mid)
    male_faces.append(mf)

# Union outer face with male joints in 2D
outer_face_with_joints = outer_face
for mf in male_faces:
    outer_face_with_joints = outer_face_with_joints.fuse(mf)
outer_face_with_joints = outer_face_with_joints.removeSplitter()

# Construct final 2D cell face
cell_face = outer_face_with_joints.cut(inner_face_reinf).removeSplitter()

# Extrude to 3D
cell_solid = cell_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
print("Integrated 3D solid created. Solid isValid:", cell_solid.isValid())

# Collect and apply end fillets
outer_wire_edges = cell_face.Wires[0].Edges
inner_wire_edges = cell_face.Wires[1].Edges

end_edges = _collect_end_edges_for_fillet(cell_solid, outer_wire_edges, inner_wire_edges, cfg.cell_len)
print(f"Collected {len(end_edges)} end edges. Attempting end fillet R={cfg.end_fillet_r}...")

try:
    cell_solid = cell_solid.makeFillet(cfg.end_fillet_r, end_edges)
    print("End fillet SUCCESS! Solid isValid:", cell_solid.isValid())
except Exception as e:
    print("End fillet FAILED:", e)
