# -*- coding: utf-8 -*-
"""
V2 — серпантинный защитный чехол кабеля. ВЕРСИЯ 5 (как V1 v5, но с разрезами).

Изменения v5 (по результатам печати):
  * ПЛОСКАЯ ПОДОШВА (D-сечение) на СПЛОШНОМ основании — печать БЕЗ ПОДДЕРЖЕК.
    Серпантинные разрезы идут сверху и НЕ доходят до низа (остаётся сплошная
    нижняя «лента» SPINE) — единая плоскость снизу + сегментированный рельеф.
  * ТОННЕЛЬ Ø4.1 (одинаковый с V1) + ЗУБЦЫ сверху для фиксации провода.
  * Посадка бубышки — вариант №3 (зазор 0.12/ст, R2.5).
  * ГНЕЗДО УДЛИНЕНО (бубышка/провод теперь заходят до упора).

Ось X — вдоль кабеля; ось кабеля z=0, плоская подошва z=BOTTOM. Печать пазом вверх.
"""
import os
import math

import FreeCAD as App
import Part

# --- бубышка / провод ----------------------------------------------------
BOOT_W = 10.0
BOOT_T = 6.0
GAP_BOOT = 0.12                # вариант №3
BOOT_R = 2.5
WALL = 2.0
FLOOR_B = 1.2                  # тоньше: центр тоннеля ниже, меньше общая толщина

CAV_W = BOOT_W + 2 * GAP_BOOT   # 10.24
CAV_T = BOOT_T + 2 * GAP_BOOT   # 6.24
SOCK_W = CAV_W + 2 * WALL       # 14.24
BOTTOM = -(FLOOR_B + CAV_T / 2.0)   # -5.12
SOCK_TOP = CAV_T / 2.0 + WALL       # +5.12
CAV_TOP = CAV_T / 2.0               # +3.12

BORE = 4.1
SLOT = BORE
RING_W = 11.0
CH_TOP = BORE / 2.0 + 0.85          # +2.9

# --- зоны (ГНЕЗДО УДЛИНЕНО) ----------------------------------------------
SOCK_END = 20.0                 # было 14 -> 20 (+6, чтобы провод заходил до упора)
TRANS_END = 27.0
TOTAL_L = 56.0

# --- серпантин -----------------------------------------------------------
PITCH = 4.0
RING_T = 2.2
GAP_CUT = PITCH - RING_T        # 1.8
BRIDGE_W = 2.6                  # перемычка-пружина (полные разрезы, без сплошного низа)

# --- зубцы-фиксаторы — скруглённые бугорки -------------------------------
TOOTH_R = 0.8
TOOTH_Z = 1.5                   # выше -> прижимают только верх провода
TOOTH_X = [31.0, 39.0, 47.0]    # на кольцах (между разрезами)

_PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(_PROOT, "Готовые модели", "V2 — пружина")
DOC_NAME = "CableProtector_Spring"


def dsec(x, w, zb, zt, r):
    a = w / 2.0
    r = min(r, a - 1e-3, (zt - zb) / 2.0 - 1e-3)

    def V(y, z):
        return App.Vector(x, y, z)

    d = r * math.sqrt(0.5)
    pBR, pTRs, pTRe = V(a, zb), V(a, zt - r), V(a - r, zt)
    pTLs, pTLe, pBL = V(-(a - r), zt), V(-a, zt - r), V(-a, zb)
    mTR, mTL = V(a - r + d, zt - r + d), V(-(a - r) - d, zt - r + d)
    edges = [
        Part.LineSegment(pBR, pTRs).toShape(), Part.Arc(pTRs, mTR, pTRe).toShape(),
        Part.LineSegment(pTRe, pTLs).toShape(), Part.Arc(pTLs, mTL, pTLe).toShape(),
        Part.LineSegment(pTLe, pBL).toShape(), Part.LineSegment(pBL, pBR).toShape(),
    ]
    return Part.Wire(edges)


def rrect_wire(x, w, h, r):
    a, b = w / 2.0, h / 2.0
    r = min(r, a - 1e-3, b - 1e-3)

    def V(y, z):
        return App.Vector(x, y, z)

    p1, p2 = V(a, -(b - r)), V(a, (b - r))
    p3, p4 = V(a - r, b), V(-(a - r), b)
    p5, p6 = V(-a, b - r), V(-a, -(b - r))
    p7, p8 = V(-(a - r), -b), V((a - r), -b)
    d = r * math.sqrt(0.5)
    mTR, mTL = V(a - r + d, b - r + d), V(-(a - r) - d, b - r + d)
    mBL, mBR = V(-(a - r) - d, -(b - r) - d), V(a - r + d, -(b - r) - d)
    edges = [
        Part.LineSegment(p1, p2).toShape(), Part.Arc(p2, mTR, p3).toShape(),
        Part.LineSegment(p3, p4).toShape(), Part.Arc(p4, mTL, p5).toShape(),
        Part.LineSegment(p5, p6).toShape(), Part.Arc(p6, mBL, p7).toShape(),
        Part.LineSegment(p7, p8).toShape(), Part.Arc(p8, mBR, p1).toShape(),
    ]
    return Part.Wire(edges)


def circle_wire(x, d):
    c = Part.Circle(App.Vector(x, 0, 0), App.Vector(1, 0, 0), d / 2.0)
    return Part.Wire([c.toShape()])


def rect_wire(x, w, z0, z1):
    a = w / 2.0
    p = [App.Vector(x, -a, z0), App.Vector(x, a, z0),
         App.Vector(x, a, z1), App.Vector(x, -a, z1)]
    e = [Part.LineSegment(p[i], p[(i + 1) % 4]).toShape() for i in range(4)]
    return Part.Wire(e)


def loft(wires):
    return Part.makeLoft(wires, True, True)


def tooth(xc):
    a = Part.makeSphere(TOOTH_R, App.Vector(xc, SLOT / 2.0, TOOTH_Z))
    b = Part.makeSphere(TOOTH_R, App.Vector(xc, -SLOT / 2.0, TOOTH_Z))
    return a.fuse(b)


def build():
    outer = loft([
        dsec(0.0,       SOCK_W, BOTTOM, SOCK_TOP, 2.5),
        dsec(SOCK_END,  SOCK_W, BOTTOM, SOCK_TOP, 2.5),
        dsec(TRANS_END, RING_W, BOTTOM, CH_TOP,   2.5),
        dsec(TOTAL_L,   RING_W, BOTTOM, CH_TOP,   2.5),
    ])
    inner = loft([
        rrect_wire(-0.5,      CAV_W, CAV_T, BOOT_R),
        rrect_wire(SOCK_END,  CAV_W, CAV_T, BOOT_R),
        circle_wire(TRANS_END, BORE),
        circle_wire(TOTAL_L + 0.5, BORE),
    ])
    body = outer.cut(inner)

    # КРЫША над гнездом + сплошная прорезь SLOT(4.1) по всей длине (без уступа,
    # без перегородок): бубышка с торца под крышу, провод в прорезь сверху.
    ZH = SOCK_TOP + 1.0
    slot = Part.makeBox(TOTAL_L + 1.5, SLOT, ZH, App.Vector(-0.5, -SLOT / 2.0, 0.0))
    body = body.cut(slot)

    # серпантинные разрезы НАСКВОЗЬ (полная пружина, без сплошного низа)
    zc0 = BOTTOM - 1.0
    zcut = CH_TOP + 2.0 - zc0
    x = TRANS_END + PITCH / 2.0
    side = 0
    big = RING_W + 6.0
    n = 0
    while x < TOTAL_L - 0.5:
        if side == 0:
            y0 = -RING_W / 2.0 + BRIDGE_W
            cut = Part.makeBox(GAP_CUT, big, zcut, App.Vector(x - GAP_CUT / 2.0, y0, zc0))
        else:
            y1 = RING_W / 2.0 - BRIDGE_W
            cut = Part.makeBox(GAP_CUT, big, zcut, App.Vector(x - GAP_CUT / 2.0, y1 - big, zc0))
        body = body.cut(cut)
        n += 1
        side ^= 1
        x += PITCH

    for xc in TOOTH_X:
        body = body.fuse(tooth(xc))
    body = body.removeSplitter()
    App.Console.PrintMessage("Серпантинных разрезов: %d\n" % n)
    return body


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = App.newDocument(DOC_NAME)
    shape = build()
    if not shape.isValid():
        App.Console.PrintWarning("Невалидно — чиню...\n")
        shape.fix(1e-6, 1e-6, 1e-6)
    bb = shape.BoundBox
    App.Console.PrintMessage(
        "Валидно: %s | тел: %d | объём: %.1f | габарит: %.1f x %.1f x %.1f | низ z=%.2f\n"
        % (shape.isValid(), len(shape.Solids), shape.Volume,
           bb.XLength, bb.YLength, bb.ZLength, bb.ZMin))

    obj = doc.addObject("Part::Feature", DOC_NAME)
    obj.Shape = shape
    doc.recompute()
    fcstd = os.path.join(OUTPUT_DIR, DOC_NAME + ".FCStd")
    step = os.path.join(OUTPUT_DIR, DOC_NAME + ".step")
    stl = os.path.join(OUTPUT_DIR, DOC_NAME + ".stl")
    doc.saveAs(fcstd)
    shape.exportStep(step)
    import MeshPart
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.04,
                               AngularDeflection=0.3, Relative=False)
    m.write(stl)
    App.Console.PrintMessage("Экспорт: FCStd / STL / STEP в %s\n" % OUTPUT_DIR)


main()
