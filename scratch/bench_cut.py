import FreeCAD
import Part
import math
import time

doc = FreeCAD.newDocument("BenchDoc")

r_out = 48.0
b_out = 15.0
a_out = 62.5
R_c_out = 6.0
cell_len = 200.0

def make_filleted_polygon_with_radii(vertices, radii):
    n = len(vertices)
    p_in = [None] * n
    p_out = [None] * n
    arcs = [None] * n
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
    return Part.Wire(all_edges)

def make_filleted_polygon(vertices, Rc):
    wire = make_filleted_polygon_with_radii(vertices, [Rc] * len(vertices))
    return Part.Face(wire)

def make_filleted_hex_wire(R, y_pos, Rc):
    points = []
    for i in range(6):
        ang = math.radians(i * 60)
        points.append(FreeCAD.Vector(R * math.cos(ang), y_pos, R * math.sin(ang)))
    
    n = len(points)
    p_in = [None] * n
    p_out = [None] * n
    arcs = [None] * n
    for i in range(n):
        v = points[i]
        v_prev = points[(i - 1) % n]
        v_next = points[(i + 1) % n]
        t1 = (v_prev - v).normalize()
        t2 = (v_next - v).normalize()
        dot = max(-1.0, min(1.0, t1.dot(t2)))
        theta = math.acos(dot)
        half_theta = theta / 2.0
        d = Rc / math.sin(half_theta)
        cot = 1.0 / math.tan(half_theta)
        bisector = (t1 + t2).normalize()
        C = v + bisector * d
        p_in[i] = v + t1 * (Rc * cot)
        p_out[i] = v + t2 * (Rc * cot)
        pmid = v + bisector * (d - Rc)
        arcs[i] = Part.Arc(p_in[i], pmid, p_out[i]).toShape()
        
    all_edges = []
    for i in range(n):
        all_edges.append(arcs[i])
        p_start = p_out[i]
        p_end = p_in[(i + 1) % n]
        if (p_start - p_end).Length > 1e-5:
            all_edges.append(Part.makeLine(p_start, p_end))
    return Part.Wire(all_edges)

def make_chamfered_hex_cutter(R, Rc, y_inner, y_outer, chamfer_dist=0.4):
    w1 = make_filleted_hex_wire(R + chamfer_dist, y_inner - 5.0, Rc)
    w2 = make_filleted_hex_wire(R + chamfer_dist, y_inner - chamfer_dist, Rc)
    w3 = make_filleted_hex_wire(R, y_inner, Rc)
    w4 = make_filleted_hex_wire(R, y_outer, Rc)
    w5 = make_filleted_hex_wire(R + chamfer_dist, y_outer + chamfer_dist, Rc)
    w6 = make_filleted_hex_wire(R + chamfer_dist, y_outer + 5.0, Rc)
    return Part.makeLoft([w1, w2, w3, w4, w5, w6], True, True)

print("Building base cell...")
vertices_out = [
    FreeCAD.Vector(a_out, 0, 0),
    FreeCAD.Vector(b_out, r_out, 0),
    FreeCAD.Vector(-b_out, r_out, 0),
    FreeCAD.Vector(-a_out, 0, 0),
    FreeCAD.Vector(-b_out, -r_out, 0),
    FreeCAD.Vector(b_out, -r_out, 0)
]
outer_face = make_filleted_polygon(vertices_out, R_c_out)
inner_face_no_reinf = outer_face.makeOffset2D(-2.3)
clean_cell_face = outer_face.cut(inner_face_no_reinf).removeSplitter()
cell_solid = clean_cell_face.extrude(FreeCAD.Vector(0, 0, cell_len))

print("Generating 50 cutters...")
t0 = time.time()
cutters = []
for idx in range(50):
    c = make_chamfered_hex_cutter(2.5, 0.8, -2.3, 0.0)
    # Translate slightly along Z to avoid exact overlap
    c.translate(FreeCAD.Vector(0, 0, 10.0 + idx * 3.0))
    cutters.append(c)
t1 = time.time()
print(f"50 cutters generated in {t1 - t0:.4f} seconds")

print("Fusing/Compounding cutters...")
t0 = time.time()
compound = Part.makeCompound(cutters)
t1 = time.time()
print(f"Compound created in {t1 - t0:.4f} seconds")

print("Performing cut of 50 cutters...")
t0 = time.time()
cut_solid = cell_solid.cut(compound).removeSplitter()
t1 = time.time()
print(f"Cut completed in {t1 - t0:.4f} seconds")
