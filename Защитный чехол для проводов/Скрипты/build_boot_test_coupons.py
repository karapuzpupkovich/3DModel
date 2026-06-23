# -*- coding: utf-8 -*-
"""
Тестовые образцы ГНЕЗДА БУБЫШКИ (USB-C overmold) для подбора посадки.

Идея: вместо печати всего чехла печатаем 5 коротких (5 мм) "люлек" с номерами
1..5 и вкладываем в них бубышку, чтобы вживую выбрать лучший зазор/форму.
Все образцы — с ВЕРХНЕЙ КРЫШКОЙ и центральной прорезью (4.4 мм) под провод,
как в основной модели V1/V2: бубышка заводится с ТОРЦА (образец сквозной),
крышка держит её сверху. Так образец повторяет реальную посадку.

Варьируем ОДНОВРЕМЕННО зазор и скругление (по выбору пользователя):
  #1  зазор +0.25/сторону, R1.5  — ближе всего к текущему V1 (прямоугольное)
  #2  зазор +0.18/сторону, R2.0
  #3  зазор +0.12/сторону, R2.5
  #4  зазор +0.06/сторону, R2.8
  #5  зазор  0.00/сторону, R3.0  — плотно, форма "стадион" (овальная)

Бубышка (замер пользователя): 10 (ширина, Y) x 6 (толщина, Z) x 17 (длина).
Ось X — вдоль кабеля (длина образца).

Запуск:
  "C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" build_boot_test_coupons.py
"""
import os
import math

import FreeCAD as App
import Part

# --- бубышка / общие параметры -------------------------------------------
BOOT_W = 10.0      # ширина бубышки (Y)
BOOT_T = 6.0       # толщина бубышки (Z)
WALL = 2.0         # стенка люльки
SLOT_BOOT = 4.4    # центральная прорезь в крышке (под провод), как в основной модели
LEN = 5.0          # длина образца вдоль кабеля (X)
DIGIT_SIZE = 3.6   # высота цифры
DIGIT_DEPTH = 0.6  # глубина гравировки

# вариант: (gap на сторону, радиус скругления гнезда)
VARIANTS = {
    1: (0.25, 1.5),
    2: (0.18, 2.0),
    3: (0.12, 2.5),
    4: (0.06, 2.8),
    5: (0.00, 3.0),
}

FONTS = [r"C:/Windows/Fonts/arialbd.ttf", r"C:/Windows/Fonts/arial.ttf"]
FONT = next((f for f in FONTS if os.path.exists(f)), None)

_PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(_PROOT, "Готовые модели", "Образцы гнезда бубышки")


def rrect_wire_yz(x, w, h, r):
    """Скруглённый прямоугольник в плоскости X=const (координаты Y,Z)."""
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


def prism(x0, x1, w, h, r):
    face = Part.Face(rrect_wire_yz(x0, w, h, r))
    return face.extrude(App.Vector(x1 - x0, 0, 0))


def dsec_wire_yz(x, w, zb, zt, r):
    """D-сечение (плоский низ zb, скруглённый верх zt) в плоскости X=const."""
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


def dprism(x0, x1, w, zb, zt, r):
    face = Part.Face(dsec_wire_yz(x0, w, zb, zt, r))
    return face.extrude(App.Vector(x1 - x0, 0, 0))


def engrave_digit(body, n, out_w, out_t):
    """Гравируем цифру на наружной грани +Y."""
    if FONT is None:
        return body
    try:
        import Draft
        doc = App.ActiveDocument
        ss = Draft.make_shapestring(String=str(n), FontFile=FONT, Size=DIGIT_SIZE)
        doc.recompute()
        text2d = ss.Shape.copy()
        # текст создаётся в плоскости XY -> повернуть в плоскость XZ (грань +Y)
        text2d.translate(App.Vector(-text2d.BoundBox.XLength / 2.0,
                                     -text2d.BoundBox.YLength / 2.0, 0))
        solid = text2d.extrude(App.Vector(0, 0, DIGIT_DEPTH + 0.2))
        # повернуть: XY-плоскость -> XZ, нормаль +Y
        solid.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
        # позиция: по центру длины X, по высоте Z, на грани Y=out_w/2
        solid.translate(App.Vector(LEN / 2.0, out_w / 2.0 + DIGIT_DEPTH, 0))
        doc.removeObject(ss.Name)
        res = body.cut(solid)
        if res.isValid() and len(res.Solids) == 1:
            return res
    except Exception as exc:  # noqa: BLE001
        App.Console.PrintWarning("Гравировка #%d пропущена: %s\n" % (n, exc))
    return body


def build_coupon(n):
    gap, r = VARIANTS[n]
    cav_w = BOOT_W + 2 * gap
    cav_t = BOOT_T + 2 * gap
    out_w = cav_w + 2 * WALL
    out_t = cav_t + 2 * WALL

    # плоская подошва (D-сечение): печать без поддержек
    outer = dprism(0.0, LEN, out_w, -out_t / 2.0, out_t / 2.0,
                   min(r + WALL, out_w / 2 - 1e-3, out_t / 2 - 1e-3))
    cavity = prism(-0.5, LEN + 0.5, cav_w, cav_t, r)
    body = outer.cut(cavity)

    # верх ОТКРЫТ (как в моделях v6, без крышки): бубышка вкладывается сверху
    mouth = Part.makeBox(LEN + 1.0, cav_w, out_t,
                         App.Vector(-0.5, -cav_w / 2.0, cav_t / 2.0))
    body = body.cut(mouth)

    body = engrave_digit(body, n, out_w, out_t)
    return body, out_w, out_t


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = App.newDocument("BootCoupons")

    import MeshPart
    import Mesh

    plate_meshes = []
    y_cursor = 0.0
    summary = []
    for n in sorted(VARIANTS):
        shape, out_w, out_t = build_coupon(n)
        gap, r = VARIANTS[n]
        cav_w = BOOT_W + 2 * gap
        cav_t = BOOT_T + 2 * gap
        summary.append((n, gap, r, cav_w, cav_t, out_w, out_t, shape.Volume))

        # индивидуальный STL (низ на Z=0)
        s = shape.copy()
        s.translate(App.Vector(0, 0, out_t / 2.0))
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.04,
                                   AngularDeflection=0.3, Relative=False)
        m.write(os.path.join(OUTPUT_DIR, "BootCoupon_%d.stl" % n))

        # вклад в общую пластину
        mp = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.04,
                                    AngularDeflection=0.3, Relative=False)
        mp.translate(0, y_cursor, 0)
        plate_meshes.append(mp)
        y_cursor += out_w + 6.0

    # общая пластина
    plate = Mesh.Mesh()
    for mp in plate_meshes:
        plate.addMesh(mp)
    plate.write(os.path.join(OUTPUT_DIR, "BootCoupons_plate.stl"))

    # сохранить FCStd с разложенными образцами
    yy = 0.0
    for n in sorted(VARIANTS):
        shape, out_w, out_t = build_coupon(n)
        o = doc.addObject("Part::Feature", "Coupon_%d" % n)
        sh = shape.copy()
        sh.translate(App.Vector(0, yy, out_t / 2.0))
        o.Shape = sh
        yy += out_w + 6.0
    doc.recompute()
    doc.saveAs(os.path.join(OUTPUT_DIR, "BootCoupons.FCStd"))

    App.Console.PrintMessage("\n=== Тестовые образцы гнезда бубышки ===\n")
    App.Console.PrintMessage(
        "№  зазор/ст  R     гнездо(ШxТ)    наружный     V,мм3\n")
    for (n, gap, r, cw, ct, ow, ot, vol) in summary:
        App.Console.PrintMessage(
            "%d   +%.2f    %.1f   %.2f x %.2f   %.1f x %.1f   %.0f\n"
            % (n, gap, r, cw, ct, ow, ot, vol))
    App.Console.PrintMessage("Экспорт: %s\n" % OUTPUT_DIR)


main()
