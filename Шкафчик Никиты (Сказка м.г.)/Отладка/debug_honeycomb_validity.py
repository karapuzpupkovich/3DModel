import os
import sys
import traceback

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import Part
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

from Стандартная_ячейка.builder import create_Стандартная_ячейка_shape
from Стандартная_ячейка.config import DEFAULT_CONFIG

try:
    shape, report = create_Стандартная_ячейка_shape(DEFAULT_CONFIG, enable_perforation=False)
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
