# -*- coding: utf-8 -*-
"""
Прорезает то же самое отверстие под верёвочку в проекте Bambu/Orca Studio,
чтобы можно было печатать сразу из готового проекта, а не пересобирать раскладку.

Исходник:  new_plane_xc.3mf        (не изменяется)
Результат: new_plane_brelok.3mf

Внутри 3mf фюзеляж лежит в «родной» ориентации самолёта (3D/Objects/object_5.model),
а на стол его кладёт матрица из <build><item objectid="2" transform="..."/>.
Скрипт читает эту матрицу, пересчитывает координаты отверстия из системы STL
(координаты стола) в локальную систему детали и вычитает то же тело с фасками.

Запуск: python "Скрипты/add_keychain_hole_3mf.py"
"""

import os
import re
import shutil
import zipfile

import numpy as np
import trimesh

from add_keychain_hole import HOLE_D, CHAMFER, HOLE_X, HOLE_Y, build_cutter

SRC_3MF = "new_plane_xc.3mf"
DST_3MF = "new_plane_brelok.3mf"
OBJ_FILE = "3D/Objects/object_5.model"   # фюзеляж (Trup)
OBJ_ID = "2"                             # его id в <build> и model_settings.config

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

VERT_RE = re.compile(r'<vertex x="([-\d.eE+]+)" y="([-\d.eE+]+)" z="([-\d.eE+]+)"\s*/>')
TRI_RE = re.compile(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"\s*/>')


def parse_object(xml_text):
    v = np.array(VERT_RE.findall(xml_text), dtype=np.float64)
    f = np.array(TRI_RE.findall(xml_text), dtype=np.int64)
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


def dump_object(xml_text, mesh):
    """Подставляет новую сетку в XML, сохраняя всё остальное."""
    verts = "\n".join(
        f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in mesh.vertices)
    tris = "\n".join(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces)
    out = re.sub(r"<vertices>.*?</vertices>",
                 "<vertices>\n" + verts + "\n    </vertices>", xml_text, flags=re.S)
    out = re.sub(r"<triangles>.*?</triangles>",
                 "<triangles>\n" + tris + "\n    </triangles>", out, flags=re.S)
    return out


def build_matrix(model_xml, objectid):
    """Матрица 3mf (построчная, p' = p*M + t) для нужного <item>."""
    m = re.search(r'<item objectid="%s"[^>]*transform="([^"]+)"' % objectid, model_xml)
    nums = [float(t) for t in m.group(1).split()]
    M = np.array(nums[:9], dtype=np.float64).reshape(3, 3)
    t = np.array(nums[9:12], dtype=np.float64)
    return M, t


def main():
    src = os.path.join(ROOT, SRC_3MF)
    dst = os.path.join(ROOT, DST_3MF)

    zin = zipfile.ZipFile(src)
    obj_xml = zin.read(OBJ_FILE).decode("utf-8")
    model_xml = zin.read("3D/3dmodel.model").decode("utf-8")
    settings = zin.read("Metadata/model_settings.config").decode("utf-8")

    mesh = parse_object(obj_xml)
    mesh.merge_vertices()
    print(f"фюзеляж в 3mf: вершин={len(mesh.vertices)} граней={len(mesh.faces)} "
          f"замкнут={mesh.is_watertight} объём={mesh.volume:.1f} куб.мм")

    M, t = build_matrix(model_xml, OBJ_ID)
    # ось отверстия на столе — Z; в локальной системе детали это ось,
    # соответствующая строке M, у которой z-компонента равна 1
    axis_row = int(np.argmax(np.abs(M[:, 2])))
    print(f"матрица из <build>: ось стола Z <- локальная ось {'xyz'[axis_row]}")

    # обратное преобразование точки со стола в локальные координаты детали
    Minv = np.linalg.inv(M)
    local = (np.array([HOLE_X, HOLE_Y, 0.0]) - t) @ Minv
    print(f"центр отверстия: стол ({HOLE_X}, {HOLE_Y}) -> локально "
          f"({local[0]:.3f}, {local[1]:.3f}, {local[2]:.3f})")

    lo, hi = mesh.bounds[0][axis_row], mesh.bounds[1][axis_row]
    cutter = build_cutter(HOLE_D, CHAMFER, lo, hi)      # ось цилиндра — Z
    # развернуть цилиндр вдоль нужной локальной оси и поставить в центр отверстия
    if axis_row == 1:                                    # ось Y
        cutter.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        cutter.apply_translation([local[0], 0.0, local[2]])
    elif axis_row == 0:                                  # ось X
        cutter.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]))
        cutter.apply_translation([0.0, local[1], local[2]])
    else:                                                # ось Z
        cutter.apply_translation([local[0], local[1], 0.0])

    result = trimesh.boolean.difference([mesh, cutter], engine="manifold")
    result.merge_vertices()
    trimesh.repair.fix_normals(result)
    print(f"после реза:    вершин={len(result.vertices)} граней={len(result.faces)} "
          f"замкнут={result.is_watertight} объём={result.volume:.1f} куб.мм "
          f"(снято {mesh.volume - result.volume:.1f} куб.мм)")

    new_obj = dump_object(obj_xml, result)
    n = len(result.faces)
    block = re.search(r'<object id="%s">.*?</object>' % OBJ_ID, settings, flags=re.S).group(0)
    new_block = block.replace('face_count="1104"', 'face_count="%d"' % n)
    new_settings = settings.replace(block, new_block)

    replace = {OBJ_FILE: new_obj.encode("utf-8"),
               "Metadata/model_settings.config": new_settings.encode("utf-8")}
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = replace.get(item.filename, zin.read(item.filename))
            zout.writestr(item, data)
    zin.close()
    print(f"сохранено: {dst}")

    # контроль: переводим результат на стол и сверяем с STL-версией
    plate = result.copy()
    plate.vertices = result.vertices @ M + t
    ref = trimesh.load(os.path.join(ROOT, "Trup_brelok.stl"), process=True)
    ref.merge_vertices()
    print(f"сверка со столом: габарит 3mf {np.round(plate.extents, 2).tolist()} "
          f"vs STL {np.round(ref.extents, 2).tolist()}; "
          f"объём {plate.volume:.1f} vs {ref.volume:.1f} куб.мм")


if __name__ == "__main__":
    main()
