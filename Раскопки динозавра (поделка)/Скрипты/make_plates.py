# -*- coding: utf-8 -*-
"""
Плиты для Bambu Lab A1 — готовые проекты .3mf.

Раскладчик и профиль печати берутся из соседнего проекта «Насадка-имя на
карандаш»: там они уже проверены слайсером (A1 0.4 / 0.20mm Standard /
PLA Basic, поддержки выключены, глажка верха). Глажка здесь особенно
кстати: гладкий верх табличек не держит краску, и её легко стереть, а
в канавках она остаётся.

Плиты:
  1 — скелет:                  все кости (белым или слоновой костью)
  2 — таблички:                табличка с колышком и карта (бежевым / «деревом»)
  3 — номерки:                 9 номерков с выемкой под цифру (светлым)
  4 — цифры:                   9 цифр-вкладышей (тёмным)
  всё одним цветом:            скелет и таблички за один запуск
  номерки в два цвета (AMS):   номерки с цифрой вторым прутком, одной плитой

    python make_plates.py
"""

from __future__ import annotations

import copy
import json
import sys
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
TOOLS = PROJECT.parent / "Насадка-имя на карандаш" / "Скрипты"
sys.path.insert(0, str(TOOLS))
from make_3mf import (CONTENT_TYPES, CUT_INFO, MODEL_NS, MODEL_RELS,  # noqa: E402
                      ROOT_RELS, SLICE_INFO, bbox, load_profile, read_stl,
                      resolve_system_preset, weld)
from make_plate import build_plate, draw_layout, objects_model_xml, pack  # noqa: E402

SKEL = PROJECT / "Готовые модели" / "Скелет"
PLAQ = PROJECT / "Готовые модели" / "Таблички"
MARK = PROJECT / "Готовые модели" / "Номерки"
MARK_AMS = MARK / "для AMS"
OUT = PROJECT / "Готовые модели" / "Плиты"
TEMPLATE = PROJECT.parent / "Насадка-имя на карандаш" / "Заготовки" / "ДИМА_7.4.3mf"

BONES = ["череп", "позвоночник с рёбрами", "хвост", "передняя лапа",
         "задняя лапа вытянутая", "задняя лапа согнутая",
         "находка косточка", "находка позвонок", "находка коготь"]
PLAQUES = ["табличка с колышком", "карта раскопок"]
NUMBERS = "123456789"
MARKERS = [f"номерок {d}" for d in NUMBERS]
DIGITS = [f"цифра {d}" for d in NUMBERS]

# Два прутка для AMS. Цвета — Bambu PLA Basic Yellow и Black: жёлтые
# номерки с чёрными цифрами, как настоящие маркеры находок. В слайсере при
# отправке на печать прутки всё равно сопоставляются со слотами AMS.
AMS_COLOURS = ["#F4EE2AFF", "#000000FF"]
# Промывка при смене цвета, мм³, из таблицы Bambu (resources/flush/
# flush_data_standard.txt): жёлтый -> чёрный 120, чёрный -> жёлтый 450.
AMS_FLUSH = ["0", "120", "450", "0"]
# Настройки, которые хранятся по одной на пруток, но не входят в пресет
# прутка (живут в проекте). Остальные «прутковые» берутся из самого пресета.
PER_FILAMENT_EXTRA = {
    "default_filament_colour", "filament_colour", "filament_ids", "filament_is_mixed",
    "filament_map", "filament_map_2", "filament_mixed_components", "filament_mixed_gradient",
    "filament_mixed_gradient_curve", "filament_mixed_gradient_per_part",
    "filament_mixed_gradient_range", "filament_mixed_sublayer_ratios", "filament_nozzle_map",
    "filament_self_index", "filament_volume_map", "filament_change_length_nc",
    "enable_overhang_bridge_fan", "enable_pressure_advance", "pressure_advance",
    "first_x_layer_fan_speed", "first_x_layer_part_fan_speed", "ironing_fan_speed",
    "overhang_threshold_participating_cooling",
}


def source(name: str) -> Path:
    if name in BONES:
        return SKEL / f"{name}.stl"
    if name in PLAQUES:
        return PLAQ / f"{name}.stl"
    return MARK / f"{name}.stl"


def make(title: str, names: list[str], profile: dict, app_version: str) -> None:
    items, sizes, sources = [], {}, {}
    for n in names:
        lo, hi = bbox(read_stl(source(n)))
        dx, dy = hi[0] - lo[0], hi[1] - lo[1]
        items.append((n, dx, dy))
        sizes[n] = (dx, dy)
        sources[n] = source(n)
    plates = pack(items, gap=6.0)
    if len(plates) != 1:
        sys.exit(f"{title}: не влезло на один стол ({len(plates)} плиты)")
    folder = OUT / title
    folder.mkdir(parents=True, exist_ok=True)
    build_plate(plates[0], sources, folder / f"{title}.3mf", profile, app_version)
    draw_layout(plates, sizes, folder / "раскладка.png")


# --------------------------------------------------------------------------- #
#  Двухцветная плита: объекты из нескольких частей, у каждой свой пруток
# --------------------------------------------------------------------------- #
def two_filament_profile(profile: dict) -> dict:
    """
    Профиль на два прутка из профиля на один. Всё, что хранится по одной
    штуке на пруток, дублируется; настройки сопла и принтера остаются
    одиночными — у A1 одно сопло, AMS lite только подаёт прутки.
    """
    cfg = copy.deepcopy(profile)
    fil = resolve_system_preset("filament", cfg["filament_settings_id"][0])
    for k, v in cfg.items():
        if isinstance(v, list) and len(v) == 1 and (k in fil or k in PER_FILAMENT_EXTRA):
            cfg[k] = v * 2
    cfg["filament_colour"] = list(AMS_COLOURS)
    cfg["filament_self_index"] = ["1", "2"]
    cfg["flush_volumes_matrix"] = list(AMS_FLUSH)
    # [процесс, пруток 1, пруток 2, принтер]
    cfg["different_settings_to_system"] = [cfg["different_settings_to_system"][0], "", "", ""]
    cfg["inherits_group"] = ["", "", "", ""]
    return cfg


def root_model_multi(objs, title: str, app_version: str) -> str:
    res, build = [], []
    for o in objs:
        comps = "\n".join(
            f'    <component p:path="/3D/Objects/object_1.model" objectid="{p["mesh_id"]}" '
            f'p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 {o["cz"]:.9g}"/>'
            for p in o["parts"])
        res.append(f'  <object id="{o["obj_id"]}" p:UUID="{uuid.uuid4()}" type="model">\n'
                   f'   <components>\n{comps}\n   </components>\n  </object>')
        px, py = o["pos"]
        build.append(f'  <item objectid="{o["obj_id"]}" p:UUID="{uuid.uuid4()}" '
                     f'transform="1 0 0 0 1 0 0 0 1 {px:.6g} {py:.6g} 0" printable="1"/>')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>\n'
            f' <metadata name="Application">BambuStudio-{app_version}</metadata>\n'
            f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
            f' <metadata name="Title">{escape(title)}</metadata>\n'
            f' <resources>\n' + "\n".join(res) + '\n </resources>\n'
            f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(build) + '\n </build>\n'
            f'</model>\n')


def model_settings_multi(objs) -> str:
    out = []
    for o in objs:
        cz = o["cz"]
        parts = []
        for p in o["parts"]:
            n = escape(p["name"])
            parts.append(f"""    <part id="{p['mesh_id']}" subtype="normal_part">
      <metadata key="name" value="{n}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 {cz:.9g} 0 0 0 1"/>
      <metadata key="source_file" value="{n}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="0"/>
      <metadata key="source_offset_y" value="0"/>
      <metadata key="source_offset_z" value="{cz:.9g}"/>
      <metadata key="extruder" value="{p['extruder']}"/>
      <mesh_stat face_count="{len(p['faces'])}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>""")
        faces = sum(len(p["faces"]) for p in o["parts"])
        out.append(f"""  <object id="{o['obj_id']}">
    <metadata key="name" value="{escape(o['name'])}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{faces}"/>
""" + "\n".join(parts) + "\n  </object>")
    inst = "\n".join(
        f"""    <model_instance>
      <metadata key="object_id" value="{o['obj_id']}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="{i + 1}"/>
    </model_instance>""" for i, o in enumerate(objs))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
            + "\n".join(out) + '\n  <plate>\n'
            '    <metadata key="plater_id" value="1"/>\n'
            '    <metadata key="plater_name" value="Plate 1"/>\n'
            '    <metadata key="locked" value="false"/>\n'
            '    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
            '    <metadata key="gcode_file" value=""/>\n'
            + inst + '\n  </plate>\n  <assemble>\n  </assemble>\n</config>\n')


def make_multi(title: str, objects: list, profile: dict, app_version: str) -> None:
    """
    objects: [(имя, [(stl, пруток), ...])] — части объекта смоделированы в
    общих координатах, их взаимное положение сохраняется: объект
    центрируется по общему габариту всех частей.
    """
    loaded, items, sizes = [], [], {}
    for name, parts in objects:
        tris = [(stl, ext, read_stl(stl)) for stl, ext in parts]
        lo, hi = bbox([t for _, _, ts in tris for t in ts])
        loaded.append((name, tris, lo, hi))
        dx, dy = hi[0] - lo[0], hi[1] - lo[1]
        items.append((name, dx, dy))
        sizes[name] = (dx, dy)
    plates = pack(items, gap=6.0)
    if len(plates) != 1:
        sys.exit(f"{title}: не влезло на один стол ({len(plates)} плиты)")
    pos = {n: (x, y) for n, x, y in plates[0]}

    objs, meshes, mesh_id = [], [], 0
    for k, (name, tris, lo, hi) in enumerate(loaded, start=1):
        c = [(lo[i] + hi[i]) / 2 for i in range(3)]
        parts = []
        for stl, ext, ts in tris:
            mesh_id += 1
            centered = [tuple((v[0] - c[0], v[1] - c[1], v[2] - c[2]) for v in t) for t in ts]
            verts, faces = weld(centered)
            part = {"name": f"{name} — {stl.stem}", "mesh_id": mesh_id, "verts": verts,
                    "faces": faces, "extruder": ext}
            parts.append(part)
            meshes.append(part)
        objs.append({"name": name, "obj_id": 1000 + k, "parts": parts, "cz": c[2],
                     "pos": pos[name]})

    folder = OUT / title
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"{title}.3mf"
    cfg = two_filament_profile(profile)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("3D/3dmodel.model", root_model_multi(objs, title, app_version))
        z.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS)
        z.writestr("3D/Objects/object_1.model", objects_model_xml(meshes))
        z.writestr("Metadata/project_settings.config", json.dumps(cfg, ensure_ascii=False, indent=4))
        z.writestr("Metadata/model_settings.config", model_settings_multi(objs))
        z.writestr("Metadata/slice_info.config", SLICE_INFO.format(version=app_version))
        z.writestr("Metadata/cut_information.xml", CUT_INFO)
        z.writestr("Metadata/filament_sequence.json",
                   '{"plate_1":{"nozzle_sequence":[],"optimal_assignment":[],"sequence":[]}}')
    tri = sum(len(m["faces"]) for m in meshes)
    print(f"OK {out.name:<22} деталей {len(objs):3d}   частей {len(meshes):3d}   "
          f"граней {tri:7d}   {out.stat().st_size / 1024 / 1024:.1f} МБ   прутков 2")
    draw_layout(plates, sizes, folder / "раскладка.png")


def main() -> None:
    profile, diff = load_profile(TEMPLATE, "off", {})
    app_version = profile.get("version", "02.07.01.57")
    print(f"Профиль: {profile.get('printer_settings_id')} / {profile.get('print_settings_id')}"
          f"   правки: {', '.join(diff)}\n")
    only = sys.argv[1:]

    def want(title):
        return not only or any(s in title for s in only)

    for title, names in (("1 — скелет", BONES), ("2 — таблички", PLAQUES),
                         ("3 — номерки", MARKERS), ("4 — цифры", DIGITS),
                         ("всё одним цветом", BONES + PLAQUES)):
        if want(title):
            make(title, names, profile, app_version)
    title = "номерки в два цвета (AMS)"
    if want(title):
        make_multi(title, [(f"номерок {d}", [(MARK_AMS / "основа.stl", 1),
                                              (MARK_AMS / f"цифра {d}.stl", 2)])
                           for d in NUMBERS], profile, app_version)


if __name__ == "__main__":
    main()
