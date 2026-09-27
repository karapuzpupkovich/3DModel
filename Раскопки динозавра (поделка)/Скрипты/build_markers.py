# -*- coding: utf-8 -*-
"""
Номерки находок 1–9: табличка на опоре и цифра.

Два варианта одной геометрии:

  вкладыши   табличка с выемкой в форме цифры и отдельная цифра, которую
             вставляют в выемку. Печатаются двумя плитами разного цвета без
             AMS; собирать можно вместе с ребёнком.
  для AMS    та же табличка без выемки и цифра над лицом — две части одного
             объекта, каждая своим прутком. Печатается одной плитой.

Всё печатается плашмя, лицом вверх, без поддержек. Поэтому опора у
таблички только спереди: спина лежит на столе, а холмик опоры растёт вверх
вместе с лицом. Стоя табличка опирается на заднюю кромку и на холмик —
центр тяжести в пределах опоры, запас на опрокидывание назад ~24°.

Контуры цифр берутся из того же шрифта, что и надпись на большой табличке,
и считаются в shapely: так сразу видно, пройдут ли зазоры и «островки».
Объём собирает OpenSCAD.

    python build_markers.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import shapely
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUT = PROJECT / "Готовые модели" / "Номерки"
OUT_AMS = OUT / "для AMS"
sys.path.insert(0, str(HERE))
from build_plaques import FONT_FILE, check, run_openscad  # noqa: E402

DIGITS = "123456789"

# ---- цифра
DIGIT_H = 10.0     # высота цифры по шрифту, мм
OPEN = 0.35        # просветы (4, 6, 8, 9) и узкие щели на стыках штрихов
                   # (2, 3, 5, 6, верхняя петля 8 — 0.5-0.9 мм) шире
                   # шрифтовых на столько с каждой стороны. Иначе «островок»
                   # или «язычок» таблички в них не напечатать, а сопло 0.4
                   # не пропечатает щель в самой цифре. Истончается только
                   # штрих у щели: равномерное истончение всей цифры
                   # пережимало стык дуг у тройки
INLET_RHO = 0.6    # щель — то, что заливает морфологическое закрытие радиусом
INLET_MIN = 0.35   # ... площадью от стольких мм²; меньше — просто уголки стыков
CLEAR = 0.15       # зазор вкладыша по внешнему контуру, на сторону
CLEAR_IN = 0.25    # зазор вокруг островков: мелкие отверстия печатаются уже
                   # номинала, а мелкие столбики — толще
LEAD = 0.15        # первый слой цифры уже: срезает «слоновью ногу» и даёт заход
DIGIT_T = 2.0      # толщина вкладыша
POCKET = 1.4       # глубина выемки: вкладыш выступает над лицом на 0.6
RAISE = 0.6        # для AMS: цифра над лицом на те же 0.6

# ---- табличка (координаты печати: лицо вверх, Y — вверх у стоящей таблички)
W, H, T = 16.0, 23.0, 3.0
R = 3.0            # скругление верхних углов
FOOT_D = 11.0      # опора: вылет от спины таблички вперёд
FOOT_H1 = 2.5      # высота прямой передней стенки опоры
FOOT_H2 = 7.0      # на этой высоте холмик сходится с лицом
DIGIT_Y = (FOOT_H2 + H) / 2    # центр цифры — посередине открытой части лица


# --------------------------------------------------------------------------- #
#  Контур цифры из шрифта
# --------------------------------------------------------------------------- #
class FlatPen(BasePen):
    """Раскладывает контуры глифа в ломаные (кривые — по 16 отрезков)."""

    def __init__(self, glyphset, steps=16):
        super().__init__(glyphset)
        self.rings, self.cur, self.steps = [], None, steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _qCurveToOne(self, p1, p2):
        (x0, y0), n = self.cur[-1], self.steps
        for i in range(1, n + 1):
            t = i / n
            a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
            self.cur.append((a * x0 + b * p1[0] + c * p2[0], a * y0 + b * p1[1] + c * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        (x0, y0), n = self.cur[-1], self.steps
        for i in range(1, n + 1):
            t = i / n
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            self.cur.append((a * x0 + b * p1[0] + c * p2[0] + d * p3[0],
                             a * y0 + b * p1[1] + c * p2[1] + d * p3[1]))

    def _closePath(self):
        if self.cur and len(self.cur) > 2:
            self.rings.append(self.cur)
        self.cur = None

    _endPath = _closePath


_FONT = None


def winding(pt, ring: np.ndarray) -> int:
    """Сколько раз замкнутая ломаная обходит точку (со знаком)."""
    x, y = pt
    x0, y0 = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    cross = (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)
    up = (y0 <= y) & (y1 > y) & (cross > 0)
    down = (y0 > y) & (y1 <= y) & (cross < 0)
    return int(up.sum() - down.sum())


def nonzero_fill(rings):
    """
    Заливка по правилу ненулевой обмотки, как у FreeType. В этом шрифте
    цифра — обычно ОДИН контур, пересекающий сам себя (штрих поверх штриха),
    и просветы восьмёрки или шестёрки образованы не отдельными контурами,
    а направлением обхода. Контур режется на области в точках
    самопересечения, и каждая область заливается, если контур её обходит.
    """
    arrs = [np.asarray(r, float) for r in rings]
    lines = unary_union([LineString(np.vstack([a, a[:1]])) for a in arrs])
    faces = polygonize(lines)
    return unary_union([f for f in faces
                        if sum(winding(f.representative_point().coords[0], a) for a in arrs)])


def glyph(ch: str) -> Polygon:
    """Цифра шрифтом, высотой DIGIT_H, центр габарита — в (0, DIGIT_Y)."""
    global _FONT
    _FONT = _FONT or TTFont(FONT_FILE)
    gs = _FONT.getGlyphSet()
    pen = FlatPen(gs)
    gs[_FONT.getBestCmap()[ord(ch)]].draw(pen)
    g = nonzero_fill(pen.rings)
    s = DIGIT_H / 725.0                                 # единый кегль для всех цифр
    g = affinity.scale(g, s, s, origin=(0, 0))
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, -(x0 + x1) / 2, DIGIT_Y - (y0 + y1) / 2)


def parts_of(geom):
    return list(getattr(geom, "geoms", [geom]))


def narrow_inlets(solid: Polygon) -> list:
    """Узкие щели внешнего контура: их заливает закрытие радиусом INLET_RHO."""
    closed = solid.buffer(INLET_RHO, quad_segs=16).buffer(-INLET_RHO, quad_segs=16)
    return [c for c in parts_of(closed.difference(solid)) if c.area >= INLET_MIN]


def shapes(ch: str) -> dict:
    """Все плоские контуры одной цифры и проверка печатности."""
    g = glyph(ch)
    digit_parts = []
    for p in parts_of(g):
        solid = Polygon(p.exterior)
        gaps = [Polygon(r) for r in p.interiors] + narrow_inlets(solid)
        wide = unary_union([x.buffer(OPEN, quad_segs=12) for x in gaps]) if gaps else None
        digit_parts.append(solid.difference(wide) if gaps else solid)
    digit = unary_union(digit_parts)
    pocket_parts = []
    for p in parts_of(digit):
        outer = Polygon(p.exterior).buffer(CLEAR, quad_segs=12)
        islands = [Polygon(r).buffer(-CLEAR_IN, quad_segs=12) for r in p.interiors]
        islands = [i for i in islands if not i.is_empty]
        pocket_parts.append(outer.difference(unary_union(islands)) if islands else outer)
    pocket = unary_union(pocket_parts)
    lead = digit.buffer(-LEAD, quad_segs=12)

    # --- печатность
    def inscribed(poly):                     # диаметр вписанной окружности
        return 2 * shapely.maximum_inscribed_circle(poly, 0.01).length

    islands = [Polygon(r) for p in parts_of(pocket) for r in p.interiors]
    counters = [Polygon(r) for p in parts_of(digit) for r in p.interiors]
    # штрих: цифра не должна рваться при эрозии на 0.7 (перешейки уже 1.4 мм)
    eroded = digit.buffer(-0.7)
    info = {
        "parts": len(parts_of(digit)),
        "stroke_ok": len(parts_of(eroded)) == len(parts_of(digit)),
        "island_min": min((inscribed(i) for i in islands), default=None),
        "counter_min": min((inscribed(c) for c in counters), default=None),
        "bounds": digit.bounds,
    }
    return {"digit": digit, "pocket": pocket, "lead": lead, "info": info}


# --------------------------------------------------------------------------- #
#  OpenSCAD
# --------------------------------------------------------------------------- #
def scad_poly(geom) -> str:
    out = []
    for p in parts_of(geom):
        pts, paths = [], []
        for ring in (p.exterior, *p.interiors):
            c = list(ring.coords)[:-1]
            paths.append(list(range(len(pts), len(pts) + len(c))))
            pts += [[round(x, 4), round(y, 4)] for x, y in c]
        out.append(f"polygon(points={pts}, paths={paths});")
    return "union() { " + " ".join(out) + " }"


def foot_profile() -> list:
    """
    Профиль опоры в координатах (Y, Z) печати: прямая передняя стенка
    высотой FOOT_H1 и четверть эллипса до лица таблички. Каждый следующий
    слой уже предыдущего — навесов нет.
    """
    pts = [(0.0, 0.0), (0.0, FOOT_D)]
    for i in range(0, 25):
        a = math.radians(90 * i / 24)
        pts.append((FOOT_H1 + (FOOT_H2 - FOOT_H1) * math.sin(a),
                    T + (FOOT_D - T) * math.cos(a)))
    pts.append((FOOT_H2, 0.0))
    return [[round(y, 4), round(z, 4)] for y, z in pts]


def body_scad() -> str:
    """Табличка с опорой, без выемки."""
    return f"""union() {{
    linear_extrude({T}) hull() {{
      translate([{-W / 2 + R}, {H - R}]) circle(r={R}, $fn=48);
      translate([{W / 2 - R}, {H - R}]) circle(r={R}, $fn=48);
      translate([{-W / 2}, 0]) square([{W}, {H - R}]);
    }}
    // опора: профиль (Y, Z) вытянут вдоль X на всю ширину таблички
    rotate([90, 0, 90]) linear_extrude(height={W}, center=true)
      polygon(points={foot_profile()});
  }}"""


def plaque_scad(sh) -> str:
    return f"""// Номерок с выемкой под цифру — генерируется build_markers.py
difference() {{
  {body_scad()}
  translate([0, 0, {T - POCKET}]) linear_extrude({POCKET + 1})
    {scad_poly(sh["pocket"])}
}}
"""


def digit_scad(sh) -> str:
    return f"""// Цифра-вкладыш — генерируется build_markers.py
union() {{
  linear_extrude(0.2) {scad_poly(sh["lead"])}
  translate([0, 0, 0.2]) linear_extrude({DIGIT_T - 0.2}) {scad_poly(sh["digit"])}
}}
"""


def ams_digit_scad(sh) -> str:
    return f"""// Цифра над лицом таблички (второй пруток) — генерируется build_markers.py
translate([0, 0, {T}]) linear_extrude({RAISE}) {scad_poly(sh["digit"])}
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_AMS.mkdir(parents=True, exist_ok=True)
    print(f"табличка {W:g} x {H:g} x {T:g} мм, опора вперёд {FOOT_D - T:g} мм, "
          f"цифра {DIGIT_H:g} мм, выемка {POCKET:g}, вкладыш {DIGIT_T:g}\n")
    # для AMS основа у всех номерков одна и та же, различается только цифра
    check("основа (AMS)", run_openscad(f"// Основа номерка для AMS\n{body_scad()}\n",
                                       OUT_AMS / "основа.stl"))
    for ch in DIGITS:
        sh = shapes(ch)
        i = sh["info"]
        x0, y0, x1, y1 = i["bounds"]
        isl = f"{i['island_min']:.2f}" if i["island_min"] is not None else "—"
        cnt = f"{i['counter_min']:.2f}" if i["counter_min"] is not None else "—"
        print(f"цифра {ch}: {x1 - x0:4.1f} x {y1 - y0:4.1f} мм  частей {i['parts']}  "
              f"штрих>=1.4 {'да' if i['stroke_ok'] else 'НЕТ'}  "
              f"просвет {cnt}  островок {isl}")
        check(f"номерок {ch}", run_openscad(plaque_scad(sh), OUT / f"номерок {ch}.stl"))
        check(f"цифра {ch}", run_openscad(digit_scad(sh), OUT / f"цифра {ch}.stl"))
        check(f"цифра {ch} (AMS)", run_openscad(ams_digit_scad(sh), OUT_AMS / f"цифра {ch}.stl"))


if __name__ == "__main__":
    main()
