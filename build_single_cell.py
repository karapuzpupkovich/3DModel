import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from honeycomb_cell.export_single_cell import main as _honeycomb_main

_honeycomb_main()
raise SystemExit

import os
import sys
import math

print("="*60)
print("  Building single honeycomb cell (debug mode)")
print("="*60)

try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: Must run from FreeCAD environment")
    sys.exit(1)

doc = FreeCAD.newDocument("SingleCell")

# =============================================
# ПАРАМЕТРЫ ЯЧЕЙКИ
# =============================================

# Внешний контур шестигранника
r_out = 48.0       # половина высоты (расстояние от центра до плоской грани)
b_out = 15.0       # половина ширины плоской грани
a_out = 62.5       # половина ширины по вершинам
R_c_out = 6.0      # радиус скругления углов шестигранника
cell_len = 200.0   # длина ячейки (глубина шкафчика)
wall_t = 2.3       # толщина стенки

# Гребень (Male joint) — v1..v2 по нормали к грани, w1..w2 по касательной
MALE_V1 = -0.5     # начало гребня (0.5мм внутри стенки для надёжного слияния)
MALE_V2 = 3.0      # кончик гребня (3мм наружу)
MALE_W1 = 24.0     # ширина основания гребня (при v1)
MALE_W2 = 31.0     # ширина кончика гребня (при v2)
MALE_R_TIP = 0.4   # скругление кончика гребня

# Паз (Female joint) — ширина должна быть чуть шире гребня для зазора
# Гребень при v=0: w = 24 + 7*0.5/3.5 = 25.0мм → паз = 25.6мм (зазор 0.3мм/сторону)
# Гребень при v=3.0: w = 31.0мм → паз при глубине 3.0 должен быть 31.6мм
FEMALE_W_BASE = 25.6    # ширина паза у поверхности стенки
FEMALE_W_TIP = 32.0     # ширина паза на дне
FEMALE_DEPTH = 3.2      # глубина паза (чуть больше высоты гребня для зазора)

# Усилительная площадка под пазом
REINF_V1 = -wall_t      # -2.3мм (от внутренней поверхности стенки)
REINF_V2 = -4.8          # до -4.8мм (вглубь)
REINF_W1 = 58.0          # ширина у стенки (расширена на 5мм с каждой стороны)
REINF_W2 = 48.0          # ширина на внутреннем краю
REINF_R = 3.0            # скругление краёв площадки

# Перфорация
PERF_R = 2.5             # радиус отверстия
PERF_RC = 0.8            # скругление углов шестигранного отверстия
PERF_SPACING_Z = 7.0     # шаг по длине (Z)
PERF_SPACING_U = 7.0     # шаг по ширине грани (U)
PERF_EDGE_MIN = 7.5      # мин. отступ от края грани (5мм + радиус отверстия 2.5мм)
PERF_CHAMFER = 0.4       # глубина фаски на перфорации
PERF_GROOVE_MIN = 20.0   # мин. отступ от центра грани на пазовых гранях (чтобы не попасть в паз)
PERF_ROWS = 27           # количество рядов перфорации
PERF_Z_START = 9.0       # начальная позиция первого ряда

# Торцевое скругление
END_FILLET_R = 0.8

ENABLE_PERFORATION = True

# =============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================

def get_face_angle_and_dist(i, a, b, r):
    """Возвращает угол и расстояние до грани i шестигранника."""
    theta_0 = math.degrees(math.atan2(a - b, r))
    if   i == 0: return theta_0,           a * math.cos(math.radians(theta_0))
    elif i == 1: return 90.0,              r
    elif i == 2: return 180.0 - theta_0,   a * math.cos(math.radians(theta_0))
    elif i == 3: return 180.0 + theta_0,   a * math.cos(math.radians(theta_0))
    elif i == 4: return 270.0,             r
    elif i == 5: return 360.0 - theta_0,   a * math.cos(math.radians(theta_0))


def make_filleted_polygon_with_radii(vertices, radii):
    """Создаёт замкнутый контур (Wire) из вершин с индивидуальными радиусами скругления."""
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
    """Создаёт трапецеидальное сечение: основание w1 при v1, верхушка w2 при v2."""
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
    """Создаёт Face из вершин с одинаковым радиусом скругления."""
    wire = make_filleted_polygon_with_radii(vertices, [Rc] * len(vertices))
    return Part.Face(wire)


def make_filleted_hex_wire(R, y_pos, Rc):
    """Создаёт скруглённый шестигранный Wire в плоскости XZ на высоте y_pos."""
    points = []
    for i in range(6):
        ang = math.radians(i * 60)
        points.append(FreeCAD.Vector(R * math.cos(ang), y_pos, R * math.sin(ang)))
    n = len(points)
    p_in = [None] * n
    p_out = [None] * n
    arcs_list = [None] * n
    for i in range(n):
        v = points[i]
        v_prev = points[(i - 1) % n]
        v_next = points[(i + 1) % n]
        t1 = (v_prev - v).normalize()
        t2 = (v_next - v).normalize()
        dot_val = max(-1.0, min(1.0, t1.dot(t2)))
        theta = math.acos(dot_val)
        half_theta = theta / 2.0
        d = Rc / math.sin(half_theta)
        cot_val = 1.0 / math.tan(half_theta)
        bisector = (t1 + t2).normalize()
        p_in[i] = v + t1 * (Rc * cot_val)
        p_out[i] = v + t2 * (Rc * cot_val)
        pmid = v + bisector * (d - Rc)
        arcs_list[i] = Part.Arc(p_in[i], pmid, p_out[i]).toShape()
    all_edges = []
    for i in range(n):
        all_edges.append(arcs_list[i])
        p_start = p_out[i]
        p_end = p_in[(i + 1) % n]
        if (p_start - p_end).Length > 1e-5:
            all_edges.append(Part.makeLine(p_start, p_end))
    return Part.Wire(all_edges)


def make_chamfered_hex_cutter(R, Rc, y_inner, y_outer, chamfer=0.4):
    """Создаёт шестигранный каттер с фасками на обеих поверхностях.
    
    Профиль (вдоль Y):
      y_inner-5 ... y_inner:     R+chamfer (расширенный, за пределами)
      y_inner ... y_inner+chamfer: R+chamfer → R (фаска внутренней поверхности)
      y_inner+chamfer ... y_outer-chamfer: R (основное отверстие)
      y_outer-chamfer ... y_outer: R → R+chamfer (фаска наружной поверхности)
      y_outer ... y_outer+5:     R+chamfer (расширенный, за пределами)
    """
    w1 = make_filleted_hex_wire(R + chamfer, y_inner - 5.0, Rc)
    w2 = make_filleted_hex_wire(R + chamfer, y_inner, Rc)
    w3 = make_filleted_hex_wire(R, y_inner + chamfer, Rc)
    w4 = make_filleted_hex_wire(R, y_outer - chamfer, Rc)
    w5 = make_filleted_hex_wire(R + chamfer, y_outer, Rc)
    w6 = make_filleted_hex_wire(R + chamfer, y_outer + 5.0, Rc)
    return Part.makeLoft([w1, w2, w3, w4, w5, w6], True, True)


def make_female_cutter_face(mid, alpha_deg, w_base, w_tip, depth):
    """Создаёт профиль каттера паза с крылышками и скруглёнными входными углами.
    
    Профиль (6 точек):
      p1 — крыло слева (шире основания, снаружи стенки)
      p2 — край паза слева (у поверхности стенки)
      p3 — дно паза слева (глубже)
      p4 — дно паза справа
      p5 — край паза справа (у поверхности)
      p6 — крыло справа
    
    Скругление R=1.0 на p2/p5 для плавного входа в паз.
    """
    alpha = math.radians(alpha_deg)
    n_vec = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    t_vec = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    p1 = mid - t_vec * (w_base / 2.0 + 2.0) + n_vec * 1.0
    p2 = mid - t_vec * (w_base / 2.0)        + n_vec * 0.0
    p3 = mid - t_vec * (w_tip / 2.0)         + n_vec * (-depth)
    p4 = mid + t_vec * (w_tip / 2.0)         + n_vec * (-depth)
    p5 = mid + t_vec * (w_base / 2.0)        + n_vec * 0.0
    p6 = mid + t_vec * (w_base / 2.0 + 2.0)  + n_vec * 1.0
    vertices = [p1, p2, p3, p4, p5, p6]
    radii = [0.0, 1.0, 0.0, 0.0, 1.0, 0.0]
    wire = make_filleted_polygon_with_radii(vertices, radii)
    return Part.Face(wire)


# =============================================
# ПОСТРОЕНИЕ ЯЧЕЙКИ
# =============================================

def create_honeycomb_cell_shape():
    vertices_out = [
        FreeCAD.Vector(a_out, 0, 0),          # 0 — правая вершина
        FreeCAD.Vector(b_out, r_out, 0),      # 1 — верх-право
        FreeCAD.Vector(-b_out, r_out, 0),     # 2 — верх-лево
        FreeCAD.Vector(-a_out, 0, 0),         # 3 — левая вершина
        FreeCAD.Vector(-b_out, -r_out, 0),    # 4 — низ-лево
        FreeCAD.Vector(b_out, -r_out, 0)      # 5 — низ-право
    ]

    # ═══════════════════════════════════════
    # Шаг 1: Внешний и внутренний контуры → полая оболочка
    # ═══════════════════════════════════════
    print("  [1/7] Creating hex shell...")
    outer_face = make_filleted_polygon(vertices_out, R_c_out)
    inner_face = outer_face.makeOffset2D(-wall_t)
    clean_cell_face = outer_face.cut(inner_face).removeSplitter()

    # ═══════════════════════════════════════
    # Шаг 2: Выдавливание на длину ячейки
    # ═══════════════════════════════════════
    print("  [2/7] Extruding cell body...")
    clean_cell_solid = clean_cell_face.extrude(FreeCAD.Vector(0, 0, cell_len))

    # ═══════════════════════════════════════
    # Шаг 3: Скругление торцов базового шестигранника (R=0.8мм)
    #         Применяем ДО добавления гребней/пазов — так надёжнее
    # ═══════════════════════════════════════
    print("  [3/7] Filleting end edges...")
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

    cell_solid = clean_cell_solid.makeFillet(END_FILLET_R, end_edges_to_fillet)
    print(f"         Filleted {len(end_edges_to_fillet)} end edges")

    # ═══════════════════════════════════════
    # Шаг 4: Усилительные площадки под пазами (грани 2,3)
    # ═══════════════════════════════════════
    print("  [4/7] Adding reinforcement plates...")
    for i in [2, 3]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i + 1) % 6]) * 0.5
        reinf_face = make_centered_trapezoid_face(
            mid, alpha, REINF_V1, REINF_V2, REINF_W1, REINF_W2, REINF_R, REINF_R
        )
        reinf_solid = reinf_face.extrude(FreeCAD.Vector(0, 0, cell_len))
        cell_solid = cell_solid.fuse(reinf_solid).removeSplitter()

    # ═══════════════════════════════════════
    # Шаг 5: Гребни (Male joints) на гранях 0, 5
    #         С 45° срезами на торцах для совпадения со скруглением
    # ═══════════════════════════════════════
    print("  [5/7] Adding ridges (male joints)...")
    for i in [0, 5]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i + 1) % 6]) * 0.5

        # Строим гребень в локальных координатах (ось нормали = Y)
        male_face = make_centered_trapezoid_face(
            FreeCAD.Vector(0, 0, 0), 90.0,
            MALE_V1, MALE_V2, MALE_W1, MALE_W2,
            0.0, MALE_R_TIP
        )
        male_solid = male_face.extrude(FreeCAD.Vector(0, 0, cell_len))

        # 45° срезы на торцах — гребень начинается на расстоянии END_FILLET_R от торца
        box_start = Part.makeBox(100.0, 100.0, 100.0)
        box_start.translate(FreeCAD.Vector(-50.0, -50.0, -100.0))
        box_start.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 45.0)
        box_start.translate(FreeCAD.Vector(0, 0, END_FILLET_R))

        box_end = Part.makeBox(100.0, 100.0, 100.0)
        box_end.translate(FreeCAD.Vector(-50.0, -50.0, 0.0))
        box_end.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -45.0)
        box_end.translate(FreeCAD.Vector(0, 0, cell_len - END_FILLET_R))

        male_solid = male_solid.cut(box_start).cut(box_end)

        # Поворот и перенос в глобальные координаты
        male_solid.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), alpha - 90.0)
        male_solid.translate(mid)

        cell_solid = cell_solid.fuse(male_solid).removeSplitter()

    # ═══════════════════════════════════════
    # Шаг 6: Пазы (Female joints) на гранях 2, 3
    #         С скруглёнными входными углами (R=1.0мм)
    # ═══════════════════════════════════════
    print("  [6/7] Cutting grooves (female joints)...")
    for i in [2, 3]:
        alpha, dist = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid = (vertices_out[i] + vertices_out[(i + 1) % 6]) * 0.5
        female_face = make_female_cutter_face(mid, alpha, FEMALE_W_BASE, FEMALE_W_TIP, FEMALE_DEPTH)
        female_solid = female_face.extrude(FreeCAD.Vector(0, 0, cell_len))
        cell_solid = cell_solid.cut(female_solid).removeSplitter()

    if not ENABLE_PERFORATION:
        return cell_solid

    # ═══════════════════════════════════════
    # Шаг 7: Перфорация с фаской на всех гранях
    # ═══════════════════════════════════════
    print("  [7/7] Creating perforation holes...")
    cutters_list = []

    # Вычисляем полуширину каждой грани для правильного размещения отверстий
    face_half_lengths = {}
    for i in range(6):
        v_i = vertices_out[i]
        v_next = vertices_out[(i + 1) % 6]
        face_half_lengths[i] = (v_i - v_next).Length / 2.0

    # Полуширина гребня для определения типа отверстия
    ridge_half_w = MALE_W1 / 2.0  # 12мм

    total_holes = 0
    for i in range(6):
        alpha_i, dist_i = get_face_angle_and_dist(i, a_out, b_out, r_out)
        mid_i = (vertices_out[i] + vertices_out[(i + 1) % 6]) * 0.5

        is_flat = i in [1, 4]
        is_ridge = i in [0, 5]
        is_groove = i in [2, 3]

        half_len = face_half_lengths[i]
        max_u = half_len - PERF_EDGE_MIN  # максимальный u от центра

        face_holes = 0
        for row in range(PERF_ROWS):
            z_pos = PERF_Z_START + row * PERF_SPACING_Z

            # Генерируем u-координаты в шахматном порядке
            u_list = []
            if row % 2 == 0:
                # Чётные ряды: 0, ±7, ±14, ±21, ...
                u = 0.0
                while u <= max_u + 0.1:
                    u_list.append(u)
                    if u > 0.01:
                        u_list.append(-u)
                    u += PERF_SPACING_U
            else:
                # Нечётные ряды: ±3.5, ±10.5, ±17.5, ...
                u = PERF_SPACING_U / 2.0  # 3.5
                while u <= max_u + 0.1:
                    u_list.append(u)
                    u_list.append(-u)
                    u += PERF_SPACING_U

            for u in u_list:
                # Проверка: не выходит ли за границы грани
                if abs(u) > max_u:
                    continue

                # Проверка: не попадает ли в зону паза (пропускаем)
                if is_groove and abs(u) < PERF_GROOVE_MIN:
                    continue

                # Определяем толщину материала в данной точке
                if is_ridge and abs(u) <= ridge_half_w:
                    # Отверстие через гребень: от кончика гребня до внутренней стенки
                    y_outer = MALE_V2       # 3.0
                    y_inner = -wall_t       # -2.3
                else:
                    # Обычное отверстие через стенку
                    y_outer = 0.0
                    y_inner = -wall_t       # -2.3

                # Создаём каттер с фаской
                cutter = make_chamfered_hex_cutter(PERF_R, PERF_RC, y_inner, y_outer, PERF_CHAMFER)

                # Поворачиваем каттер по нормали к грани
                rot_ang = alpha_i - 90.0
                if abs(rot_ang) > 0.001:
                    cutter.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), rot_ang)

                # Сдвигаем по касательному вектору (u) и к центру грани
                alpha_i_rad = math.radians(alpha_i)
                t_vec_i = FreeCAD.Vector(-math.sin(alpha_i_rad), math.cos(alpha_i_rad), 0)
                cutter.translate(t_vec_i * u + mid_i + FreeCAD.Vector(0, 0, z_pos))

                cutters_list.append(cutter)
                face_holes += 1

        total_holes += face_holes
        face_name = "flat" if is_flat else ("ridge" if is_ridge else "groove")
        print(f"         Face {i} ({face_name}): {face_holes} holes")

    print(f"         Total holes: {total_holes}")

    if cutters_list:
        print("         Cutting all holes (boolean operation)...")
        all_cutters = Part.makeCompound(cutters_list)
        cell_solid = cell_solid.cut(all_cutters).removeSplitter()

    return cell_solid


# =============================================
# СБОРКА И СОХРАНЕНИЕ
# =============================================

cell_shape = create_honeycomb_cell_shape()

obj = doc.addObject("Part::Feature", "HoneycombCell")
obj.Shape = cell_shape
if obj.ViewObject:
    obj.ViewObject.ShapeColor = (0.75, 0.75, 0.78)

doc.recompute()

# Сохраняем
save_path = r"C:\3DModel\SingleCell.FCStd"
doc.saveAs(save_path)
print(f"\nSingle cell saved to: {save_path}")
print("="*60)
