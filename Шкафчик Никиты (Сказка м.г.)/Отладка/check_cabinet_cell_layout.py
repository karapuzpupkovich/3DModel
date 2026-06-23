import itertools
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
except ImportError:
    print("Error: run this test inside FreeCAD.")
    sys.exit(1)

from Стандартная_ячейка.builder import create_Стандартная_ячейка_shape
from Стандартная_ячейка.config import DEFAULT_CONFIG

centers = [
    ("ShoeCell_1", 83.5, 64.0),
    ("ShoeCell_2", 83.5, 160.0),
    ("ShoeCell_3", 161.0, 112.0),
    ("ShoeCell_4", 238.5, 64.0),
    ("ShoeCell_5", 238.5, 160.0),
]

shape, report = create_Стандартная_ячейка_shape(DEFAULT_CONFIG, enable_perforation=False)
rotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)
placed = []
for name, center_x, center_z in centers:
    instance = shape.copy()
    instance.Placement = FreeCAD.Placement(FreeCAD.Vector(center_x, 20.0, center_z), rotation)
    placed.append((name, instance))

max_overlap = 0.0
for (name_a, shape_a), (name_b, shape_b) in itertools.combinations(placed, 2):
    overlap = shape_a.common(shape_b).Volume
    max_overlap = max(max_overlap, overlap)
    print(f"{name_a} vs {name_b}: {overlap:.6f} mm^3")

print(f"Valid baseline shape: {report.valid}")
print(f"Max pair overlap: {max_overlap:.6f} mm^3")
if max_overlap < 1e-6:
    print("Success: Cabinet layout is collision-free.")
else:
    raise RuntimeError("Cabinet layout has overlapping cells")
