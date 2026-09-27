# -*- coding: utf-8 -*-
"""
Плиты для Bambu Lab A1 — готовые проекты .3mf.

Раскладчик и профиль печати берутся из соседнего проекта «Насадка-имя на
карандаш»: там они уже проверены слайсером (A1 0.4 / 0.20mm Standard /
PLA Basic, поддержки выключены, глажка верха). Глажка здесь особенно
кстати: гладкий верх табличек не держит краску, и её легко стереть, а
в канавках она остаётся.

Плиты:
  1 — скелет:            все кости (печатать белым или слоновой костью)
  2 — таблички:          табличка с колышком и карта (бежевым / «деревом»)
  все вместе:            одним цветом за один запуск

    python make_plates.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
TOOLS = PROJECT.parent / "Насадка-имя на карандаш" / "Скрипты"
sys.path.insert(0, str(TOOLS))
from make_plate import build_plate, draw_layout, pack  # noqa: E402
from make_3mf import bbox, load_profile, read_stl  # noqa: E402

SKEL = PROJECT / "Готовые модели" / "Скелет"
PLAQ = PROJECT / "Готовые модели" / "Таблички"
OUT = PROJECT / "Готовые модели" / "Плиты"
TEMPLATE = PROJECT.parent / "Насадка-имя на карандаш" / "Заготовки" / "ДИМА_7.4.3mf"

BONES = ["череп", "позвоночник с рёбрами", "хвост", "передняя лапа",
         "задняя лапа вытянутая", "задняя лапа согнутая",
         "находка косточка", "находка позвонок", "находка коготь"]
PLAQUES = ["табличка с колышком", "карта раскопок"]


def source(name: str) -> Path:
    return (SKEL if name in BONES else PLAQ) / f"{name}.stl"


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


def main() -> None:
    profile, diff = load_profile(TEMPLATE, "off", {})
    app_version = profile.get("version", "02.07.01.57")
    print(f"Профиль: {profile.get('printer_settings_id')} / {profile.get('print_settings_id')}"
          f"   правки: {', '.join(diff)}\n")
    make("1 — скелет", BONES, profile, app_version)
    make("2 — таблички", PLAQUES, profile, app_version)
    make("всё одним цветом", BONES + PLAQUES, profile, app_version)


if __name__ == "__main__":
    main()
