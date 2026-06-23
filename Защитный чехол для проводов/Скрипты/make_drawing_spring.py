# -*- coding: utf-8 -*-
"""
Чертёж V2 — пружинного (серпантинного) чехла: 3 вида + изометрия + размеры.

Запуск:
  "C:/Program Files/FreeCAD 1.1/bin/python.exe" make_drawing_spring.py
"""
import os
import FreeCAD
import Part
import TechDraw

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_PROOT, "Готовые модели", "V2 — пружина")
STEP = os.path.join(OUT, "CableProtector_Spring.step")
STL = os.path.join(OUT, "CableProtector_Spring.stl")

RED = "#b02828"
GREY = "#888888"


def polylines(group):
    out = []
    if group is None:
        return out
    try:
        edges = group.Edges
    except Exception:
        return out
    for e in edges:
        try:
            pts = e.discretize(Number=40)
        except Exception:
            continue
        out.append([(p.x, p.y) for p in pts])
    return out


def project(shape, direction):
    groups = TechDraw.projectEx(shape, FreeCAD.Vector(*direction))
    return (groups[0] if len(groups) > 0 else None,
            groups[5] if len(groups) > 5 else None)


def _map(pl, swap):
    return [(p[1], p[0]) for p in pl] if swap else [(p[0], p[1]) for p in pl]


def draw_view(ax, shape, direction, title, swap=False):
    vis, hid = project(shape, direction)
    for pl in polylines(hid):
        m = _map(pl, swap)
        ax.plot([p[0] for p in m], [p[1] for p in m], color=GREY, lw=0.6, ls=(0, (4, 3)))
    for pl in polylines(vis):
        m = _map(pl, swap)
        ax.plot([p[0] for p in m], [p[1] for p in m], color="black", lw=1.3)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.axis("off")


def dim_h(ax, x1, x2, y, text):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=1.0))
    ax.text((x1 + x2) / 2, y + 0.6, text, color=RED, ha="center", va="bottom", fontsize=8.5)


def dim_v(ax, y1, y2, x, text, side=1):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=1.0))
    ax.text(x + 0.6 * side, (y1 + y2) / 2, text, color=RED, va="center",
            ha="left" if side > 0 else "right", fontsize=8.5, rotation=90)


def ext(ax, x, y0, y1):
    ax.plot([x, x], [y0, y1], color=RED, lw=0.5)


def draw_iso(ax):
    import struct
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    tris = []
    with open(STL, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        for _ in range(n):
            f.read(12)
            tris.append([struct.unpack("<3f", f.read(12)) for _v in range(3)])
            f.read(2)
    coll = Poly3DCollection(tris, facecolor="#cfe0c9", edgecolor="#5a6675",
                            linewidths=0.12, alpha=1.0)
    ax.add_collection3d(coll)
    allp = np.array([p for t in tris for p in t])
    ax.set_xlim(allp[:, 0].min(), allp[:, 0].max())
    ax.set_ylim(-25, 25)
    ax.set_zlim(-25, 25)
    ax.set_box_aspect((float(np.ptp(allp[:, 0])), 50, 50))
    ax.view_init(elev=24, azim=-62)
    ax.set_title("Изометрия — серпантинная цепь", fontsize=11, fontweight="bold")
    ax.set_axis_off()


def main():
    shape = Part.Shape()
    shape.read(STEP)

    fig = plt.figure(figsize=(16.5, 11.7))
    fig.suptitle("V2 — Пружинный (серпантинный) чехол кабеля USB-C — CableProtector_Spring (PLA)",
                 fontsize=15, fontweight="bold")

    ax_side = fig.add_axes([0.05, 0.55, 0.55, 0.36])
    draw_view(ax_side, shape, (0, 1, 0), "Вид сбоку  (профиль X–Z)", swap=True)
    dim_h(ax_side, 0, 50, -8.5, "50.0  (общая длина)")
    dim_h(ax_side, 0, 14, -6.0, "14.0  (гнездо)")
    dim_h(ax_side, 21, 50, -6.0, "серпантин: шаг 4.0, кольцо 2.2")
    ext(ax_side, 0, -5.2, -9.0); ext(ax_side, 14, -5.2, -9.0); ext(ax_side, 50, -5.2, -9.0)
    dim_v(ax_side, -5.15, 5.15, 52.5, "10.3", side=1)
    ax_side.text(1.0, 6.6, "перёд ОТКРЫТ\n(бубышка наружу)", color=RED, fontsize=7.5, ha="left")

    ax_top = fig.add_axes([0.05, 0.10, 0.55, 0.34])
    draw_view(ax_top, shape, (0, 0, 1), "Вид сверху  (X–Y): гнездо + серпантин (мостики L/R)", swap=False)
    dim_v(ax_top, -7.15, 7.15, 52.5, "14.3", side=1)
    ax_top.text(7, 0, "люлька 10.3", color=RED, fontsize=7.0, ha="center", va="center")
    ax_top.text(35, 0, "цепь колец, мостики поочерёдно\nслева/справа → пружинит вбок",
                color=RED, fontsize=7.0, ha="center", va="center")

    ax_end = fig.add_axes([0.66, 0.55, 0.30, 0.36])
    draw_view(ax_end, shape, (1, 0, 0), "Вид с торца  (Y–Z, сечение гнезда)", swap=True)
    dim_h(ax_end, -7.15, 7.15, -8.0, "14.3")
    dim_v(ax_end, -5.15, 5.15, 8.8, "10.3", side=1)
    dim_h(ax_end, -5.15, 5.15, 5.3, "гнездо 10.3 × 6.3")
    ax_end.text(0, -10.3, "кольцо 10.2 × 7.6 · канал Ø4.4 (открыт сверху)",
                color=RED, fontsize=8, ha="center")

    ax_iso = fig.add_axes([0.63, 0.06, 0.34, 0.40], projection="3d")
    draw_iso(ax_iso)

    info = (
        "МАТЕРИАЛ: PLA (жёсткий). Печать пазом ВВЕРХ, без поддержек.\n"
        "За основу — форма/технология 'На основе этой модели.stl':\n"
        "сплошное гнездо спереди + гибкая серпантинная цепь колец.\n"
        "\n"
        "Изменены ТОЛЬКО размеры под пользователя:\n"
        "  бубышка 10×6 → гнездо 10.3×6.3 (зазор 0.15/ст, R2.5)\n"
        "  провод Ø4 → открытый канал Ø4.4 (укладка сверху)\n"
        "Цепь из 7 колец, мостики чередуются L/R → защита от перегиба.\n"
        "Монтаж: уложить кабель в канал, бубышку — в переднюю люльку."
    )
    fig.text(0.05, 0.955, info, fontsize=8.5, va="top", family="monospace",
             bbox=dict(boxstyle="round", fc="#f0f4f0", ec="#cccccc"))

    png = os.path.join(OUT, "CableProtector_Spring_drawing.png")
    pdf = os.path.join(OUT, "CableProtector_Spring_drawing.pdf")
    fig.savefig(png, dpi=130)
    fig.savefig(pdf)
    print("Чертёж V2 сохранён:\n  %s\n  %s" % (png, pdf))


main()
