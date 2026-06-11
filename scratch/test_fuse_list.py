import sys
import os
import math

PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part
from honeycomb_cell.config import DEFAULT_CONFIG, HoneycombConfig

cfg = DEFAULT_CONFIG

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

vertices_out = [
    FreeCAD.Vector(cfg.a_out, 0, 0),
    FreeCAD.Vector(cfg.b_out, cfg.r_out, 0),
    FreeCAD.Vector(-cfg.b_out, cfg.r_out, 0),
    FreeCAD.Vector(-cfg.a_out, 0, 0),
    FreeCAD.Vector(-cfg.b_out, -cfg.r_out, 0),
    FreeCAD.Vector(cfg.b_out, -cfg.r_out, 0),
]

outer_face = Part.Face(make_filleted_polygon_with_radii(vertices_out, [cfg.corner_radius]*6))

# Create male joint faces
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

# Method 1: List fuse
try:
    f_list = outer_face.fuse(male_faces).removeSplitter()
    print("Method 1 (list fuse) faces count:", len(f_list.Faces))
except Exception as e:
    print("Method 1 failed:", e)

# Method 2: Fuse without intermediate removeSplitter
try:
    f_no_splitter = outer_face.fuse(male_faces[0]).fuse(male_faces[1]).removeSplitter()
    print("Method 2 (no intermediate removeSplitter) faces count:", len(f_no_splitter.Faces))
except Exception as e:
    print("Method 2 failed:", e)

# Method 3: Fuse joint 1 first, then joint 0
try:
    f_reverse = outer_face.fuse(male_faces[1]).removeSplitter().fuse(male_faces[0]).removeSplitter()
    print("Method 3 (reverse order) faces count:", len(f_reverse.Faces))
except Exception as e:
    print("Method 3 failed:", e)

# Method 4: Fuse in 3D instead of 2D? No, we want 2D.
# Method 5: Union of Wires and then create Face
try:
    # Get wires
    w_out = outer_face.Wires[0]
    w_m0 = male_faces[0].Wires[0]
    w_m1 = male_faces[1].Wires[0]
    # Fuse them
    w_f = w_out.fuse(w_m0).fuse(w_m1)
    w_f_clean = w_f.removeSplitter()
    print("Method 5 (wire fuse) faces count:", len(Part.Face(w_f_clean).Faces))
except Exception as e:
    print("Method 5 failed:", e)
