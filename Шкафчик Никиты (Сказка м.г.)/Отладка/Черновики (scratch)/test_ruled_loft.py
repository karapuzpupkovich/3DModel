import FreeCAD
import Part
import math
import time

doc = FreeCAD.newDocument("TestRuledLoft")

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

R = 2.5
Rc = 0.8
d = 0.4
y_inner = -2.3
y_outer = 0.0

w1 = make_filleted_hex_wire(R + d, y_inner - 5.0, Rc)
w2 = make_filleted_hex_wire(R + d, y_inner - d, Rc)
w3 = make_filleted_hex_wire(R, y_inner, Rc)
w4 = make_filleted_hex_wire(R, y_outer, Rc)
w5 = make_filleted_hex_wire(R + d, y_outer + d, Rc)
w6 = make_filleted_hex_wire(R + d, y_outer + 5.0, Rc)

t0 = time.time()
loft_ruled = Part.makeLoft([w1, w2, w3, w4, w5, w6], True, True)
t1 = time.time()
print(f"Ruled Loft created in {t1 - t0:.6f} seconds")

t0 = time.time()
loft_smooth = Part.makeLoft([w1, w2, w3, w4, w5, w6], True, False)
t2 = time.time()
print(f"Smooth Loft created in {t2 - t0:.6f} seconds")

print("Ruled loft volume:", loft_ruled.Volume)
print("Smooth loft volume:", loft_smooth.Volume)
