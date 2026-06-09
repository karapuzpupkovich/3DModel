import os
import sys
import traceback

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
except ImportError:
    print("Error: run this test inside FreeCAD.")
    sys.exit(1)

try:
    from honeycomb_cell.builder import create_honeycomb_cell_shape
    from honeycomb_cell.config import DEFAULT_CONFIG

    shape, _ = create_honeycomb_cell_shape(DEFAULT_CONFIG, enable_perforation=False)

    left = shape.copy()
    right = shape.copy()

    rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)
    left.Placement = FreeCAD.Placement(FreeCAD.Vector(83.5, 20.0, 64.0), rot)
    right.Placement = FreeCAD.Placement(FreeCAD.Vector(161.0, 20.0, 112.0), rot)

    common = left.common(right)
    print(f"Overlap Volume: {common.Volume:.6f} mm^3")
    print(f"Overlap Area: {common.Area:.6f} mm^2")
    if common.Volume < 1e-6:
        print("Success: Cells fit perfectly with zero overlap volume!")
    else:
        raise RuntimeError("Cells overlap")
except Exception:
    traceback.print_exc()
    raise
