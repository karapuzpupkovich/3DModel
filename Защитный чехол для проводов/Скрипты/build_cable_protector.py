# -*- coding: utf-8 -*-
"""
Защитный чехол-фиксатор зарядного кабеля (USB-C, iPhone 16 / MacBook). ВЕРСИЯ 5.

Изменения v5 (по результатам печати v2):
  * ПЛОСКАЯ ПОДОШВА снизу (D-сечение: низ плоский, верх скруглён) — деталь
    устойчиво стоит на столе, печатается БЕЗ ПОДДЕРЖЕК.
  * ТОННЕЛЬ Ø4.1 — прямой, БЕЗ перегородок и без расширения (одинаковый с V2).
  * Крепёж провода — ЗУБЦЫ сверху у кромок паза (а не перегородки): провод
    проталкивается мимо них в тоннель и слегка прижат сверху; внутри тоннеля
    зубцов нет, поверхность гладкая.
  * Посадка бубышки — вариант №3 (зазор 0.12/ст, R2.5) — выбран по образцам.

Ось X — вдоль кабеля (X=0 — передний открытый торец, бубышка торчит наружу).
Ось Y — ширина, Z — толщина. Ось кабеля z=0, плоская подошва z=BOTTOM.
Печать ПАЗОМ ВВЕРХ, плоской подошвой на стол.

Запуск:
  "C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" build_cable_protector.py
"""
import os
import math

import FreeCAD as App
import Part

# --------------------------------------------------------------------------
# ПАРАМЕТРЫ (мм)
# --------------------------------------------------------------------------
BOOT_W = 10.0          # ширина бубышки (Y)
BOOT_T = 6.0           # толщина бубышки (Z)
CABLE_D = 4.0          # диаметр провода

GAP_BOOT = 0.12        # зазор вокруг бубышки на сторону (вариант №3)
BOOT_R = 2.5           # скругление гнезда
WALL = 2.0
FLOOR_B = 2.0          # толщина дна под гнездом

CAV_W = BOOT_W + 2 * GAP_BOOT      # 10.24
CAV_T = BOOT_T + 2 * GAP_BOOT      # 6.24
SOCK_W = CAV_W + 2 * WALL          # 14.24
BOTTOM = -(FLOOR_B + CAV_T / 2.0)  # -5.12  плоская подошва
SOCK_TOP = CAV_T / 2.0 + WALL      # +5.12

BORE = 4.1             # тоннель под провод (одинаковый с V2)
SLOT = BORE            # ширина верхнего паза = диаметру (лёгкая укладка)
CH_W = 11.0            # наружная ширина канала
CH_TOP = BORE / 2.0 + 0.85         # +2.9  верх канала
CAV_TOP = CAV_T / 2.0              # +3.12 верх полости гнезда (низ крышки)

# Зоны вдоль X
POCKET_END = 14.0
TRANS_END = 22.0
TOTAL_L = 52.0

# Зубцы-фиксаторы — скруглённые бугорки у кромок паза (без острых углов)
TOOTH_R = 0.8          # радиус бугорка
TOOTH_Z = 1.5          # выше -> прижимают только верх провода, не мешают вставлять
TOOTH_X = [22.0, 30.0, 38.0, 46.0]

_PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(_PROOT, "Готовые модели", "V1 — чехол")
DOC_NAME = "CableProtector"


# --------------------------------------------------------------------------
# Контуры
# --------------------------------------------------------------------------
def dsec(x, w, zb, zt, r):
    """D-сечение: плоский низ (zb), вертикальные борта, скруглённый верх (zt)."""
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
    """Пара скруглённых бугорков у кромок паза — прижимают провод, без острых углов."""
    a = Part.makeSphere(TOOTH_R, App.Vector(xc, SLOT / 2.0, TOOTH_Z))
    b = Part.makeSphere(TOOTH_R, App.Vector(xc, -SLOT / 2.0, TOOTH_Z))
    return a.fuse(b)


# --------------------------------------------------------------------------
# Построение
# --------------------------------------------------------------------------
def build():
    outer = loft([
        dsec(0.0,        SOCK_W, BOTTOM, SOCK_TOP, 2.5),
        dsec(POCKET_END, SOCK_W, BOTTOM, SOCK_TOP, 2.5),
        dsec(TRANS_END,  CH_W,   BOTTOM, CH_TOP,   2.5),
        dsec(TOTAL_L,    CH_W,   BOTTOM, CH_TOP,   2.5),
    ])

    # полость гнезда (ось z=0) -> воронка -> прямой тоннель Ø4.1
    inner = loft([
        rrect_wire(-0.5,       CAV_W, CAV_T, BOOT_R),    # перёд открыт
        rrect_wire(POCKET_END, CAV_W, CAV_T, BOOT_R),
        circle_wire(TRANS_END, BORE),
        circle_wire(TOTAL_L + 0.5, BORE),
    ])
    body = outer.cut(inner)

    # КРЫША над гнездом + сплошная прорезь SLOT(4.1) по всей длине (без уступа,
    # без перегородок): бубышка заводится с ТОРЦА под крышу, провод
    # проталкивается в прорезь сверху.
    ZH = SOCK_TOP + 1.0
    slot = Part.makeBox(TOTAL_L + 1.5, SLOT, ZH, App.Vector(-0.5, -SLOT / 2.0, 0.0))
    body = body.cut(slot)

    # зубцы-фиксаторы
    for xc in TOOTH_X:
        body = body.fuse(tooth(xc))
    body = body.removeSplitter()
    return body


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = App.newDocument(DOC_NAME)
    shape = build()
    if not shape.isValid():
        App.Console.PrintWarning("Тело невалидно — чиню...\n")
        shape.fix(1e-6, 1e-6, 1e-6)
    bb = shape.BoundBox
    App.Console.PrintMessage(
        "Валидно: %s | тел: %d | объём: %.1f мм^3 | габарит: %.1f x %.1f x %.1f | низ z=%.2f\n"
        % (shape.isValid(), len(shape.Solids), shape.Volume,
           bb.XLength, bb.YLength, bb.ZLength, bb.ZMin))

    obj = doc.addObject("Part::Feature", DOC_NAME)
    obj.Shape = shape
    doc.recompute()
    fcstd = os.path.join(OUTPUT_DIR, DOC_NAME + ".FCStd")
    stl = os.path.join(OUTPUT_DIR, DOC_NAME + ".stl")
    step = os.path.join(OUTPUT_DIR, DOC_NAME + ".step")
    doc.saveAs(fcstd)
    shape.exportStep(step)
    import MeshPart
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                               AngularDeflection=0.4, Relative=False)
    m.write(stl)
    App.Console.PrintMessage("Экспортировано: FCStd / STL / STEP\n")


main()
