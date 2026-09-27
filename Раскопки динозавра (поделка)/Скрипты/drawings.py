# -*- coding: utf-8 -*-
"""
Рисунки для гравировки: динозавр на табличке и карта раскопок.

Каждый рисунок — набор элементов:
  stroke(точки, ширина)  — линия-канавка (закругл. концы);
  fill(контур)           — залитая лунка (череп, крестик);
  island(контур/круг)    — «остров» внутри лунки, НЕ гравируется (глаз).

Всё, что гравируется, станет канавкой глубиной ~0.8 мм — её заливают
краской и стирают излишки с поверхности. Отсюда правила:
  * канавка не уже 0.8 мм — иначе краска не зайдёт, а сопло 0.4 не
    пропечатает стенки;
  * перемычка между канавками не уже 0.8 мм — иначе стенка сломается
    при стирании краски.

Координаты в мм, начало — левый нижний угол рисунка, Y вверх.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Drawing:
    strokes: list = field(default_factory=list)   # (points, width)
    fills: list = field(default_factory=list)      # points
    islands: list = field(default_factory=list)    # ("circle", cx, cy, r) | ("poly", points)

    def stroke(self, pts, w=0.95):
        self.strokes.append(([tuple(p) for p in pts], w))

    def fill(self, pts):
        self.fills.append([tuple(p) for p in pts])

    def island_circle(self, cx, cy, r):
        self.islands.append(("circle", cx, cy, r))

    def island_poly(self, pts):
        self.islands.append(("poly", [tuple(p) for p in pts]))

    def bounds(self):
        xs, ys = [], []
        for pts, w in self.strokes:
            xs += [p[0] - w / 2 for p in pts] + [p[0] + w / 2 for p in pts]
            ys += [p[1] - w / 2 for p in pts] + [p[1] + w / 2 for p in pts]
        for pts in self.fills:
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def moved(self, dx, dy, s=1.0):
        """Копия со сдвигом и масштабом (ширины линий не масштабируются)."""
        d = Drawing()
        d.strokes = [([(x * s + dx, y * s + dy) for x, y in pts], w) for pts, w in self.strokes]
        d.fills = [[(x * s + dx, y * s + dy) for x, y in pts] for pts in self.fills]
        for isl in self.islands:
            if isl[0] == "circle":
                d.islands.append(("circle", isl[1] * s + dx, isl[2] * s + dy, isl[3] * s))
            else:
                d.islands.append(("poly", [(x * s + dx, y * s + dy) for x, y in isl[1]]))
        return d

    def merged(self, other):
        d = Drawing()
        d.strokes = self.strokes + other.strokes
        d.fills = self.fills + other.fills
        d.islands = self.islands + other.islands
        return d

    # ---------------------------------------------------------------- OpenSCAD
    def scad(self, fn=20):
        """2D-модуль OpenSCAD: всё, что гравируется, минус острова."""
        out = ["union() {"]
        for pts, w in self.strokes:
            r = w / 2
            if len(pts) == 1:
                out.append(f"  translate([{pts[0][0]:.3f},{pts[0][1]:.3f}]) circle(r={r:.3f},$fn={fn});")
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                out.append(f"  hull(){{translate([{x0:.3f},{y0:.3f}]) circle(r={r:.3f},$fn={fn});"
                           f"translate([{x1:.3f},{y1:.3f}]) circle(r={r:.3f},$fn={fn});}}")
        for pts in self.fills:
            out.append("  polygon(" + str([[round(x, 3), round(y, 3)] for x, y in pts]) + ");")
        out.append("}")
        body = "\n".join(out)
        if not self.islands:
            return body
        isl = ["union() {"]
        for it in self.islands:
            if it[0] == "circle":
                isl.append(f"  translate([{it[1]:.3f},{it[2]:.3f}]) circle(r={it[3]:.3f},$fn={fn * 2});")
            else:
                isl.append("  polygon(" + str([[round(x, 3), round(y, 3)] for x, y in it[1]]) + ");")
        isl.append("}")
        return "difference() {\n" + body + "\n" + "\n".join(isl) + "\n}"


# --------------------------------------------------------------------------- #
#  Помощники рисования
# --------------------------------------------------------------------------- #
def bez(p0, p1, p2, n=10):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / (n - 1) for i in range(n))]


def spline(pts, n_per=6):
    """Сглаженная ломаная (Катмулл — Ром) через опорные точки."""
    if len(pts) < 3:
        return pts
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n_per):
            t = k / n_per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                             for j in range(2)))
    out.append(tuple(pts[-1]))
    return out


def along(path, dist):
    """Точка и касательная на расстоянии dist вдоль ломаной."""
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if acc + seg >= dist and seg > 0:
            t = (dist - acc) / seg
            return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), ((x1 - x0) / seg, (y1 - y0) / seg)
        acc += seg
    (x0, y0), (x1, y1) = path[-2], path[-1]
    seg = math.hypot(x1 - x0, y1 - y0) or 1
    return path[-1], ((x1 - x0) / seg, (y1 - y0) / seg)


def length(path):
    return sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(path, path[1:]))


def ticks(d: Drawing, path, start, end, step, half, w=0.8):
    """Поперечные чёрточки вдоль линии — позвонки хвоста и шеи."""
    s = start
    while s <= end + 1e-6:
        (x, y), (tx, ty) = along(path, s)
        nx, ny = -ty, tx
        d.stroke([(x - nx * half, y - ny * half), (x + nx * half, y + ny * half)], w)
        s += step


def dashed(d: Drawing, path, dash=2.0, gap=1.3, w=0.9):
    L = length(path)
    s = 0.0
    while s < L:
        e = min(s + dash, L)
        pts = [along(path, s)[0]]
        k = s + 0.5
        while k < e:
            pts.append(along(path, k)[0])
            k += 0.5
        pts.append(along(path, e)[0])
        d.stroke(pts, w)
        s = e + gap


# --------------------------------------------------------------------------- #
#  Тираннозавр для таблички (как на образце: идёт вправо, пасть открыта)
# --------------------------------------------------------------------------- #
def trex() -> Drawing:
    """
    Таз сзади, грудная клетка впереди, лапы растут из таза — как на образце.
    Зубчики пасти на образце мельче сопла (0.5 мм), поэтому пасть — клин
    с двумя крупными зубами: такие и пропечатаются, и закрасятся.
    """
    d = Drawing()
    back = spline([(0.8, 4.9), (4.2, 6.5), (8.2, 8.5), (11.8, 10.0), (14.6, 10.7),
                   (18.0, 10.8), (21.2, 10.3), (23.4, 10.0), (25.0, 11.2), (26.2, 12.5)], 5)
    d.stroke(back, 1.15)
    ticks(d, back, 1.2, 9.8, 1.9, 0.95, 0.8)
    skull = [(25.4, 12.2), (25.7, 14.3), (27.3, 15.5), (30.0, 15.9), (32.6, 15.3),
             (34.3, 14.3), (34.6, 13.3), (32.2, 12.9), (30.0, 12.55),
             (30.4, 11.2), (33.6, 11.0), (33.9, 10.3), (31.4, 9.9), (28.2, 10.1),
             (26.3, 10.9)]
    d.fill(skull)
    d.island_circle(28.3, 14.0, 0.65)
    # пасть: клин и два зуба-выступа сверху
    d.island_poly([(29.6, 12.1), (34.4, 12.95), (34.0, 12.25), (33.3, 12.0),
                   (32.6, 11.25), (32.1, 11.95), (31.2, 11.8), (30.6, 11.05), (30.2, 11.7)])
    # рёбра — впереди таза, под грудью
    for x0 in (16.2, 18.4, 20.6):
        d.stroke(bez((x0, 10.5), (x0 + 0.7, 8.0), (x0 + 0.2, 5.4), 6), 0.9)
    d.stroke(bez((22.6, 9.9), (23.1, 8.0), (22.6, 6.3), 6), 0.85)
    # брюшная линия: на неё садятся концы рёбер — грудная клетка как на образце
    d.stroke(spline([(16.4, 5.4), (19.4, 4.9), (22.6, 6.3)], 5), 0.8)
    # передние лапки
    d.stroke([(23.6, 8.6), (24.8, 7.3), (25.8, 6.9)], 0.8)
    # задние лапы из таза: одна назад, другая вперёд
    d.stroke([(13.2, 9.7), (11.3, 5.6), (12.6, 1.9)], 1.2)
    d.stroke([(12.6, 1.9), (14.8, 0.7)], 0.95)
    d.stroke([(12.6, 1.9), (13.8, 0.35)], 0.85)
    d.stroke([(14.3, 9.6), (16.2, 5.8), (15.0, 2.0)], 1.2)
    d.stroke([(15.0, 2.0), (17.2, 0.8)], 0.95)
    d.stroke([(15.0, 2.0), (16.2, 0.45)], 0.85)
    return d


# --------------------------------------------------------------------------- #
#  Длинношеий динозавр для карты (как на образце: голова слева вверху)
# --------------------------------------------------------------------------- #
def sauropod() -> Drawing:
    d = Drawing()
    spine = spline([(3.2, 16.0), (4.8, 14.4), (6.6, 11.6), (9.2, 9.6), (12.5, 9.1),
                    (16.5, 9.6), (20.5, 9.8), (24.0, 9.2), (27.5, 8.0), (31.0, 7.2),
                    (34.0, 7.6), (35.6, 8.8)], 5)
    d.stroke(spine, 1.0)
    # голова — залитая лунка с глазом
    head = [(1.3, 15.4), (1.5, 17.0), (2.8, 17.9), (4.6, 17.6), (5.1, 16.4),
            (4.0, 15.4), (2.6, 15.0)]
    d.fill(head)
    d.island_circle(3.5, 16.7, 0.5)
    # позвонки шеи и хвоста
    L = length(spine)
    ticks(d, spine, 3.6, 10.5, 1.75, 0.85, 0.8)
    ticks(d, spine, L - 11.5, L - 1.2, 1.75, 0.8, 0.8)
    # рёбра
    for x0 in (13.2, 15.2, 17.2, 19.2, 21.0):
        top = 9.3 if x0 < 20 else 9.5
        d.stroke(bez((x0, top), (x0 + 0.5, top - 2.3), (x0 + 0.1, 5.2), 6), 0.85)
    # брюшная линия, на которую садятся рёбра
    d.stroke(spline([(12.4, 5.9), (16.5, 5.0), (21.8, 5.4)], 5), 0.85)
    # ноги-столбы
    for x0, lean in ((12.6, -0.4), (14.6, 0.3), (21.4, -0.2), (23.4, 0.4)):
        d.stroke([(x0, 7.0), (x0 + lean, 3.4), (x0 + lean * 0.5, 0.8)], 1.05)
        d.stroke([(x0 + lean * 0.5, 0.8), (x0 + lean * 0.5 + 1.3, 0.5)], 0.85)
    return d


# --------------------------------------------------------------------------- #
#  Карта раскопок
# --------------------------------------------------------------------------- #
def dig_map(W=60.0, H=44.0) -> Drawing:
    d = Drawing()
    inset = 3.4
    # рамка, нарисованная «от руки» — чуть кривая
    fr = [(inset, inset + 0.3), (W / 2, inset - 0.15), (W - inset, inset + 0.25),
          (W - inset - 0.2, H / 2), (W - inset, H - inset - 0.2), (W / 2, H - inset + 0.2),
          (inset + 0.15, H - inset), (inset - 0.1, H / 2), (inset, inset + 0.3)]
    d.stroke(fr, 0.85)
    # динозавр
    d = d.merged(sauropod().moved(7.0, 20.0))
    # горы
    for x0, h in ((42.5, 4.4), (47.0, 5.6), (51.5, 3.8)):
        d.stroke([(x0 - 2.6, 20.6), (x0, 20.6 + h), (x0 + 2.6, 20.6)], 0.85)
    # компас: стрелка на север и буква «С»
    cx, cy = 50.0, 33.0
    d.fill([(cx, cy + 4.6), (cx - 1.4, cy + 0.6), (cx, cy + 1.4), (cx + 1.4, cy + 0.6)])
    d.stroke([(cx, cy + 1.2), (cx, cy - 2.4)], 0.85)
    arc = [(cx + 1.25 * math.cos(math.radians(a)) - 0.2, cy - 4.6 + 1.25 * math.sin(math.radians(a)))
           for a in range(40, 330, 25)]
    d.stroke(arc, 0.85)
    # пунктир к месту раскопок
    trail = spline([(7.5, 8.0), (12.5, 13.0), (19.5, 10.8), (25.5, 7.2),
                    (32.0, 9.8), (38.5, 12.2), (44.0, 10.5)], 6)
    dashed(d, trail, dash=2.0, gap=1.35, w=0.9)
    # крестик «копать здесь»
    x, y, r = 49.2, 9.8, 2.3
    d.stroke([(x - r, y - r), (x + r, y + r)], 1.25)
    d.stroke([(x - r, y + r), (x + r, y - r)], 1.25)
    # ёлочки у тропы — залитые треугольники, их удобно закрасить зелёным
    for tx, ty, h in ((27.6, 13.4, 4.6), (31.2, 12.6, 3.8)):
        d.fill([(tx - h * 0.42, ty), (tx, ty + h), (tx + h * 0.42, ty)])
        d.stroke([(tx, ty + 0.2), (tx, ty - 1.2)], 0.9)
    return d


# --------------------------------------------------------------------------- #
#  Предпросмотр
# --------------------------------------------------------------------------- #
def preview(drawing: Drawing, out, box=None, title=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon
    x0, y0, x1, y1 = box or drawing.bounds()
    fig, ax = plt.subplots(figsize=((x1 - x0) / 7, (y1 - y0) / 7), dpi=110)
    ax.set_facecolor("#e9d6b0")
    mm_to_pt = 72 / 25.4 * ((fig.get_size_inches()[0] * 25.4) / (x1 - x0))
    for pts, w in drawing.strokes:
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color="#2a1c10", lw=w * mm_to_pt, solid_capstyle="round",
                solid_joinstyle="round")
    for pts in drawing.fills:
        ax.add_patch(Polygon(pts, closed=True, color="#2a1c10"))
    for it in drawing.islands:
        if it[0] == "circle":
            ax.add_patch(Circle((it[1], it[2]), it[3], color="#e9d6b0"))
        else:
            ax.add_patch(Polygon(it[1], closed=True, color="#e9d6b0"))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
