import os
import sys

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

from honeycomb_cell.builder import create_honeycomb_cell_shape
from honeycomb_cell.config import DEFAULT_CONFIG

shape, report = create_honeycomb_cell_shape(DEFAULT_CONFIG, enable_perforation=False)
print(f"Valid: {report.valid}")
print(f"Baseline Volume: {shape.Volume:.3f} mm^3")
print(f"Baseline Area: {shape.Area:.3f} mm^2")
bbox = shape.BoundBox
print(f"Bounding Box: {bbox.XLength:.3f} x {bbox.YLength:.3f} x {bbox.ZLength:.3f} mm")
