import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from honeycomb_cell.cabinet_builder import main as _cabinet_main

_cabinet_main()
raise SystemExit

import os
import sys
import math

print("Starting cabinet model generation inside FreeCAD...")

try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: FreeCAD and Part modules must be loaded from within FreeCAD environment.")
    sys.exit(1)

# 1. Создаем новый документ
doc = FreeCAD.newDocument("NikitasCabinet")

# 2. Создаем управляющую таблицу (Spreadsheet) для параметров
sheet = doc.addObject("Spreadsheet::Sheet", "Spreadsheet")
sheet.set("B1", "0")
sheet.setAlias("B1", "DoorAngle")

# Размеры шкафчика (в мм)
W = 322       # Внешняя ширина (290 мм внутренняя ширина + 2 * 16 мм стенки)
H = 1295      # Внешняя высота корпуса (без ножек)
D = 350       # Внешняя глубина
t = 16        # Толщина ЛДСП
leg_h = 100   # Высота ножек

# Внутренние высоты отделений
h_headwear = 150
h_spare = 115
h_outerwear = 750
h_shoes = 200

# Цвета для визуализации (RGB кортежи)
wood_color = (0.91, 0.84, 0.72)      # Цвет светлого дерева
leg_color = (0.3, 0.3, 0.3)          # Темно-серый для ножек
door_color = (0.95, 0.95, 0.95)       # Светлый/белый для двери

# Разноцветные соты для красоты и детского восприятия (яркие цвета)
cell_colors = [
    (0.95, 0.75, 0.15),  # Желтый (Ячейка 1)
    (0.85, 0.35, 0.25),  # Терракотовый/Красный (Ячейка 2)
    (0.35, 0.65, 0.55),  # Бирюзовый (Ячейка 3)
    (0.85, 0.55, 0.15),  # Оранжевый (Ячейка 4)
    (0.45, 0.75, 0.35),  # Салатовый/Зеленый (Ячейка 5)
]

# Функция для быстрого создания панелей
def add_panel(name, length, width, height, x, y, z, color):
    obj = doc.addObject("Part::Box", name)
    obj.Length = length
    obj.Width = width
    obj.Height = height
    obj.Placement = FreeCAD.Placement(FreeCAD.Vector(x, y, z), FreeCAD.Rotation(0, 0, 0))
    if obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj

# Боковые стенки
left_wall = add_panel("LeftWall", t, D, H, 0, 0, 0, wood_color)
right_wall = add_panel("RightWall", t, D, H, W - t, 0, 0, wood_color)

# Топ и Дно
top_panel = add_panel("TopPanel", W - 2*t, D, t, t, 0, H - t, wood_color)
bottom_panel = add_panel("BottomPanel", W - 2*t, D, t, t, 0, 0, wood_color)

# Задняя стенка (вкладная, 16мм для прочности модели)
back_panel = add_panel("BackWall", W - 2*t, t, H - 2*t, t, D - t, t, wood_color)

# Полки
shelf_1 = add_panel("Shelf1_Headwear", W - 2*t, D - t, t, t, 0, H - t - h_headwear - t, wood_color)
shelf_2 = add_panel("Shelf2_Spare", W - 2*t, D - t, t, t, 0, H - t - h_headwear - t - h_spare - t, wood_color)
shelf_3 = add_panel("Shelf3_Shoes", W - 2*t, D - t, t, t, 0, t + h_shoes, wood_color)

# Ножки (4 штуки)
leg1 = add_panel("Leg1", 30, 30, leg_h, 20, 20, -leg_h, leg_color)
leg2 = add_panel("Leg2", 30, 30, leg_h, W - 50, 20, -leg_h, leg_color)
leg3 = add_panel("Leg3", 30, 30, leg_h, 20, D - 50, -leg_h, leg_color)
leg4 = add_panel("Leg4", 30, 30, leg_h, W - 50, D - 50, -leg_h, leg_color)

# Дверца (выставим перед шкафчиком, привяжем ее открытие к Spreadsheet.DoorAngle)
door = doc.addObject("Part::Box", "Door")
door.Length = W - 4
door.Width = t
door.Height = H - 4
door.Placement = FreeCAD.Placement(FreeCAD.Vector(2, 0, 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, -1), 0))
if door.ViewObject:
    door.ViewObject.ShapeColor = door_color
    door.ViewObject.Transparency = 50

# Привязываем угол вращения двери к таблице
door.setExpression("Placement.Rotation.Angle", "Spreadsheet.DoorAngle")

# ==========================================
# ПРОЕКТИРОВАНИЕ СОТОВОГО ОРГАНАЙЗЕРА ОБУВИ
# ==========================================

ENABLE_PERFORATION = True

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

def local_to_global(u, v, alpha):
    x = -u * math.sin(alpha) + v * math.cos(alpha)
    y = u * math.cos(alpha) + v * math.sin(alpha)
    return FreeCAD.Vector(x, y, 0)

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
    w2 = make_filleted_hex_wire(R + chamfer_dist, y_inner, Rc)
    w3 = make_filleted_hex_wire(R, y_inner + chamfer_dist, Rc)
    w4 = make_filleted_hex_wire(R, y_outer - chamfer_dist, Rc)
    w5 = make_filleted_hex_wire(R + chamfer_dist, y_outer, Rc)
    w6 = make_filleted_hex_wire(R + chamfer_dist, y_outer + 5.0, Rc)
    return Part.makeLoft([w1, w2, w3, w4, w5, w6], True, True)

def make_female_cutter_face(mid, alpha_deg, w_base, w_tip, depth):
    alpha = math.radians(alpha_deg)
    n_vec = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    t_vec = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    p1 = mid - t_vec * (w_base/2.0 + 2.0) + n_vec * 1.0
    p2 = mid - t_vec * (w_base/2.0)       + n_vec * 0.0
    p3 = mid - t_vec * (w_tip/2.0)        + n_vec * (-depth)
    p4 = mid + t_vec * (w_tip/2.0)        + n_vec * (-depth)
    p5 = mid + t_vec * (w_base/2.0)       + n_vec * 0.0
    p6 = mid + t_vec * (w_base/2.0 + 2.0) + n_vec * 1.0
    vertices = [p1, p2, p3, p4, p5, p6]
    radii = [0.0, 1.0, 0.0, 0.0, 1.0, 0.0]
    wire = make_filleted_polygon_with_radii(vertices, radii)
    return Part.Face(wire)

def create_honeycomb_cell_shape():
    vertices_out = [
        FreeCAD.Vector(a_out, 0, 0),
        FreeCAD.Vector(b_out, r_out, 0),
        FreeCAD.Vector(-b_out, r_out, 0),
        FreeCAD.Vector(-a_out, 0, 0),
        FreeCAD.Vector(-b_out, -r_out, 0),
        FreeCAD.Vector(b_out, -r_out, 0)
    ]
    
    # 1. Создаем внешний контур соты (face)
    outer_face = make_filleted_polygon(vertices_out, R_c_out)
    
    # 2. Создаем внутренний контур с помощью 2D-смещения (offset) для абсолютно равномерной стенки 2.3мм
    inner_face_no_reinf = outer_face.makeOffset2D(-2.3)
    clean_cell_face = outer_face.cut(inner_face_no_reinf).removeSplitter()
    
    # Выдавливаем базовое тело соты
    clean_cell_solid = clean_cell_face.extrude(FreeCAD.Vector(0, 0, cell_len))
    cell_solid = clean_cell_solid
    
    # 4. Добавляем внутренние усилительные площадки под пазы
    reinf_solids = []
    for i in [2, 3]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        reinf_face = make_centered_trapezoid_face(mid, alpha, -2.3, -4.8, 58.0, 48.0, 3.0, 3.0)
        reinf_solid = reinf_face.extrude(FreeCAD.Vector(0, 0, cell_len))
        reinf_solids.append(reinf_solid)
        
    for rs in reinf_solids:
        cell_solid = cell_solid.fuse(rs).removeSplitter()
        
    # 5. Добавляем гребни (Male) - шипы скруглены по вершине R_tip=1.0мм
    for i in [0, 5]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        
        # Строим гребень в локальных координатах
        male_face_local = make_centered_trapezoid_face(FreeCAD.Vector(0,0,0), 90.0, -0.5, 3.0, 30.0, 38.0, 0.0, 1.0)
        male_solid_local = male_face_local.extrude(FreeCAD.Vector(0, 0, cell_len))
        
        # Поворачиваем и перемещаем в глобальную позицию
        male_solid_local.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), alpha - 90.0)
        male_solid_local.translate(mid)
        
        cell_solid = cell_solid.fuse(male_solid_local).removeSplitter()
        
    # 6. Вырезаем пазы (Female) - входные углы скруглены R_base=1.0мм, дно паза sharp, сдвинуто к v1 = 1.0мм
    for i in [2, 3]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i+1)%6]) * 0.5
        female_face = make_female_cutter_face(mid, alpha, 31.3, 39.7, 3.2)
        female_solid = female_face.extrude(FreeCAD.Vector(0, 0, cell_len))
        cell_solid = cell_solid.cut(female_solid).removeSplitter()
        
    # 6.5 Скругляем все торцы модели (включая гребни и пазы) R=0.8мм
    end_edges_to_fillet = []
    for e in cell_solid.Edges:
        bbox = e.BoundBox
        if (bbox.ZMax < 0.01 and bbox.ZMin > -0.01) or (bbox.ZMax < cell_len + 0.01 and bbox.ZMin > cell_len - 0.01):
            end_edges_to_fillet.append(e)
            
    if end_edges_to_fillet:
        try:
            cell_solid = cell_solid.makeFillet(0.8, end_edges_to_fillet)
        except Exception as e:
            print(f"Warning: Global end fillet failed: {e}")
        
    if not ENABLE_PERFORATION:
        return cell_solid
        
    # 7. Выполняем перфорацию с учетом скругления и конических фасок
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
                # Добавляем ряды отверстий только на гребнях/пазах
                u_coords = [-3.5, 3.5] if row % 2 == 0 else [-7.0, 0.0, 7.0]
                
            for u in u_coords:
                # Рассчитываем координаты внешней и внутренней границ стенки
                if face_type == 'flat':
                    y_outer = 0.0
                    y_inner = -2.3
                else:
                    if i in [0, 5]: # Гребень
                        y_outer = 3.0
                        y_inner = -2.3
                    else: # Паз
                        y_outer = -3.2
                        y_inner = -4.8
                        
                cutter = make_chamfered_hex_cutter(r_pat, Rc_pat, y_inner, y_outer)
                
                rot_ang = alpha_i - 90.0
                if abs(rot_ang) > 0.001:
                    cutter.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), rot_ang)
                    
                # Локальный сдвиг u идет по тангенциальному вектору грани t_vec
                alpha_i_rad = math.radians(alpha_i)
                t_vec_i = FreeCAD.Vector(-math.sin(alpha_i_rad), math.cos(alpha_i_rad), 0)
                
                cutter.translate(t_vec_i * u + mid_i + FreeCAD.Vector(0, 0, z_pos))
                cutters_list.append(cutter)
                
    if cutters_list:
        all_cutters = Part.makeCompound(cutters_list)
        cell_solid = cell_solid.cut(all_cutters).removeSplitter()
        return cell_solid
    else:
        return cell_solid

# Создаем геометрию соты
cell_shape = create_honeycomb_cell_shape()

# Координаты для идеального размещения 5 сот в шахматном порядке (с учетом a_out=62.5 и r_out=48.0)
# Центр шкафчика по ширине X = 161.0мм (290мм внутренняя ширина + 16мм стенка)
centers = [
    ("ShoeCell_1", 83.5, 64.0),                             #  Колонка 0, снизу
    ("ShoeCell_2", 83.5, 160.0),                            #  Колонка 0, сверху
    ("ShoeCell_3", 161.0, 112.0),                           #  Колонка 1, по центру
    ("ShoeCell_4", 238.5, 64.0),                            #  Колонка 2, снизу
    ("ShoeCell_5", 238.5, 160.0)                            #  Колонка 2, сверху
]

cells_list = []
for idx, (name, cx, cz) in enumerate(centers):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = cell_shape.copy()
    
    # Все ячейки абсолютно идентичны и ориентированы одинаково (без вращения вокруг оси Y, так как верх и низ плоские):
    # Достаточно повернуть на -90 градусов вокруг X, чтобы длина Z встала вдоль глубины Y шкафчика.
    rot_std = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)
    obj.Placement = FreeCAD.Placement(FreeCAD.Vector(cx, 20.0, cz), rot_std)
    
    if obj.ViewObject:
        obj.ViewObject.ShapeColor = cell_colors[idx]
    cells_list.append(obj)

# ==========================================
# СБОРКА И СОХРАНЕНИЕ
# ==========================================

cabinet_group = doc.addObject("App::DocumentObjectGroup", "CabinetAssembly")
cabinet_group.Label = "Сборка Шкафчика"
all_parts = [left_wall, right_wall, top_panel, bottom_panel, back_panel, shelf_1, shelf_2, shelf_3, leg1, leg2, leg3, leg4, door]
all_parts.extend(cells_list)

for obj in all_parts:
    cabinet_group.addObject(obj)

doc.recompute()

try:
    import FreeCADGui as Gui
    if Gui.activeDocument() and Gui.activeDocument().activeView():
        Gui.activeDocument().activeView().viewIsometric()
        Gui.activeDocument().activeView().fitAll()
except Exception as e:
    pass

# Сохраняем проект
save_dir = r"C:\3DModel\Шкафчик Никиты (Сказка м.г.)"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
save_path = os.path.join(save_dir, "Cabinet.FCStd")
doc.saveAs(save_path)
print(f"Model saved successfully to: {save_path}")
