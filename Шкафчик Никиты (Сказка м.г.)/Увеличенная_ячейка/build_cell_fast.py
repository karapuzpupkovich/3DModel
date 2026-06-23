"""
Быстрый вариант увеличенной ячейки — ПРОРЕЖЕННАЯ перфорация (для ускорения печати).

Геометрия и стенка 2.3 мм НЕ меняются (прочность та же, замки те же). Меняется
только сетка отверстий:
  * ряды по высоте: 28 -> 14 (шаг 6.6 -> 13.2 мм);
  * столбцы: каждый второй из штатных (builder сам отфильтрует невалидные).
Отверстия того же размера (Ø5.6), но реже => перемычки ~7.6 мм (вместо 1.0,
крепче) и в разы меньше контуров на слой => печать заметно быстрее.
Итог: ~364 отверстия вместо 1344.

Экспорт — ОТДЕЛЬНЫЙ файл HoneycombCell_large_fast.* ; оригинал не трогается.
Сборка тяжёлая (булевы вычитания) — идёт ~10-15 мин, это нормально.

Запуск (без таймаута, дать досчитать):
  "C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" build_cell_fast.py
"""
import os
import sys
import traceback
from dataclasses import replace

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Mesh

from Увеличенная_ячейка.builder import create_large_cell_shape
from Увеличенная_ячейка.config import DEFAULT_CONFIG


def L(msg):
    FreeCAD.Console.PrintMessage("FAST| " + str(msg) + "\n")


def make_fast_config(cfg):
    return replace(
        cfg,
        perforation_rows=14,
        perforation_spacing_z=13.2,
        perforation_cols_face_0=cfg.perforation_cols_face_0[::2],
        perforation_cols_face_1=cfg.perforation_cols_face_1[::2],
        perforation_cols_face_2=cfg.perforation_cols_face_2[::2],
        perforation_cols_face_3=cfg.perforation_cols_face_3[::2],
    )


def main():
    out = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out, exist_ok=True)
    name = "HoneycombCell_large_fast"
    try:
        L("building sparse-perforation cell...")
        shape, report = create_large_cell_shape(
            make_fast_config(DEFAULT_CONFIG), enable_perforation=True, log=L)
        L("valid=%s holes=%s bbox %.0fx%.0fx%.0f" % (
            report.valid, report.total_holes,
            shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength))
        doc = FreeCAD.newDocument(name)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        doc.recompute()
        doc.saveAs(os.path.join(out, name + ".FCStd"))
        shape.exportStep(os.path.join(out, name + ".step"))
        Mesh.export([obj], os.path.join(out, name + ".stl"))
        L("exported: %s .FCStd / .step / .stl" % name)
    except Exception as exc:  # noqa: BLE001
        L("ERROR: " + repr(exc))
        L(traceback.format_exc())


main()
