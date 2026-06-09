import os
import sys
import traceback

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import Part
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

from honeycomb_cell.builder import create_honeycomb_cell_shape
from honeycomb_cell.config import DEFAULT_CONFIG

try:
    shape, report = create_honeycomb_cell_shape(DEFAULT_CONFIG, enable_perforation=False)
    print(f"Valid flag: {report.valid}")
    print(f"Shape type: {shape.ShapeType}")
    print(f"Solids: {len(shape.Solids)}")
    print(f"Shells: {len(shape.Shells)}")
    print(f"Faces: {len(shape.Faces)}")
    print("Running shape.check(True)...")
    result = shape.check(True)
    print(f"check(True) returned: {result!r}")
except Exception:
    traceback.print_exc()
    raise
