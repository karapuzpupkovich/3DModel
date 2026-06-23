import FreeCAD
import Part
import math

doc = FreeCAD.newDocument("TestTongueVolume")

def make_centered_trapezoid_face(mid, alpha_deg, v1, v2, w1, w2, R_base=0.0, R_tip=0.0):
    alpha = math.radians(alpha_deg)
    n_vec = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    t_vec = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    p1 = mid - t_vec * (w1 / 2.0) + n_vec * v1
    p2 = mid - t_vec * (w2 / 2.0) + n_vec * v2
    p3 = mid + t_vec * (w2 / 2.0) + n_vec * v2
    p4 = mid + t_vec * (w1 / 2.0) + n_vec * v1
    vertices = [p1, p2, p3, p4]
    
    n = len(vertices)
    p_in = [None] * n
    p_out = [None] * n
    arcs = [None] * n
    radii = [R_base, R_tip, R_tip, R_base]
    for i in range(n):
        v = vertices[i]
        r = radii[i]
        if r > 0.01:
            v_prev = vertices[(i - 1) % n]
            v_next = vertices[(i + 1) % n]
            t1 = (v_prev - v).normalize()
            t2 = (v_next - v).normalize()
            dot = max(-1.0, min(1.0, t1.dot(t2)))
            theta = math.acos(dot)
            half_theta = theta / 2.0
            d = r / math.sin(half_theta)
            cot = 1.0 / math.tan(half_theta)
            bisector = (t1 + t2).normalize()
            C = v + bisector * d
            p_in[i] = v + t1 * (r * cot)
            p_out[i] = v + t2 * (r * cot)
            pmid = v + bisector * (d - r)
            arcs[i] = Part.Arc(p_in[i], pmid, p_out[i]).toShape()
        else:
            p_in[i] = v
            p_out[i] = v
            arcs[i] = None
    all_edges = []
    for i in range(n):
        if arcs[i] is not None:
            all_edges.append(arcs[i])
        p_start = p_out[i]
        p_end = p_in[(i + 1) % n]
        if (p_start - p_end).Length > 1e-5:
            all_edges.append(Part.makeLine(p_start, p_end))
    wire = Part.Wire(all_edges)
    return Part.Face(wire)

mid_local = FreeCAD.Vector(0,0,0)
male_face = make_centered_trapezoid_face(mid_local, 90.0, -0.5, 3.0, 23.0, 30.0, 0.0, 0.4)
tongue = male_face.extrude(FreeCAD.Vector(0, 0, 200.0))

# Start cut:
# We want to remove the region Z < 0.8 + Y.
# We make a box that starts from Z=0.8 and goes in -Z direction.
# Before rotation, box is: X[-50, 50], Y[-50, 50], Z[-100, 0]
box_start = Part.makeBox(100.0, 100.0, 100.0)
box_start.translate(FreeCAD.Vector(-50.0, -50.0, -100.0))
# Rotate by +45 degrees around X:
box_start.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 45.0)
# Translate by 0.8 in Z:
box_start.translate(FreeCAD.Vector(0, 0, 0.8))

t_cut_start = tongue.cut(box_start)

# End cut:
# We want to remove the region Z > 199.2 - Y.
# We make a box that starts from Z=199.2 and goes in +Z direction.
# Before rotation, box is: X[-50, 50], Y[-50, 50], Z[0, 100]
box_end = Part.makeBox(100.0, 100.0, 100.0)
box_end.translate(FreeCAD.Vector(-50.0, -50.0, 0.0))
# Rotate by -45 degrees around X:
box_end.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -45.0)
# Translate by 199.2 in Z:
box_end.translate(FreeCAD.Vector(0, 0, 199.2))

t_cut_both = t_cut_start.cut(box_end)

print("Original Volume:", tongue.Volume)
print("Volume after CutBoth:", t_cut_both.Volume)
bbox = t_cut_both.BoundBox
print(f"BBox: X({bbox.XMin:.4f} to {bbox.XMax:.4f}), Y({bbox.YMin:.4f} to {bbox.YMax:.4f}), Z({bbox.ZMin:.4f} to {bbox.ZMax:.4f})")

print("Vertices with Z < 5.0:")
for v in t_cut_both.Vertexes:
    if v.Point.z < 5.0:
        print(f"  ({v.Point.x:.4f}, {v.Point.y:.4f}, {v.Point.z:.4f})")
