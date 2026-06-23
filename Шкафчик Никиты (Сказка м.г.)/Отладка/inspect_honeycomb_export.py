import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP_PATH = os.path.join(PROJECT_DIR, "Стандартная_ячейка", "output", "HoneycombCell.step")

try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: run this script inside FreeCAD.")
    sys.exit(1)

shape = Part.Shape()
shape.read(STEP_PATH)
print(f"Shape Type: {shape.ShapeType}")
print(f"Solids: {len(shape.Solids)}")
print(f"Valid: {shape.isValid()}")
bbox = shape.BoundBox
print(f"Bounding Box: X({bbox.XMin:.3f} to {bbox.XMax:.3f}), Y({bbox.YMin:.3f} to {bbox.YMax:.3f}), Z({bbox.ZMin:.3f} to {bbox.ZMax:.3f})")
print(f"Dimensions: {bbox.XLength:.3f} x {bbox.YLength:.3f} x {bbox.ZLength:.3f} mm")
if shape.Solids:
    solid = shape.Solids[0]
    print(f"Volume: {solid.Volume:.3f} mm^3")
    print(f"Area: {solid.Area:.3f} mm^2")
