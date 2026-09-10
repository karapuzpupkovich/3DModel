#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка проекта Bambu Studio (.3mf) из готового STL.

Профиль печати берётся из 3MF-заготовки, скачанной с MakerWorld
(`Заготовки/ДИМА_7.4.3mf`) — там уже лежит рабочая связка
«Bambu Lab A1 0.4 nozzle / 0.20mm Standard / Bambu PLA Basic».
Копируется только сам профиль (стоковые настройки Bambu); метаданные
MakerWorld — DesignModelId, MakerLab* — не переносятся.

Поверх профиля применяются правки под эту деталь: см. OVERRIDES.

    python make_3mf.py "Готовые модели/МАКСИМ_7.8.stl"
    python make_3mf.py "Готовые модели"/*.stl --supports auto
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_names import bbox, read_stl  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = PROJECT_DIR / "Заготовки" / "ДИМА_7.4.3mf"

BED_CENTER = (128.0, 128.0)  # A1: printable_area 256 x 256

# Правки профиля под насадку-имя. Обоснование — в README проекта.
#
# Поддержки выключены не «на глаз»: при enable_support=1 слайсер печатает
# поддержку с Z 0.20 до 8.60, то есть ВНУТРИ канала Ø7.8 (он идёт с 1.10
# до 8.90). Вынуть её оттуда нельзя — карандаш просто не влезет. Других
# навесов в детали нет: буквы выдавлены вертикально от стола, а свод над
# каналом слайсер кладёт мостом.
OVERRIDES = {
    "enable_support": "0",
    "ironing_type": "top",           # глажка верхних поверхностей — гладкий верх
    "sparse_infill_density": "25%",  # плотнее опора под верхней коркой
    "brim_type": "auto_brim",
}

MODEL_NS = (
    'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
    'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
    'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
    'requiredextensions="p"'
)

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""

MODEL_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""

SLICE_INFO = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="{version}"/>
  </header>
</config>
"""

CUT_INFO = """<?xml version="1.0" encoding="utf-8"?>
<objects>
 <object id="1">
  <cut_id id="0" check_sum="1" connectors_cnt="0"/>
 </object>
</objects>
"""


def weld(tris):
    """Треугольники -> (список вершин, список индексных троек)."""
    index: dict[tuple, int] = {}
    verts: list[tuple] = []
    faces: list[tuple] = []
    for tri in tris:
        ids = []
        for v in tri:
            key = (round(v[0], 6), round(v[1], 6), round(v[2], 6))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            ids.append(index[key])
        if len({*ids}) == 3:  # вырожденные грани Bambu Studio ругает
            faces.append(tuple(ids))
    return verts, faces


def object_model_xml(verts, faces, obj_uuid: str) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
        ' <resources>',
        f'  <object id="1" p:UUID="{obj_uuid}" type="model">',
        '   <mesh>',
        '    <vertices>',
    ]
    out += [f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>' for x, y, z in verts]
    out += ['    </vertices>', '    <triangles>']
    out += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces]
    out += ['    </triangles>', '   </mesh>', '  </object>', ' </resources>',
            ' <build/>', '</model>', '']
    return "\n".join(out)


def root_model_xml(title: str, offset, app_version: str) -> str:
    ox, oy, oz = offset
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" {MODEL_NS}>
 <metadata name="Application">BambuStudio-{app_version}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{escape(title)}</metadata>
 <resources>
  <object id="2" p:UUID="{uuid.uuid4()}" type="model">
   <components>
    <component p:path="/3D/Objects/object_1.model" objectid="1" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {ox:.9g} {oy:.9g} {oz:.9g}"/>
   </components>
  </object>
 </resources>
 <build p:UUID="{uuid.uuid4()}">
  <item objectid="2" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {BED_CENTER[0]:.6g} {BED_CENTER[1]:.6g} 0" printable="1"/>
 </build>
</model>
"""


def model_settings_xml(name: str, face_count: int, offset) -> str:
    ox, oy, oz = offset
    n = escape(name)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="{n}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{face_count}"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{n}"/>
      <metadata key="matrix" value="1 0 0 {ox:.9g} 0 1 0 {oy:.9g} 0 0 1 {oz:.9g} 0 0 0 1"/>
      <metadata key="source_file" value="{n}.stl"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="{ox:.9g}"/>
      <metadata key="source_offset_y" value="{oy:.9g}"/>
      <metadata key="source_offset_z" value="{oz:.9g}"/>
      <metadata key="extruder" value="1"/>
      <mesh_stat face_count="{face_count}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="Plate 1"/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="gcode_file" value=""/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="1"/>
    </model_instance>
  </plate>
  <assemble>
  </assemble>
</config>
"""


def load_profile(template: Path, supports: str, extra: dict[str, str]) -> dict:
    with zipfile.ZipFile(template) as z:
        cfg = json.loads(z.read("Metadata/project_settings.config").decode("utf-8"))
    cfg.update(OVERRIDES)
    if supports == "auto":
        cfg["enable_support"] = "1"
    cfg.update(extra)
    return cfg


def build(stl: Path, out: Path, profile: dict, app_version: str) -> None:
    tris = read_stl(stl)
    lo, hi = bbox(tris)
    # Bambu хранит меш вокруг начала координат, а положение — в трансформации.
    cx, cy, cz = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    centered = [tuple((v[0] - cx, v[1] - cy, v[2] - cz) for v in t) for t in tris]

    verts, faces = weld(centered)
    name = stl.stem

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("3D/3dmodel.model", root_model_xml(name, (cx, cy, cz), app_version))
        z.writestr("3D/_rels/3dmodel.model.rels", MODEL_RELS)
        z.writestr("3D/Objects/object_1.model",
                   object_model_xml(verts, faces, str(uuid.uuid4())))
        z.writestr("Metadata/project_settings.config",
                   json.dumps(profile, ensure_ascii=False, indent=4))
        z.writestr("Metadata/model_settings.config",
                   model_settings_xml(name, len(faces), (cx, cy, cz)))
        z.writestr("Metadata/slice_info.config", SLICE_INFO.format(version=app_version))
        z.writestr("Metadata/cut_information.xml", CUT_INFO)
        z.writestr("Metadata/filament_sequence.json",
                   '{"plate_1":{"nozzle_sequence":[],"optimal_assignment":[],"sequence":[]}}')

    print(f"OK {out.name:<24} {hi[0]-lo[0]:6.2f} x {hi[1]-lo[1]:5.2f} x "
          f"{hi[2]-lo[2]:5.2f} мм   граней {len(faces):6d}   "
          f"{out.stat().st_size/1024:.0f} КБ")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Сборка .3mf для Bambu Studio из STL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("stl", nargs="+", type=Path)
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE,
                    help="3MF, из которого берётся профиль печати")
    ap.add_argument("--supports", choices=("off", "auto"), default="off",
                    help="поддержки: off — деталь печатается без них")
    ap.add_argument("--set", action="append", default=[], metavar="КЛЮЧ=ЗНАЧЕНИЕ",
                    help="точечная правка профиля, можно повторять")
    ap.add_argument("--out", type=Path, default=None,
                    help="каталог для .3mf (по умолчанию рядом с STL)")
    args = ap.parse_args()

    if not args.template.exists():
        sys.exit(f"Заготовка с профилем не найдена: {args.template}")

    extra = {}
    for item in args.set:
        if "=" not in item:
            sys.exit(f"Ожидался формат КЛЮЧ=ЗНАЧЕНИЕ, получено: {item}")
        k, v = item.split("=", 1)
        extra[k.strip()] = v.strip()

    profile = load_profile(args.template, args.supports, extra)
    app_version = profile.get("version", "02.07.01.57")

    print(f"Профиль: {profile.get('printer_settings_id')} / "
          f"{profile.get('print_settings_id')} / "
          f"{', '.join(profile.get('filament_settings_id', []))}")
    print(f"Поддержки: {'включены' if profile['enable_support'] == '1' else 'выключены'}"
          f"   заполнение: {profile['sparse_infill_density']}\n")

    for stl in args.stl:
        if not stl.exists():
            sys.exit(f"Нет файла: {stl}")
        out_dir = args.out or stl.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        build(stl, out_dir / f"{stl.stem}.3mf", profile, app_version)


if __name__ == "__main__":
    main()
