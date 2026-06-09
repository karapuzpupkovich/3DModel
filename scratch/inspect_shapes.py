import sys, os
PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part
from honeycomb_cell.builder import create_honeycomb_cell_shape
from honeycomb_cell.config import DEFAULT_CONFIG

shape, report = create_honeycomb_cell_shape(DEFAULT_CONFIG, enable_perforation=False)
print("="*60)
print("Shape type:", shape.ShapeType)
print("Number of Solids:", len(shape.Solids))
print("Number of Shells:", len(shape.Shells))
print("Number of Faces:", len(shape.Faces))
print("Number of Edges:", len(shape.Edges))
print("IsValid:", shape.isValid())
print("Number of Compounds:", len(shape.Compounds) if hasattr(shape, "Compounds") else "N/A")
print("="*60)
