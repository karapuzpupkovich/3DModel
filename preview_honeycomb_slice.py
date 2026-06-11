import os
import struct
import sys
import traceback
from dataclasses import replace

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD

from Стандартная_ячейка.builder import create_Стандартная_ячейка_shape
from Стандартная_ячейка.config import DEFAULT_CONFIG


def write_binary_stl(shape, path: str, deflection: float = 0.5) -> None:
    vertices, facets = shape.tessellate(deflection)
    with open(path, "wb") as handle:
        handle.write(b"HoneycombSlicePreview".ljust(80, b" "))
        handle.write(struct.pack("<I", len(facets)))
        for i1, i2, i3 in facets:
            p1 = vertices[i1]
            p2 = vertices[i2]
            p3 = vertices[i3]
            handle.write(struct.pack("<fff", 0.0, 0.0, 0.0))
            handle.write(struct.pack("<fff", p1.x, p1.y, p1.z))
            handle.write(struct.pack("<fff", p2.x, p2.y, p2.z))
            handle.write(struct.pack("<fff", p3.x, p3.y, p3.z))
            handle.write(struct.pack("<H", 0))


def main() -> None:
    cfg = replace(
        DEFAULT_CONFIG,
        cell_len=56.0,
        perforation_rows=8,
        perforation_z_start=3.5,
    )
    shape, report = create_Стандартная_ячейка_shape(cfg, enable_perforation=True, log=print)

    doc = FreeCAD.newDocument("HoneycombSlicePreview")
    obj = doc.addObject("Part::Feature", "HoneycombSlicePreview")
    obj.Shape = shape
    doc.recompute()

    output_dir = os.path.join(PROJECT_DIR, "Стандартная_ячейка", "output")
    os.makedirs(output_dir, exist_ok=True)
    stl_path = os.path.join(output_dir, "HoneycombSlicePreview.stl")
    write_binary_stl(shape, stl_path)

    print(f"Slice valid: {report.valid}")
    print(f"Slice holes: {report.total_holes}")
    print(stl_path)


try:
    main()
except Exception:
    traceback.print_exc()
    raise