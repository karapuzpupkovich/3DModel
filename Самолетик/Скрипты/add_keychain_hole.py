# -*- coding: utf-8 -*-
"""
Добавляет в киль (хвост) фюзеляжа самолётика сквозное отверстие под верёвочку,
чтобы использовать модель как брелок.

Исходник:  Trup.stl.stl   (профиль самолёта, плита толщиной 10 мм, лежит в плоскости XY)
Результат: Trup_brelok.stl

Система координат исходного STL:
    Y — продольная ось самолёта: Y~100 — нос, Y~178 — хвост
    X — вертикаль самолёта:      X~135 — низ (брюхо), X~162 — верх (кончик киля)
    Z — толщина фюзеляжа 0..10 мм (при печати — вертикаль стола)

Отверстие сверлится вдоль Z, т.е. насквозь через 10 мм фюзеляжа.
При печати оно оказывается вертикальным — печатается идеально круглым, без поддержек.
С обеих сторон снята фаска 45°, чтобы верёвочка не перетиралась об острую кромку.

Запуск:  python "Скрипты/add_keychain_hole.py"
Зависимости: trimesh, manifold3d, numpy, shapely, rtree, scipy
"""

import os
import numpy as np
import trimesh

# ----------------------------------------------------------------------------
# ПАРАМЕТРЫ (менять здесь)
# ----------------------------------------------------------------------------
HOLE_D = 3.0        # диаметр отверстия, мм (верёвочка 2.2 мм; FDM печатает отверстия
                    # на 0.1-0.3 мм уже номинала, поэтому 3.0 -> по факту ~2.8)
CHAMFER = 0.5       # фаска 45° с обеих сторон, мм
HOLE_X = 157.30     # положение центра отверстия в киле
HOLE_Y = 172.96     # (проверено: до ближайшей стенки 4.09 мм)

SRC = "Trup.stl.stl"
DST = "Trup_brelok.stl"

# ----------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def build_cutter(diameter, chamfer, z_lo, z_hi, sections=96):
    """Тело вычитания: цилиндр + конические фаски 45° сверху и снизу."""
    r = diameter / 2.0
    rc = r + chamfer
    over = 1.0  # запас за пределы детали
    profile = np.array([
        [0.0,    z_lo - over],
        [rc,     z_lo - over],
        [rc,     z_lo],
        [r,      z_lo + chamfer],
        [r,      z_hi - chamfer],
        [rc,     z_hi],
        [rc,     z_hi + over],
        [0.0,    z_hi + over],
    ])
    return trimesh.creation.revolve(profile, sections=sections)


def main():
    src_path = os.path.join(ROOT, SRC)
    mesh = trimesh.load(src_path, process=True)
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    trimesh.repair.fix_normals(mesh)
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)
    print(f"исходник:  {SRC}  граней={len(mesh.faces)}  замкнут={mesh.is_watertight}"
          f"  объём={mesh.volume:.1f} куб.мм")

    z_lo, z_hi = mesh.bounds[0][2], mesh.bounds[1][2]

    cutter = build_cutter(HOLE_D, CHAMFER, z_lo, z_hi)
    cutter.apply_translation([HOLE_X, HOLE_Y, 0.0])

    result = trimesh.boolean.difference([mesh, cutter], engine="manifold")
    result.merge_vertices()
    trimesh.repair.fix_normals(result)

    removed = mesh.volume - result.volume
    print(f"результат: {DST}  граней={len(result.faces)}  замкнут={result.is_watertight}"
          f"  объём={result.volume:.1f} куб.мм  (снято {removed:.1f} куб.мм)")

    dst_path = os.path.join(ROOT, DST)
    result.export(dst_path)
    print(f"сохранено: {dst_path}")


if __name__ == "__main__":
    main()
