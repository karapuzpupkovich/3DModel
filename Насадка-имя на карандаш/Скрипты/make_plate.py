#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Раскладка нескольких насадок на один стол A1 — один проект вместо 28 запусков.

Печать по одной штуке дорога не самим временем, а накладными расходами:
Bambu тратит ~6 минут подготовки плюс таймлапс на КАЖДЫЙ запуск, и это ещё
28 снятий детали со стола. Плита собирает всё в один проект.

Количество копий берётся из списка группы: если детей с одним именем двое,
на стол кладутся две штуки.

    python make_plate.py --csv "дети.csv" --rename ДМИТРИЙ=ДИМА
    python make_plate.py --csv "дети.csv" --per-plate 10   # разбить на плиты
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
import zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_3mf import (CONTENT_TYPES, CUT_INFO, MODEL_NS, MODEL_RELS, ROOT_RELS,
                      SLICE_INFO, bbox, load_profile, read_stl, weld)
from names_from_csv import read_names

PROJECT_DIR = Path(__file__).resolve().parent.parent

BED = 256.0        # A1: printable_area 256 x 256
MARGIN = 8.0       # отступ от края стола
GAP = 5.0          # зазор между деталями


# --------------------------------------------------------------------------- #
#  Упаковка
# --------------------------------------------------------------------------- #
def pack(items, bed: float = BED, margin: float = MARGIN, gap: float = GAP,
         per_plate: int | None = None):
    """
    Полочная упаковка: детали сортируются по ширине (Y) и раскладываются
    рядами. Насадки — длинные тонкие полоски, поэтому ряды получаются
    плотными, а обычный полочный алгоритм даёт результат близкий к
    оптимальному без всякой сложной эвристики.

    items: [(имя, длина X, ширина Y)], возвращает [[(имя, x, y), ...], ...]
    — по списку на каждую плиту, координаты центра детали.
    """
    usable = bed - 2 * margin
    too_big = [n for n, dx, dy in items if dx > usable or dy > usable]
    if too_big:
        sys.exit(f"Не влезает на стол: {', '.join(too_big)}")

    order = sorted(items, key=lambda it: (-it[2], -it[1]))
    plates, shelves, placed_on_plate = [], [], 0

    def shelves_height(sh):
        return sum(s["h"] for s in sh) + gap * max(0, len(sh) - 1)

    def flush():
        nonlocal shelves, placed_on_plate
        if shelves:
            plates.append(shelves)
        shelves, placed_on_plate = [], 0

    for name, dx, dy in order:
        if per_plate and placed_on_plate >= per_plate:
            flush()
        shelf = next((s for s in shelves if s["free"] >= dx + gap), None)
        if shelf is None:
            need = dy if not shelves else shelves_height(shelves) + gap + dy
            if need > usable:
                flush()
            shelf = {"h": dy, "free": usable, "items": []}
            shelves.append(shelf)
        shelf["items"].append((name, dx, dy))
        shelf["free"] -= dx + gap
        placed_on_plate += 1
    flush()

    out = []
    for sh in plates:
        coords, y = [], margin
        total_h = shelves_height(sh)
        y = (bed - total_h) / 2                      # ряды по центру стола
        for s in sh:
            row_w = sum(i[1] for i in s["items"]) + gap * (len(s["items"]) - 1)
            x = (bed - row_w) / 2                    # ряд по центру стола
            for name, dx, dy in s["items"]:
                coords.append((name, x + dx / 2, y + s["h"] / 2))
                x += dx + gap
            y += s["h"] + gap
        out.append(coords)
    return out


# --------------------------------------------------------------------------- #
#  Сборка 3MF с несколькими объектами
# --------------------------------------------------------------------------- #
def objects_model_xml(meshes) -> str:
    """Все сетки плиты в одном /3D/Objects/object_1.model."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>',
           ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
           ' <resources>']
    for m in meshes:
        out += [f'  <object id="{m["mesh_id"]}" p:UUID="{uuid.uuid4()}" type="model">',
                '   <mesh>', '    <vertices>']
        out += [f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>'
                for x, y, z in m["verts"]]
        out += ['    </vertices>', '    <triangles>']
        out += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m["faces"]]
        out += ['    </triangles>', '   </mesh>', '  </object>']
    out += [' </resources>', ' <build/>', '</model>', '']
    return "\n".join(out)


def root_model_xml(meshes, title: str, app_version: str) -> str:
    res, build = [], []
    for m in meshes:
        cx, cy, cz = m["offset"]
        res += [f'  <object id="{m["obj_id"]}" p:UUID="{uuid.uuid4()}" type="model">',
                '   <components>',
                f'    <component p:path="/3D/Objects/object_1.model" '
                f'objectid="{m["mesh_id"]}" p:UUID="{uuid.uuid4()}" '
                f'transform="1 0 0 0 1 0 0 0 1 {cx:.9g} {cy:.9g} {cz:.9g}"/>',
                '   </components>', '  </object>']
        px, py = m["pos"]
        build.append(f'  <item objectid="{m["obj_id"]}" p:UUID="{uuid.uuid4()}" '
                     f'transform="1 0 0 0 1 0 0 0 1 {px:.6g} {py:.6g} 0" printable="1"/>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>\n'
            f' <metadata name="Application">BambuStudio-{app_version}</metadata>\n'
            f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            f' <metadata name="Title">{escape(title)}</metadata>\n'
            f' <resources>\n' + "\n".join(res) + '\n </resources>\n'
            f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(build) + '\n </build>\n'
            f'</model>\n')


def model_settings_xml(meshes) -> str:
    objs = []
    for m in meshes:
        cx, cy, cz = m["offset"]
        n = escape(m["name"])
        objs.append(f"""  <object id="{m['obj_id']}">
    <metadata key="name" value="{n}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{len(m['faces'])}"/>
    <part id="{m['mesh_id']}" subtype="normal_part">
      <metadata key="name" value="{n}"/>
      <metadata key="matrix" value="1 0 0 {cx:.9g} 0 1 0 {cy:.9g} 0 0 1 {cz:.9g} 0 0 0 1"/>
      <metadata key="source_file" value="{n}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="{cx:.9g}"/>
      <metadata key="source_offset_y" value="{cy:.9g}"/>
      <metadata key="source_offset_z" value="{cz:.9g}"/>
      <metadata key="extruder" value="1"/>
      <mesh_stat face_count="{len(m['faces'])}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>""")
    inst = "\n".join(
        f"""    <model_instance>
      <metadata key="object_id" value="{m['obj_id']}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{i + 1}"/>
    </model_instance>""" for i, m in enumerate(meshes))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
            + "\n".join(objs) + '\n  <plate>\n'
            '    <metadata key="plater_id" value="1"/>\n'
            '    <metadata key="plater_name" value="Plate 1"/>\n'
            '    <metadata key="locked" value="false"/>\n'
            '    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
            '    <metadata key="gcode_file" value=""/>\n'
            + inst + '\n  </plate>\n  <assemble>\n  </assemble>\n</config>\n')


def build_plate(placements, sources: dict[str, Path], out: Path,
                profile: dict, app_version: str) -> None:
    meshes = []
    for idx, (name, px, py) in enumerate(placements, start=1):
        tris = read_stl(sources[name])
        lo, hi = bbox(tris)
        cx, cy, cz = ((lo[0]+hi[0])/2, (lo[1]+hi[1])/2, (lo[2]+hi[2])/2)
        centered = [tuple((v[0]-cx, v[1]-cy, v[2]-cz) for v in t) for t in tris]
        verts, faces = weld(centered)
        meshes.append({"name": name, "mesh_id": idx, "obj_id": 1000 + idx,
                       "verts": verts, "faces": faces,
                       "offset": (cx, cy, cz), "pos": (px, py)})

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("3D/3dmodel.model", root_model_xml(meshes, out.stem, app_version))
        z.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS)
        z.writestr("3D/Objects/object_1.model", objects_model_xml(meshes))
        z.writestr("Metadata/project_settings.config",
                   json.dumps(profile, ensure_ascii=False, indent=4))
        z.writestr("Metadata/model_settings.config", model_settings_xml(meshes))
        z.writestr("Metadata/slice_info.config", SLICE_INFO.format(version=app_version))
        z.writestr("Metadata/cut_information.xml", CUT_INFO)
        z.writestr("Metadata/filament_sequence.json",
                   '{"plate_1":{"nozzle_sequence":[],"optimal_assignment":[],"sequence":[]}}')

    tri = sum(len(m["faces"]) for m in meshes)
    print(f"OK {out.name:<22} деталей {len(meshes):3d}   граней {tri:7d}   "
          f"{out.stat().st_size/1024/1024:.1f} МБ")


def draw_layout(plates, sizes, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, axes = plt.subplots(1, len(plates), figsize=(6 * len(plates), 6.4),
                             facecolor="#1c1c1c")
    for ax, coords in zip(np_atleast(axes), plates):
        ax.add_patch(Rectangle((0, 0), BED, BED, facecolor="#2a2a2a",
                               edgecolor="#666", lw=1))
        for name, cx, cy in coords:
            dx, dy = sizes[name]
            ax.add_patch(Rectangle((cx - dx/2, cy - dy/2), dx, dy,
                                   facecolor="#ff9e1a", edgecolor="#7a4a00", lw=0.6))
            ax.text(cx, cy, name, ha="center", va="center", fontsize=6.5,
                    color="#2a1800", clip_on=True)
        ax.set_xlim(-6, BED + 6); ax.set_ylim(-6, BED + 6)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{len(coords)} шт. на столе 256 × 256",
                     color="#dddddd", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor=fig.get_facecolor())
    print(f"схема раскладки: {path}")


def np_atleast(axes):
    return axes if hasattr(axes, "__len__") else [axes]


def main() -> None:
    ap = argparse.ArgumentParser(description="Раскладка насадок на стол A1.")
    ap.add_argument("--csv", type=Path, required=True, help="список группы")
    ap.add_argument("--rename", nargs="*", default=[], metavar="БЫЛО=СТАЛО")
    ap.add_argument("--src", type=Path, default=PROJECT_DIR / "Готовые модели")
    ap.add_argument("--out", type=Path, default=PROJECT_DIR / "Готовые модели" / "Плиты")
    ap.add_argument("--hole", type=float, default=7.8)
    ap.add_argument("--per-plate", type=int, default=None,
                    help="максимум деталей на одну плиту")
    ap.add_argument("--gap", type=float, default=GAP, help="зазор между деталями, мм")
    ap.add_argument("--template", type=Path,
                    default=PROJECT_DIR / "Заготовки" / "ДИМА_7.4.3mf")
    args = ap.parse_args()

    swaps = {}
    for item in args.rename:
        was, now = item.split("=", 1)
        swaps[was.strip().upper()] = now.strip().upper()

    people = [(fio, swaps.get(n, n)) for fio, n in read_names(args.csv)]
    counts = Counter(n for _, n in people)

    items, sizes, sources = [], {}, {}
    for name, cnt in sorted(counts.items()):
        stl = args.src / f"{name}_{args.hole:g}.stl"
        if not stl.exists():
            sys.exit(f"Нет модели: {stl}")
        lo, hi = bbox(read_stl(stl))
        dx, dy = hi[0] - lo[0], hi[1] - lo[1]
        sources[name] = stl
        sizes[name] = (dx, dy)
        for _ in range(cnt):
            items.append((name, dx, dy))

    print(f"Деталей к раскладке: {len(items)} "
          f"({len(counts)} имён, дубли: "
          f"{', '.join(f'{n}×{c}' for n, c in sorted(counts.items()) if c > 1)})\n")

    plates = pack(items, gap=args.gap, per_plate=args.per_plate)

    profile, diff = load_profile(args.template, "off", {})
    app_version = profile.get("version", "02.07.01.57")
    print(f"Профиль: {profile.get('printer_settings_id')} / "
          f"{profile.get('print_settings_id')}   правки: {', '.join(diff)}\n")

    args.out.mkdir(parents=True, exist_ok=True)
    for i, coords in enumerate(plates, start=1):
        build_plate(coords, sources, args.out / f"Плита {i}.3mf", profile, app_version)

    draw_layout(plates, sizes, args.out / "раскладка.png")


if __name__ == "__main__":
    main()
