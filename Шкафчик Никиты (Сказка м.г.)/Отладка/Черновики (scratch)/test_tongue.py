import FreeCAD
import Part
import math

doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("TestTongueDoc")

# Remove old objects if they exist
for name in ["TestTongue", "CutStart", "CutEnd"]:
    old = doc.getObject(name)
    if old:
        doc.removeObject(old.Name)

def make_centered_trapezoid_face(mid, alpha_deg, v1, v2, w1, w2, R_base=0.0, R_tip=0.0):
    alpha = math.radians(alpha_deg)
    n_vec = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    t_vec = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    p1 = mid - t_vec * (w1 / 2.0) + n_vec * v1
    p2 = mid - t_vec * (w2 / 2.0) + n_vec * v2
    p3 = mid + t_vec * (w2 / 2.0) + n_vec * v2
    p4 = mid + t_vec * (w1 / 2.0) + n_vec * v1
    vertices = [p1, p2, p3, p4]
    
    # Simple make_filleted_polygon_with_radii inside:
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

# Build tongue solid in local coordinates (where face normal is +Y, tangent is -X)
# mid = (0,0), alpha = 90.0
mid_local = FreeCAD.Vector(0,0,0)
male_face = make_centered_trapezoid_face(mid_local, 90.0, -0.5, 3.0, 23.0, 30.0, 0.0, 0.4)
tongue = male_face.extrude(FreeCAD.Vector(0, 0, 200.0))

# We want to keep the region where Z >= 0.8 + Y (at the start) and Z <= 199.2 - Y (at the end).
# Let's cut the tongue with two wedge-like boxes.
# Cutting box for start:
# A box of size 100x100x100.
# We want it to occupy the region Z < 0.8 + Y.
# Let's define the box:
box_start = Part.makeBox(100.0, 100.0, 100.0)
# Translate it to center in X, and place Y and Z appropriately:
# X goes from -50 to 50
box_start.translate(FreeCAD.Vector(-50.0, -50.0, -100.0)) # now Z is from -100 to 0
# Rotate 45 degrees around X axis to get Z - Y = 0 boundary
box_start.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -45.0)
# Now shift it to Z = 0.8
box_start.translate(FreeCAD.Vector(0, 0, 0.8))

# Cutting box for end:
box_end = Part.makeBox(100.0, 100.0, 100.0)
box_end.translate(FreeCAD.Vector(-50.0, -50.0, 0.0)) # Z is from 0 to 100
box_end.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 45.0)
box_end.translate(FreeCAD.Vector(0, 0, 199.2))

# Cut the tongue
tongue_cut = tongue.cut(box_start).cut(box_end)

# Add to document to inspect bounding box
obj = doc.addObject("Part::Feature", "TestTongue")
obj.Shape = tongue_cut
doc.recompute()

bbox = tongue_cut.BoundBox
print(f"Tongue BBox: X({bbox.XMin:.2f} to {bbox.XMax:.2f}), Y({bbox.YMin:.2f} to {bbox.YMax:.2f}), Z({bbox.ZMin:.2f} to {bbox.ZMax:.2f})")
# Let's verify Z limits at Y = -0.5 (base) and Y = 3.0 (tip):
# Z at Y=-0.5 should be 0.8 - 0.5 = 0.3? No, Z = 0.8 + Y, so Z = 0.8 - 0.5 = 0.3.
# Z at Y=3.0 should be 0.8 + 3.0 = 3.8.
# Z at Y=-0.5 at end should be 199.2 - (-0.5) = 199.7.
# Z at Y=3.0 at end should be 199.2 - 3.0 = 196.2.
# So total Z bounds should be [0.3, 199.7]. Let's check!
