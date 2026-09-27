# -*- coding: utf-8 -*-
"""
Скелет динозавра для поделки «Раскопки» — полурельефные кости.

Кости лежат в песке на боку, как находка на раскопках: плоское дно, округлый
верх. Это же делает их печатными без поддержек. Скелет разбит на детали,
которые ребёнок раскладывает в песке по схеме.

Координаты и размеры сняты с образца (Референсы/образец.webp): кадр со
скелетом, 6 px = 1 мм после приведения к масштабу ×1.33 (см. README).
Череп смотрит влево (−X), спина вверх (+Y), рёбра и лапы вниз (−Y).

Запуск (нужен Blender — из него берутся numpy и OpenVDB):
    blender -b -P build_skeleton.py
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sdf import (Ellipsoid, Part, RoundCone, Sphere, bezier, chain,  # noqa: E402
                 write_stl)

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "Готовые модели" / "Скелет"


# --------------------------------------------------------------------------- #
#  Геометрические помощники (всё в плоскости XY, z = 0)
# --------------------------------------------------------------------------- #
def v2(x, y):
    return np.array([x, y], dtype=float)


def unit(v):
    return v / np.linalg.norm(v)


def left(u):
    """Нормаль, повёрнутая на +90° — «спинная» сторона для цепочки слева направо."""
    return np.array([-u[1], u[0]])


def p3(p, z=0.0):
    return (float(p[0]), float(p[1]), z)


def deg(u):
    return math.degrees(math.atan2(u[1], u[0]))


def dog_bone(p0, p1, r=1.7, lobe_r=2.05, lobe_off=None, k=0.45):
    """
    Мультяшная кость: стержень и по две шишки-мыщелка на концах —
    как на образце. Шишки разнесены почти на свой диаметр, чтобы между
    ними остался видимый вырез: при большем перекрытии и мягком слиянии
    они сливались в один шар и кость теряла узнаваемый силуэт.
    """
    p0, p1 = v2(*p0), v2(*p1)
    u = unit(p1 - p0)
    n = left(u)
    off = 0.92 * lobe_r if lobe_off is None else lobe_off
    prims = [RoundCone(a=p3(p0), b=p3(p1), ra=r, rb=r, k=0.6)]
    for end, sgn in ((p0, 1), (p1, -1)):
        base = end + u * sgn * 0.55 * lobe_r
        for s in (-1, 1):
            prims.append(Sphere(c=p3(base + n * s * off), r=lobe_r, k=k))
    return prims


def claw(base, ctrl, tip, r0=1.15, r1=0.55, n=7, k=0.5):
    """Изогнутый коготь: сужающаяся трубка по кривой Безье, кончик скруглён."""
    pts = bezier(base, ctrl, tip, n)
    radii = [r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    return chain(pts, radii, k=k)


def vertebra(c, u, s, knob=True):
    """
    Позвонок-«катушка»: тело, два бортика по краям и остистый отросток
    на спинной стороне. s — полуширина тела.
    """
    c = v2(*c)
    a = deg(u)
    n = left(u)
    prims = [Ellipsoid(c=p3(c), r=(0.9 * s, s, 0.92 * s), ang=a, k=0.45)]
    for sgn in (-1, 1):
        prims.append(Ellipsoid(c=p3(c + u * sgn * 0.78 * s),
                               r=(0.36 * s, 1.1 * s, 0.98 * s), ang=a, k=0.3))
    if knob:
        tip = c + n * 1.45 * s
        prims.append(RoundCone(a=p3(c + n * 0.5 * s), b=p3(tip),
                               ra=0.5 * s, rb=0.46 * s, k=0.5))
    return prims


def spine(centers, sizes, rod=0.5, knob=True):
    """Цепочка позвонков вдоль ломаной центров плюс осевой стержень."""
    cs = [v2(*c) for c in centers]
    prims = []
    rod_r = [rod * s for s in sizes]
    prims += chain([p3(c) for c in cs], rod_r, k=0.4)
    for i, c in enumerate(cs):
        a = cs[max(0, i - 1)]
        b = cs[min(len(cs) - 1, i + 1)]
        prims += vertebra(c, unit(b - a), sizes[i], knob=knob)
    return prims


def rib(root, tip, bow, r_max, r_tip=0.7, n=9):
    """
    Ребро-«клык», как на образце: толстое у корня, сужается к кончику,
    выгнуто назад. bow — вынос средней точки поперёк ребра, мм.
    """
    root, tip = v2(*root), v2(*tip)
    d = tip - root
    mid = root + d * 0.45 + left(unit(d)) * -bow
    pts = bezier(root, mid, tip, n)
    radii = []
    for i in range(n):
        t = i / (n - 1)
        # быстро набирает толщину у корня, потом плавно сходит на нет
        prof = min(1.0, 0.72 + t * 1.6) if t < 0.18 else 1.0 - (t - 0.18) / 0.82 * (1 - r_tip / r_max)
        radii.append(r_max * prof)
    segs = chain(pts, radii, k=0.3)
    segs[0].k = 0.9          # корень плавно врастает в позвонок
    return segs


# --------------------------------------------------------------------------- #
#  Детали
# --------------------------------------------------------------------------- #
def skull():
    """
    Череп с приоткрытой пастью. Верхняя челюсть — сужающийся «клюв»,
    сзади свод черепа; нижняя челюсть — тонкая кость, срастается с черепом
    только у шарнира. Глазница, окно перед ней и ноздря — лунки сверху,
    их удобно закрасить тёмным.
    """
    p = Part("череп")
    # верхняя челюсть и свод
    p.add(RoundCone(a=(27.0, 16.0, 0), b=(2.0, 9.6, 0), ra=7.5, rb=1.6, k=0.5))
    p.add(Ellipsoid(c=(31.0, 18.5, 0), r=(9.0, 9.0, 7.6), k=2.5))
    # надбровье и затылочный бугор — мягкие выпуклости на своде
    p.add(Ellipsoid(c=(26.0, 24.2, 0), r=(5.2, 2.4, 5.6), ang=-12, k=1.6))
    p.add(Ellipsoid(c=(37.2, 15.0, 0), r=(3.6, 4.6, 6.2), k=1.8))
    # скуловая дуга: утолщение над углом рта
    p.add(RoundCone(a=(33.0, 10.2, 0), b=(19.0, 9.4, 0), ra=3.1, rb=2.0, k=1.2))
    # нижняя челюсть: от шарнира к кончику, чуть вогнутая
    jaw = [(33.2, 8.2, 0), (25.0, 5.9, 0), (17.0, 4.1, 0), (9.0, 2.6, 0), (2.4, 1.9, 0)]
    p.add(chain(jaw, [2.5, 2.1, 1.85, 1.55, 1.3], k=0.3))
    p.prims[-4].k = 1.2      # у шарнира — плавно в череп
    # зубы верхней челюсти: вниз и чуть назад
    for x in (4.2, 7.3, 10.4, 13.5, 16.6, 19.7, 22.6):
        y_edge = 8.05 + 0.018 * (x - 2.0)
        p.add(RoundCone(a=(x, y_edge + 0.9, 0), b=(x + 0.35, y_edge - 1.75, 0),
                        ra=0.88, rb=0.36, k=0.35))
    # зубы нижней челюсти: вверх
    for x in (5.6, 8.9, 12.2, 15.5, 18.8):
        t = (x - 2.4) / (33.2 - 2.4)
        y_top = 1.9 + t * 6.3 + (1.3 + t * 1.2)
        p.add(RoundCone(a=(x, y_top - 0.9, 0), b=(x - 0.3, y_top + 1.45, 0),
                        ra=0.78, rb=0.33, k=0.3))
    # лунки: глазница, предглазничное окно, ноздря
    p.add(Sphere(c=(27.0, 18.8, 4.5), r=3.9, op="sub", k=0.55))
    p.add(Ellipsoid(c=(17.2, 14.3, 4.1), r=(3.3, 1.85, 3.0), ang=14, op="sub", k=0.45))
    p.add(Ellipsoid(c=(6.3, 10.75, 2.35), r=(1.55, 0.95, 1.35), ang=14, op="sub", k=0.3))
    return p


# центры позвонков, снятые с образца (мм)
NECK_BACK = [(42.5, 15.0), (47.8, 11.3), (53.4, 8.3), (59.1, 5.8), (64.7, 3.5),
             (70.2, 1.3), (75.5, -0.8), (80.7, -3.0), (85.8, -5.4), (90.8, -7.9)]
TAIL = [(95.8, -10.5), (100.4, -13.2), (104.7, -16.0), (108.7, -18.8),
        (112.4, -21.6), (115.9, -24.4), (119.1, -27.2), (122.0, -30.0)]


def spine_ribs():
    """Шея и спина: десять позвонков и шесть рёбер-«клыков»."""
    p = Part("позвоночник с рёбрами")
    sizes = [2.45, 2.4, 2.35, 2.3, 2.3, 2.25, 2.2, 2.15, 2.1, 2.05]
    p.add(spine(NECK_BACK, sizes))
    # рёбра: корень под позвонком, кончик вниз и чуть к голове (как на образце)
    ribs = [  # (индекс позвонка, вектор к кончику, выгиб, толщина)
        (2, (-6.2, -18.0), 1.4, 3.15),
        (3, (-5.6, -19.6), 1.5, 2.95),
        (4, (-4.6, -20.2), 1.5, 2.7),
        (5, (-1.8, -19.4), 1.4, 2.45),
        (6, (-1.6, -17.6), 1.3, 2.2),
        (7, (-2.0, -14.6), 1.1, 1.95),
    ]
    for i, (dx, dy), bow, r in ribs:
        c = v2(*NECK_BACK[i])
        a = v2(*NECK_BACK[max(0, i - 1)])
        b = v2(*NECK_BACK[i + 1])
        down = -left(unit(b - a))
        root = c + down * 1.6
        p.add(rib(root, root + v2(dx, dy), bow, r))
    return p


def tail():
    """Хвост: восемь позвонков, к кончику мельче."""
    p = Part("хвост")
    sizes = [2.0, 1.9, 1.78, 1.66, 1.54, 1.42, 1.3, 1.18]
    p.add(spine(TAIL, sizes, rod=0.55))
    return p


def arm():
    """Передняя лапа: плечевая кость и кисть с тремя когтями."""
    p = Part("передняя лапа")
    shoulder, wrist = (0.0, 0.0), (-17.0, -12.4)
    p.add(dog_bone(shoulder, wrist, r=1.6, lobe_r=1.95))
    w = v2(*wrist)
    for ang in (-150, -178, 152):          # веер пальцев вниз-влево
        u = v2(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        base = w + u * 1.2
        tip = w + u * 7.6
        ctrl = w + u * 4.6 + left(u) * -1.2
        p.add(RoundCone(a=p3(w), b=p3(base), ra=1.5, rb=1.2, k=0.6))
        p.add(claw(base, ctrl, tip, r0=1.15, r1=0.6))
    return p


def leg_bent():
    """Задняя лапа, согнутая: бедро вниз, голень влево, стопа с когтями."""
    p = Part("задняя лапа согнутая")
    hip, knee, ankle = (0.0, 0.0), (6.5, -19.5), (-17.5, -22.6)
    p.add(dog_bone(hip, knee, r=1.8, lobe_r=2.15))
    p.add(dog_bone(knee, ankle, r=1.7, lobe_r=2.05))
    a = v2(*ankle)
    for ang in (-140, -165, 168):
        u = v2(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        base = a + u * 1.6
        tip = a + u * 8.2
        ctrl = a + u * 5.0 + left(u) * -1.3
        p.add(RoundCone(a=p3(a), b=p3(base), ra=1.6, rb=1.25, k=0.6))
        p.add(claw(base, ctrl, tip, r0=1.2, r1=0.62))
    return p


def leg_straight():
    """Задняя лапа, вытянутая: одна длинная кость и стопа."""
    p = Part("задняя лапа вытянутая")
    top, ankle = (0.0, 0.0), (20.5, -13.2)
    p.add(dog_bone(top, ankle, r=1.8, lobe_r=2.15))
    a = v2(*ankle)
    for ang in (-60, -90, -118):
        u = v2(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        base = a + u * 1.6
        tip = a + u * 8.0
        ctrl = a + u * 4.9 + left(u) * 1.3
        p.add(RoundCone(a=p3(a), b=p3(base), ra=1.6, rb=1.25, k=0.6))
        p.add(claw(base, ctrl, tip, r0=1.2, r1=0.62))
    return p


def finds():
    """Россыпь «находок» для раскопок: косточка, позвонок и коготь."""
    parts = []
    b = Part("находка косточка")
    b.add(dog_bone((0, 0), (15, 0), r=1.5, lobe_r=1.85))
    parts.append(b)
    v = Part("находка позвонок")
    v.add(vertebra((0, 0), v2(1, 0), 2.6))
    parts.append(v)
    c = Part("находка коготь")
    c.add(claw((0, 0), (5.5, 2.4), (10.5, -1.5), r0=2.0, r1=0.75, n=8, k=0.4))
    parts.append(c)
    return parts


# Где лежит каждая деталь в собранном скелете (сдвиг и поворот, мм/градусы).
# Нужно для схемы раскладки и картинок — сами STL экспортируются как есть.
LAYOUT = {
    "череп": ((0, 0), 0),
    "позвоночник с рёбрами": ((0, 0), 0),
    "хвост": ((0, 0), 0),
    "передняя лапа": ((44.5, 3.0), 0),
    "задняя лапа вытянутая": ((28.5, -15.5), 0),
    "задняя лапа согнутая": ((84.0, -12.5), 0),
    "находка косточка": ((128.0, 8.0), 25),
    "находка позвонок": ((10.0, -30.0), 0),
    "находка коготь": ((116.0, -40.0), -20),
}


def build(voxel=0.1):
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [skull(), spine_ribs(), tail(), arm(), leg_bent(), leg_straight(), *finds()]
    report = {}
    for part in parts:
        t = time.time()
        # череп детальнее (зубы), остальным кострям хватит 60 тыс.: рёбра
        # сетки ~0.3 мм — мельче, чем кладёт сопло 0.4
        pts, faces, rep = part.mesh(voxel=voxel,
                                    max_tris=90_000 if part.name == "череп" else 60_000)
        lo, hi = pts.min(0), pts.max(0)
        rep["size_mm"] = [round(float(v), 2) for v in hi - lo]
        rep["min_z"] = round(float(lo[2]), 4)
        rep["sec"] = round(time.time() - t, 1)
        report[part.name] = rep
        write_stl(OUT / f"{part.name}.stl", pts, faces)
        print(f"PART {part.name:24s} {json.dumps(rep, ensure_ascii=False)}")


if __name__ == "__main__":
    build()
