import FreeCAD
import Part
import math

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

# Build tongue solid in local coordinates
male_face = make_centered_trapezoid_face(FreeCAD.Vector(0,0,0), 90.0, -0.5, 3.0, 23.0, 30.0, 0.0, 0.4)
tongue = male_face.extrude(FreeCAD.Vector(0, 0, 200.0))

# Start cut box: rotate 45 around (0, 2.2, 0)
box_start = Part.makeBox(100.0, 100.0, 100.0)
box_start.translate(FreeCAD.Vector(-50.0, -50.0, -100.0))
box_start.rotate(FreeCAD.Vector(0, 2.2, 0.0), FreeCAD.Vector(1, 0, 0), 45.0)

# End cut box: rotate -45 around (0, 2.2, 200)
box_end = Part.makeBox(100.0, 100.0, 100.0)
box_end.translate(FreeCAD.Vector(-50.0, -50.0, 0.0))
box_end.rotate(FreeCAD.Vector(0, 2.2, 200.0), FreeCAD.Vector(1, 0, 0), -45.0)

tongue_cut = tongue.cut(box_start).cut(box_end)
bbox = tongue_cut.BoundBox
print(f"BBox Z: {bbox.ZMin:.4f} to {bbox.ZMax:.4f}")

# Find Z coordinates of vertices at tip Y=3.0 and base Y=-0.5
z_tip = [v.Point.z for v in tongue_cut.Vertexes if abs(v.Point.y - 3.0) < 0.1]
z_base = [v.Point.z for v in tongue_cut.Vertexes if abs(v.Point.y - (-0.5)) < 0.1]

print(f"Z at tip (Y=3.0): min={min(z_tip):.4f}, max={max(z_tip):.4f}")
print(f"Z at base (Y=-0.5): min={min(z_base):.4f}, max={max(z_base):.4f}")
print("IsValid:", tongue_cut.isValid())
