#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Превью STL в PNG без OpenGL.

OpenSCAD на сервере без видеокарты отдаёт пустой PNG, поэтому картинки
рисуем сами: изометрическая проекция + плоское затенение по нормали,
треугольники выводятся в порядке удаления от камеры (алгоритм художника).

    python preview.py "Готовые модели/ДИМА_7.8.stl" -o превью.png
    python preview.py a.stl b.stl --labels "мой" "эталон" -o сравнение.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_names import read_stl  # noqa: E402

LIGHT = np.array([-0.3, -0.6, 0.75])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def rotation(azim_deg: float, elev_deg: float) -> np.ndarray:
    a, e = np.radians(azim_deg), np.radians(elev_deg)
    rz = np.array([[np.cos(a), -np.sin(a), 0],
                   [np.sin(a), np.cos(a), 0],
                   [0, 0, 1]])
    rx = np.array([[1, 0, 0],
                   [0, np.cos(e), -np.sin(e)],
                   [0, np.sin(e), np.cos(e)]])
    return rx @ rz


def draw(ax, tris: np.ndarray, azim: float, elev: float, base_rgb) -> None:
    rot = rotation(azim, elev)
    v = tris @ rot.T                       # (n, 3, 3) в системе камеры

    e1 = v[:, 1] - v[:, 0]
    e2 = v[:, 2] - v[:, 0]
    nrm = np.cross(e1, e2)
    ln = np.linalg.norm(nrm, axis=1)
    ln[ln == 0] = 1.0
    nrm /= ln[:, None]

    facing = nrm[:, 1] < 0                 # камера смотрит вдоль +Y
    v, nrm = v[facing], nrm[facing]

    shade = np.clip(nrm @ LIGHT, 0, 1) * 0.65 + 0.35
    colors = np.clip(np.array(base_rgb)[None, :] * shade[:, None], 0, 1)

    order = np.argsort(v[:, :, 1].mean(axis=1))[::-1]
    polys = v[order][:, :, [0, 2]]

    ax.add_collection(PolyCollection(polys, facecolors=colors[order],
                                     edgecolors="none", antialiaseds=True))
    xy = polys.reshape(-1, 2)
    pad = 0.05 * (xy[:, 0].max() - xy[:, 0].min())
    ax.set_xlim(xy[:, 0].min() - pad, xy[:, 0].max() + pad)
    ax.set_ylim(xy[:, 1].min() - pad, xy[:, 1].max() + pad)
    ax.set_aspect("equal")
    ax.axis("off")


def main() -> None:
    ap = argparse.ArgumentParser(description="Отрисовка STL в PNG.")
    ap.add_argument("stl", nargs="+", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("preview.png"))
    ap.add_argument("--labels", nargs="*", default=None)
    ap.add_argument("--azim", type=float, default=-30.0)
    ap.add_argument("--elev", type=float, default=62.0)
    ap.add_argument("--color", nargs=3, type=float, default=(1.0, 0.62, 0.10))
    args = ap.parse_args()

    labels = args.labels or [p.stem for p in args.stl]
    n = len(args.stl)
    fig, axes = plt.subplots(n, 1, figsize=(11, 2.9 * n), facecolor="#1c1c1c")
    axes = np.atleast_1d(axes)

    for ax, path, label in zip(axes, args.stl, labels):
        tris = np.array(read_stl(path), dtype=float)
        lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
        tris -= (lo + hi) / 2
        draw(ax, tris, args.azim, args.elev, args.color)
        ax.set_title(
            f"{label}   {hi[0]-lo[0]:.2f} × {hi[1]-lo[1]:.2f} × {hi[2]-lo[2]:.2f} мм",
            color="#dddddd", fontsize=11, pad=6,
        )

    fig.tight_layout()
    fig.savefig(args.out, dpi=130, facecolor=fig.get_facecolor())
    print(f"сохранено: {args.out}")


if __name__ == "__main__":
    main()
