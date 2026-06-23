import os
import sys
import traceback

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Mesh
import Part

from Стандартная_ячейка.builder import (
    _build_outer_vertices,
    _build_perforation_cutters,
    _chunked,
    create_Стандартная_ячейка_shape,
)
from Стандартная_ячейка.config import DEFAULT_CONFIG


def main() -> None:
    cfg = DEFAULT_CONFIG
    shape, _ = create_Стандартная_ячейка_shape(cfg, enable_perforation=False, log=print)
    vertices = _build_outer_vertices(cfg)
    cutters_by_face, report = _build_perforation_cutters(vertices, cfg, print)

    for face_index in (0, 2, 3, 5):
        face_cutters = cutters_by_face[face_index]
        for chunk in _chunked(face_cutters, cfg.perforation_batch_size):
            shape = shape.cut(Part.makeCompound(list(chunk)))
        shape = shape.removeSplitter()

    doc = FreeCAD.newDocument("HoneycombJointPreview")
    obj = doc.addObject("Part::Feature", "HoneycombJointPreview")
    obj.Shape = shape
    doc.recompute()

    output_dir = os.path.join(PROJECT_DIR, "Стандартная_ячейка", "output")
    os.makedirs(output_dir, exist_ok=True)
    stl_path = os.path.join(output_dir, "HoneycombJointPreview.stl")
    Mesh.export([obj], stl_path)

    print(f"Preview holes total: {report.total_holes}")
    print(stl_path)


try:
    main()
except Exception:
    traceback.print_exc()
    raise