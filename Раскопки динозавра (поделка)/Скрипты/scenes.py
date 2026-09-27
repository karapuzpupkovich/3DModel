# -*- coding: utf-8 -*-
"""
Картинки для README и проверки пропорций.

  превью скелета.jpg     — скелет на песке, как на образце
  превью табличек.jpg    — табличка и карта уже «закрашенные»
  схема раскладки.jpg    — вид сверху с номерами деталей: как раскладывать
  диорама целиком.jpg    — коробка, песок, всё напечатанное и человечек
                           из желудей в натуральную величину: пропорции

    python scenes.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(HERE))
from build_skeleton import LAYOUT  # noqa: E402
from raster import Camera, render, save  # noqa: E402

SKEL = PROJECT / "Готовые модели" / "Скелет"
PLAQ = PROJECT / "Готовые модели" / "Таблички"
IMG = PROJECT / "Готовые модели" / "Картинки"

BONE = (0.93, 0.88, 0.76)
WOOD = (0.80, 0.62, 0.40)
PAPER = (0.86, 0.76, 0.56)
INK = (0.12, 0.08, 0.05)
SAND = (0.78, 0.63, 0.44)

# Номера деталей на схеме — в порядке, в котором их удобно раскладывать
ORDER = ["череп", "позвоночник с рёбрами", "хвост", "передняя лапа",
         "задняя лапа вытянутая", "задняя лапа согнутая",
         "находка косточка", "находка позвонок", "находка коготь"]


def placed(name, dx=0.0, dy=0.0, ang=0.0):
    m = trimesh.load(SKEL / f"{name}.stl")
    (lx, ly), la = LAYOUT[name]
    T = trimesh.transformations.rotation_matrix(math.radians(la + ang), (0, 0, 1))
    T[:3, 3] = (lx + dx, ly + dy, 0)
    m.apply_transform(T)
    return m


def obj(m, color, spec=0.15, smooth=True, paint=None):
    o = {"V": m.vertices, "F": m.faces, "color": color, "spec": spec, "smooth": smooth}
    if paint:
        o["paint"] = paint
    return o


def skeleton_objs(dx=0.0, dy=0.0):
    return [obj(placed(n, dx, dy), BONE) for n in ORDER]


# --------------------------------------------------------------------------- #
#  Условный человечек из желудей (только для картинки пропорций)
# --------------------------------------------------------------------------- #
def ellipsoid(c, r, subdiv=3):
    m = trimesh.creation.icosphere(subdivisions=subdiv)
    m.apply_scale(r)
    m.apply_translation(c)
    return m


def twig(a, b, r=1.4):
    a, b = np.array(a, float), np.array(b, float)
    return trimesh.creation.cylinder(radius=r, segment=[a, b], sections=14)


def acorn_man(x, y):
    """
    Рост ~70 мм, как у фигурки на образце в натуральную величину:
    тело — жёлудь ~20×26 мм, голова — орех ~20 мм, шляпа — плюска ~27 мм.
    Он с кисточкой и рюкзаком-скорлупкой, стоит лицом к зрителю (−Y).
    """
    nut, cap, stick, bristle = (0.55, 0.31, 0.13), (0.45, 0.33, 0.20), (0.33, 0.22, 0.14), (0.90, 0.84, 0.66)
    parts = []
    parts.append((ellipsoid((x, y, 31), (10.5, 9.5, 13)), nut))
    parts.append((ellipsoid((x, y - 1, 53), (10.5, 10, 10)), (0.62, 0.38, 0.18)))
    parts.append((ellipsoid((x, y - 1, 60), (13.5, 13, 6.5)), cap))
    parts.append((twig((x, y - 1, 65), (x + 1.5, y - 1, 71), 1.0), stick))
    parts.append((ellipsoid((x + 1, y + 11, 36), (8.5, 5, 10)), (0.50, 0.38, 0.24)))    # рюкзак
    for sx in (-5, 5):                                                                 # ноги
        parts.append((twig((x + sx, y, 20), (x + sx * 1.3, y - 1, 5), 1.5), stick))
        parts.append((ellipsoid((x + sx * 1.3, y - 4, 3.5), (4.5, 6.5, 3.5)), nut))
    parts.append((twig((x - 9, y - 2, 38), (x - 20, y - 8, 27)), stick))                # руки
    parts.append((ellipsoid((x - 21, y - 9, 26), (4, 4, 4.5)), nut))
    parts.append((twig((x + 9, y - 2, 38), (x + 17, y - 9, 30)), stick))
    parts.append((ellipsoid((x + 18, y - 10, 29), (4, 4, 4.5)), nut))
    parts.append((twig((x - 21, y - 11, 27), (x - 25, y - 20, 4), 1.2), (0.85, 0.70, 0.45)))  # кисточка
    parts.append((ellipsoid((x - 25.5, y - 21, 3.5), (2.6, 2.6, 4.2)), bristle))
    return [obj(m, c, spec=0.3) for m, c in parts]


def box(c, half):
    m = trimesh.creation.box(extents=np.array(half) * 2)
    m.apply_translation(c)
    return m


def tray(x0, x1, y0, y1, h=30.0, t=2.5):
    card = (0.66, 0.51, 0.35)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, d = x1 - x0, y1 - y0
    walls = [box((cx, y0 - t / 2, h / 2 - 2), (w / 2 + t, t / 2, h / 2)),
             box((cx, y1 + t / 2, h / 2 - 2), (w / 2 + t, t / 2, h / 2)),
             box((x0 - t / 2, cy, h / 2 - 2), (t / 2, d / 2, h / 2)),
             box((x1 + t / 2, cy, h / 2 - 2), (t / 2, d / 2, h / 2))]
    return [obj(m, card, spec=0.05, smooth=False) for m in walls]


def stones(pts, seed=4):
    rng = np.random.default_rng(seed)
    out = []
    for x, y, s in pts:
        m = ellipsoid((x, y, s * 0.25), (s, s * 0.8, s * 0.55), subdiv=2)
        m.vertices += rng.normal(0, s * 0.08, m.vertices.shape)
        out.append(obj(m, (0.48, 0.47, 0.45), spec=0.1, smooth=False))
    return out


# --------------------------------------------------------------------------- #
#  Сцены
# --------------------------------------------------------------------------- #
def scene_skeleton():
    img = render(skeleton_objs(), Camera((64, -16, 0), 175, 55, -96, 34, 1500, 850),
                 ground={"z": 0, "color": SAND}, ss=2, shadow_res=0.25)
    save(img, IMG / "превью скелета.jpg")


def scene_plaques():
    sign = trimesh.load(PLAQ / "табличка с колышком.stl")
    mp = trimesh.load(PLAQ / "карта раскопок.stl")
    mp.apply_translation((66, 30, 0))
    objs = [obj(sign, WOOD, 0.1, False, {"z_below": 2.9, "color": INK}),
            obj(mp, PAPER, 0.1, False, {"z_below": 2.3, "color": INK})]
    img = render(objs, Camera((62, 45, 0), 245, 74, -90, 32, 1400, 1100),
                 ground={"z": 0, "color": (0.60, 0.57, 0.53)}, ss=2, shadow_res=0.2)
    save(img, IMG / "превью табличек.jpg")


# Куда вынести номер детали на схеме: точка на детали и сдвиг кружка, мм.
# Кружок не должен закрывать саму кость — особенно мелкие находки.
LABELS = {
    "череп":                 ((20, 16), (-2, 15)),
    "позвоночник с рёбрами": ((66, 3), (4, 14)),
    "хвост":                 ((110, -19), (12, 9)),
    "передняя лапа":         ((36, -3), (-9, 11)),
    "задняя лапа вытянутая": ((40, -23), (-14, -9)),
    "задняя лапа согнутая":  ((80, -33.4), (0, -14)),
    "находка косточка":      ((128, 8), (0, 11)),
    "находка позвонок":      ((10, -30), (0, -11)),
    "находка коготь":        ((116, -40), (14, -6)),
}


def scene_layout():
    """Вид сверху с номерами — схема, по которой ребёнок раскладывает кости."""
    cam = Camera((62, -13, 0), 250, 89.9, -90, 30, 1500, 950)
    img = render(skeleton_objs(), cam, ground={"z": 0, "color": SAND}, ss=2, shadow_res=0.3)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("arialbd.ttf", 30)
        small = ImageFont.truetype("arial.ttf", 25)
    except OSError:
        font = small = ImageFont.load_default()

    def px(p):
        x, y, _ = cam.project(np.array([[p[0], p[1], 2.0]]))
        return float(x[0]), float(y[0])

    legend = []
    for i, n in enumerate(ORDER, 1):
        (ax, ay), (ox, oy) = LABELS[n]
        a = px((ax, ay))
        b = px((ax + ox, ay + oy))
        dr.line([a, b], fill=(120, 30, 20), width=3)
        dr.ellipse([a[0] - 5, a[1] - 5, a[0] + 5, a[1] + 5], fill=(120, 30, 20))
        r = 21
        dr.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=(180, 40, 30),
                   outline=(255, 255, 255), width=3)
        dr.text(b, str(i), fill=(255, 255, 255), font=font, anchor="mm")
        legend.append(f"{i} — {n}")
    # легенда — полосой внизу, в три колонки: сверху её закрывал череп
    cols, rows = 3, math.ceil(len(legend) / 3)
    x0, y0, cw, rh = 16, im.height - rows * 32 - 30, (im.width - 32) // 3, 32
    dr.rectangle([x0 - 4, y0 - 12, im.width - 12, im.height - 12],
                 fill=(250, 244, 232), outline=(150, 120, 90), width=2)
    for k, line in enumerate(legend):
        c, r_ = divmod(k, rows)
        dr.text((x0 + 14 + c * cw, y0 + r_ * rh), line, fill=(40, 25, 10), font=small)
    im.save(IMG / "схема раскладки.jpg", quality=92, optimize=True)


def scene_diorama():
    """
    Всё вместе в коробке 250×180 мм. Человечек — в натуральную величину,
    поэтому по картинке видно, что напечатанное с ним в одном масштабе.
    """
    x0, x1, y0, y1 = -55, 195, -95, 85
    objs = []
    objs += skeleton_objs()
    objs += tray(x0, x1, y0, y1)
    # табличка воткнута в песок: колышек на 25 мм в глубине, лицом к зрителю
    tf = trimesh.transformations
    M = (tf.translation_matrix((-18, 58, 0))
         @ tf.rotation_matrix(math.radians(-8), (0, 0, 1))
         @ tf.rotation_matrix(math.radians(90), (1, 0, 0))
         @ tf.translation_matrix((-27, -25, -1.5)))           # центр колышка -> ось
    sign = trimesh.load(PLAQ / "табличка с колышком.stl")
    sign.apply_transform(M)
    face = M[:3, :3] @ np.array([0, 0, 1.0])                   # куда смотрит лицо
    top = (M @ np.array([0, 0, 3.0, 1]))[:3]                   # точка лицевой плоскости
    objs.append(obj(sign, WOOD, 0.1, False,
                    {"dir": face.tolist(), "level": float(top @ face) - 0.1, "color": INK}))
    # карта лежит на земле справа спереди, не заезжая на хвост
    mp = trimesh.load(PLAQ / "карта раскопок.stl")
    mp.apply_translation((-30, -22, 0))
    mp.apply_transform(tf.rotation_matrix(math.radians(-14), (0, 0, 1)))
    mp.apply_translation((162, -52, 0))
    objs.append(obj(mp, PAPER, 0.1, False, {"z_below": 2.3, "color": INK}))
    objs += acorn_man(140, 42)
    objs += stones([(-35, -70, 9), (178, 60, 11), (-40, 20, 7), (185, -80, 8), (100, 70, 6)])
    cam = Camera((70, -5, 20), 430, 40, -92, 34, 1600, 1000)
    img = render(objs, cam, ground={"z": 0, "color": SAND, "rect": (x0, x1, y0, y1)},
                 ss=2, shadow_res=0.35, bg=(0.90, 0.86, 0.80))
    save(img, IMG / "диорама целиком.jpg")


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]
    for name, fn in (("skeleton", scene_skeleton), ("plaques", scene_plaques),
                     ("layout", scene_layout), ("diorama", scene_diorama)):
        if not only or name in only:
            fn()
            print("готово:", name)
