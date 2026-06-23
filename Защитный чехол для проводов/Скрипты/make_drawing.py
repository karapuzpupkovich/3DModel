# -*- coding: utf-8 -*-
"""
Чертёж защитного чехла кабеля V3 (PLA): 3 ортогональных вида (HLR-проекции
FreeCAD) + изометрия + основные размеры. Экспорт в PDF и PNG.

Запуск:
  "C:/Program Files/FreeCAD 1.1/bin/python.exe" make_drawing.py
"""
import os
import FreeCAD
import Part
import TechDraw

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(_PROOT, "Готовые модели", "V1 — чехол")
STEP = os.path.join(OUT, "CableProtector.step")
STL = os.path.join(OUT, "CableProtector.stl")

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
    vis = groups[0] if len(groups) > 0 else None
    hid = groups[5] if len(groups) > 5 else None
    return vis, hid


def _map(pl, swap, fh, fv):
    if swap:
        return [(p[1] * fh, p[0] * fv) for p in pl]
    return [(p[0] * fh, p[1] * fv) for p in pl]


def draw_view(ax, shape, direction, title, swap=False, fh=1, fv=1):
    vis, hid = project(shape, direction)
    for pl in polylines(hid):
        m = _map(pl, swap, fh, fv)
        ax.plot([p[0] for p in m], [p[1] for p in m], color=GREY, lw=0.6, ls=(0, (4, 3)))
    for pl in polylines(vis):
        m = _map(pl, swap, fh, fv)
        ax.plot([p[0] for p in m], [p[1] for p in m], color="black", lw=1.3)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.axis("off")


def dim_h(ax, x1, x2, y, text, off=0):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=1.0))
    ax.text((x1 + x2) / 2, y + off + 0.6, text, color=RED, ha="center",
            va="bottom", fontsize=8.5)


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
            tri = [struct.unpack("<3f", f.read(12)) for _v in range(3)]
            tris.append(tri)
            f.read(2)
    coll = Poly3DCollection(tris, facecolor="#c9d4e0", edgecolor="#5a6675",
                            linewidths=0.15, alpha=1.0)
    ax.add_collection3d(coll)
    allp = np.array([p for t in tris for p in t])
    ax.set_xlim(allp[:, 0].min(), allp[:, 0].max())
    ax.set_ylim(-25, 25)
    ax.set_zlim(-25, 25)
    ax.set_box_aspect((float(np.ptp(allp[:, 0])), 50, 50))
    ax.view_init(elev=22, azim=-60)
    ax.set_title("Изометрия", fontsize=11, fontweight="bold")
    ax.set_axis_off()


def main():
    shape = Part.Shape()
    shape.read(STEP)

    fig = plt.figure(figsize=(16.5, 11.7))  # A3 landscape
    fig.suptitle("Защитный чехол-фиксатор зарядного кабеля USB-C — CableProtector V3 (PLA)",
                 fontsize=15, fontweight="bold")

    # --- Вид сбоку (проекция вдоль Y): плоскость X-Z -------------------------
    ax_side = fig.add_axes([0.05, 0.55, 0.55, 0.36])
    draw_view(ax_side, shape, (0, 1, 0), "Вид сбоку  (профиль X–Z)", swap=True)
    dim_h(ax_side, 0, 52, -8.5, "52.0  (общая длина, −10 к v2)")
    dim_h(ax_side, 0, 14, -6.0, "14.0  (гнездо)")
    dim_h(ax_side, 14, 52, -6.0, "38.0  (канал + 3 фиксатора)")
    ext(ax_side, 0, -5.2, -9.0); ext(ax_side, 14, -5.2, -9.0); ext(ax_side, 52, -5.2, -9.0)
    dim_v(ax_side, -5.15, 5.15, 54.5, "10.3", side=1)
    ax_side.text(1.0, 6.6, "перёд ОТКРЫТ\n(бубышка наружу)", color=RED, fontsize=7.5, ha="left")
    ax_side.text(38, 6.6, "3 перегородки: паз 3.2\n+ дно Ø4.0 (хват Ø4)", color=RED, fontsize=7.0, ha="center")

    # --- Вид сверху (проекция вдоль Z): плоскость X-Y ------------------------
    ax_top = fig.add_axes([0.05, 0.10, 0.55, 0.34])
    draw_view(ax_top, shape, (0, 0, 1), "Вид сверху  (X–Y): люлька + drop-in канал", swap=False)
    dim_v(ax_top, -7.15, 7.15, 54.5, "14.3", side=1)
    ax_top.text(7, 0, "люлька 10.3\n(вставка с\nширокой стороны)", color=RED, fontsize=7.0, ha="center", va="center")
    ax_top.text(33, 3.2, "паз 4.6 (укладка кабеля)", color=RED, fontsize=7.0, ha="center", va="center")
    ax_top.text(38, -3.6, "перемычки 3.2 ×3", color=RED, fontsize=7.0, ha="center", va="center")

    # --- Вид с торца (проекция вдоль X): плоскость Y-Z -----------------------
    ax_end = fig.add_axes([0.66, 0.55, 0.30, 0.36])
    draw_view(ax_end, shape, (1, 0, 0), "Вид с торца  (Y–Z, сечение гнезда)", swap=True)
    dim_h(ax_end, -7.15, 7.15, -8.0, "14.3")
    dim_v(ax_end, -5.15, 5.15, 8.8, "10.3", side=1)
    dim_h(ax_end, -5.15, 5.15, 5.3, "гнездо 10.3 × 6.3 (R2.5)")
    ax_end.text(0, -10.3, "стенка 2.0 мм · открытая люлька сверху",
                color=RED, fontsize=8, ha="center")

    # --- Изометрия -----------------------------------------------------------
    ax_iso = fig.add_axes([0.63, 0.06, 0.34, 0.40], projection="3d")
    draw_iso(ax_iso)

    info = (
        "МАТЕРИАЛ: PLA (жёсткий). Печать пазом ВВЕРХ, без поддержек,\n"
        "сопло 0.4, слой 0.2, стенки 3, заполнение 30–40%.\n"
        "\n"
        "Перёд ОТКРЫТ — бубышку оставляем чуть снаружи (USB-C в порт).\n"
        "Бубышка (замер):  10 × 6 × 17 → гнездо 10.3 × 6.3 (зазор 0.15/ст)\n"
        "Провод Ø4 → канал Ø4.6, паз укладки 4.6 мм по всей длине.\n"
        "Фиксация: 3 перегородки (паз 3.2 + дно Ø4.0) на X=30/38/46.\n"
        "Монтаж: уложить кабель сверху в паз, продавить под 3 перемычки."
    )
    fig.text(0.05, 0.955, info, fontsize=8.5, va="top", family="monospace",
             bbox=dict(boxstyle="round", fc="#f4f4f0", ec="#cccccc"))

    png = os.path.join(OUT, "CableProtector_drawing.png")
    pdf = os.path.join(OUT, "CableProtector_drawing.pdf")
    fig.savefig(png, dpi=130)
    fig.savefig(pdf)
    print("Чертёж сохранён:\n  %s\n  %s" % (png, pdf))


main()
