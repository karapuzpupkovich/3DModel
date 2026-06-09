import FreeCAD
import Part
import math
import sys

# We will load the actual build_cabinet.py or create_cabinet_model.py logic to build the cell shape,
# then instantiate two of them at their respective centers, and compute their common volume.

# First, let's copy the create_honeycomb_cell_shape logic from build_cabinet.py
# (We will use the existing values of parameters)

r_out = 48.0
b_out = 15.0
a_out = 62.5
R_c_out = 6.0
cell_len = 200.0

def get_face_angle_and_dist(i, a, b, r):
    theta_0 = math.degrees(math.atan2(a - b, r))
    if i == 0:
        return theta_0, a * math.cos(math.radians(theta_0))
    elif i == 1:
        return 90.0, r
    elif i == 2:
        return 180.0 - theta_0, a * math.cos(math.radians(theta_0))
    elif i == 3:
        return 180.0 + theta_0, a * math.cos(math.radians(theta_0))
    elif i == 4:
        return 270.0, r
    elif i == 5:
        return 360.0 - theta_0, a * math.cos(math.radians(theta_0))

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

def make_centered_trapezoid_face(mid, alpha_deg, v1, v2, w1, w2, R_base=0.0, R_tip=0.0):
    alpha = math.radians(alpha_deg)
    n_vec = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    t_vec = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    p1 = mid - t_vec * (w1 / 2.0) + n_vec * v1
    p2 = mid - t_vec * (w2 / 2.0) + n_vec * v2
    p3 = mid + t_vec * (w2 / 2.0) + n_vec * v2
    p4 = mid + t_vec * (w1 / 2.0) + n_vec * v1
    vertices = [p1, p2, p3, p4]
    radii = [R_base, R_tip, R_tip, R_base]
    wire = make_filleted_polygon_with_radii(vertices, radii)
    return Part.Face(wire)

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

def create_honeycomb_cell_shape():
    vertices_out = [
        FreeCAD.Vector(a_out, 0, 0),
        FreeCAD.Vector(b_out, r_out, 0),
        FreeCAD.Vector(-b_out, r_out, 0),
        FreeCAD.Vector(-a_out, 0, 0),
        FreeCAD.Vector(-b_out, -r_out, 0),
        FreeCAD.Vector(b_out, -r_out, 0)
    ]
    
    # 1. Base outer face
    outer_face = make_filleted_polygon(vertices_out, R_c_out)
    
    # 2. Offset face for 2.3mm uniform wall
    inner_face_no_reinf = outer_face.makeOffset2D(-2.3)
    clean_cell_face = outer_face.cut(inner_face_no_reinf).removeSplitter()
    clean_cell_solid = clean_cell_face.extrude(FreeCAD.Vector(0, 0, cell_len))
    
    # 3. Fillet both outer and inner ends
    outer_wire_edges = clean_cell_face.Wires[0].Edges
    inner_wire_edges = clean_cell_face.Wires[1].Edges
    
    end_edges_to_fillet = []
    for e in clean_cell_solid.Edges:
        pts = [e.Vertex1.Point, e.Vertex2.Point]
        if all(abs(p.z) < 0.01 for p in pts) or all(abs(p.z - cell_len) < 0.01 for p in pts):
            v1_xy = FreeCAD.Vector(e.Vertex1.Point.x, e.Vertex1.Point.y, 0)
            v2_xy = FreeCAD.Vector(e.Vertex2.Point.x, e.Vertex2.Point.y, 0)
            is_end_edge = False
            for oe in outer_wire_edges:
                d1_f = (v1_xy - oe.Vertex1.Point).Length
                d2_f = (v2_xy - oe.Vertex2.Point).Length
                d1_r = (v1_xy - oe.Vertex2.Point).Length
                d2_r = (v2_xy - oe.Vertex1.Point).Length
                if (d1_f < 0.01 and d2_f < 0.01) or (d1_r < 0.01 and d2_r < 0.01):
                    is_end_edge = True
                    break
            if not is_end_edge:
                for ie in inner_wire_edges:
                    d1_f = (v1_xy - ie.Vertex1.Point).Length
                    d2_f = (v2_xy - ie.Vertex2.Point).Length
                    d1_r = (v1_xy - ie.Vertex2.Point).Length
                    d2_r = (v2_xy - ie.Vertex1.Point).Length
                    if (d1_f < 0.01 and d2_f < 0.01) or (d1_r < 0.01 and d2_r < 0.01):
                        is_end_edge = True
                        break
            if is_end_edge:
                end_edges_to_fillet.append(e)
                
    cell_solid = clean_cell_solid.makeFillet(0.8, end_edges_to_fillet)
    
    # 4. Reinforcement platforms
    reinf_solids = []
    for i in [2, 3]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        reinf_face = make_centered_trapezoid_face(mid, alpha, -2.3, -4.8, 48.0, 38.0, 2.0, 2.0)
        reinf_solid = reinf_face.extrude(FreeCAD.Vector(0, 0, cell_len))
        reinf_solids.append(reinf_solid)
    for rs in reinf_solids:
        cell_solid = cell_solid.fuse(rs).removeSplitter()
        
    # 5. Add tongues (Male) - shorter (0.8 to 199.2) and chamfered at 45 deg
    for i in [0, 5]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        
        # Local tongue face
        male_face_local = make_centered_trapezoid_face(FreeCAD.Vector(0,0,0), 90.0, -0.5, 3.0, 23.0, 30.0, 0.0, 0.4)
        male_solid_local = male_face_local.extrude(FreeCAD.Vector(0, 0, cell_len))
        
        # Cut ends of the local tongue at 45 degrees
        box_start = Part.makeBox(100.0, 100.0, 100.0)
        box_start.translate(FreeCAD.Vector(-50.0, -50.0, -100.0))
        box_start.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), 45.0)
        box_start.translate(FreeCAD.Vector(0, 0, 0.8))
        
        box_end = Part.makeBox(100.0, 100.0, 100.0)
        box_end.translate(FreeCAD.Vector(-50.0, -50.0, 0.0))
        box_end.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -45.0)
        box_end.translate(FreeCAD.Vector(0, 0, 199.2))
        
        male_solid_local = male_solid_local.cut(box_start).cut(box_end)
        
        # Transform local to global position
        male_solid_local.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), alpha - 90.0)
        male_solid_local.translate(mid)
        
        cell_solid = cell_solid.fuse(male_solid_local).removeSplitter()
        
    # 6. Cut grooves (Female) - v1 = 0.4 mm to remove the entry cusp!
    for i in [2, 3]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        female_face = make_centered_trapezoid_face(mid, alpha, 0.4, -3.2, 24.3, 30.7, 0.4, 0.0)
        female_solid = female_face.extrude(FreeCAD.Vector(0, 0, cell_len))
        cell_solid = cell_solid.cut(female_solid).removeSplitter()
        
    # 7. Perforations
    cutters_list = []
    r_pat = 2.5
    Rc_pat = 0.8
    for i in range(6):
        alpha_i, dist_i = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid_i = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        face_type = 'flat' if i in [1, 4] else 'slanted'
        
        for row in range(27):
            z_pos = 9.0 + row * 7.0
            
            if face_type == 'flat':
                u_coords = [-3.5, 3.5] if row % 2 == 0 else [-7.0, 0.0, 7.0]
            else:
                # Add central column u=0.0
                u_coords = [-23.5, 0.0, 23.5] if row % 2 == 0 else [-25.0, 0.0, 25.0]
                
            for u in u_coords:
                # Determine wall boundaries for chamfer
                if face_type == 'flat':
                    y_outer = 0.0
                    y_inner = -2.3
                else:
                    if abs(u) < 0.01:
                        if i in [0, 5]: # Tongue
                            y_outer = 3.0
                            y_inner = -2.3
                        else: # Groove
                            y_outer = -3.2
                            y_inner = -4.8
                    else: # Side holes
                        y_outer = 0.0
                        y_inner = -2.3
                        
                cutter = make_chamfered_hex_cutter(r_pat, Rc_pat, y_inner, y_outer)
                
                # Rotate and translate
                rot_ang = alpha_i - 90.0
                if abs(rot_ang) > 0.001:
                    cutter.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), rot_ang)
                
                # In make_chamfered_hex_cutter, wires are in XZ plane at Y = y_pos.
                # So we translate it by u in local X, and then by mid_i in global space!
                # Local translation of u is along local tangent t_vec.
                alpha_i_rad = math.radians(alpha_i)
                t_vec_i = FreeCAD.Vector(-math.sin(alpha_i_rad), math.cos(alpha_i_rad), 0)
                
                cutter.translate(t_vec_i * u + mid_i + FreeCAD.Vector(0, 0, z_pos))
                cutters_list.append(cutter)
                
    if cutters_list:
        all_cutters = Part.makeCompound(cutters_list)
        cell_solid = cell_solid.cut(all_cutters).removeSplitter()
        
    return cell_solid

print("Building Cell 1...")
cell1 = create_honeycomb_cell_shape()

print("Building Cell 2 (adjacent)...")
cell2 = create_honeycomb_cell_shape()

# Placement of Cell 1 and Cell 3
# Centers:
# Cell 1: (83.5, 64.0) -> rotated by -90 around X, shifted by 20.0 in Y.
# Wait! In build_cabinet.py:
# Placement is Vector(cx, 20.0, cz), rotated by -90 around X.
# Let's place them!

rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)

cell1.Placement = FreeCAD.Placement(FreeCAD.Vector(83.5, 20.0, 64.0), rot)
cell2.Placement = FreeCAD.Placement(FreeCAD.Vector(161.0, 20.0, 112.0), rot)

print("Computing intersection (overlap)...")
overlap = cell1.section(cell2)
msg_vol = f"Overlap Volume: {overlap.Volume:.6f} mm^3"
msg_area = f"Overlap Area: {overlap.Area:.6f} mm^2"
print(msg_vol)
print(msg_area)

if overlap.Volume > 1e-3:
    status = "Warning: Cells overlap!"
else:
    status = "Success: Cells fit perfectly with zero overlap volume!"
print(status)

with open("c:/3DModel/scratch/overlap_result.txt", "w", encoding="utf-8") as f:
    f.write(msg_vol + "\n" + msg_area + "\n" + status + "\n")

