import FreeCAD
import Part
import sys

print("Loading Shoerack_honeycomb.STEP...")
step_path = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)\Shoerack_honeycomb.STEP"

try:
    shape = Part.Shape()
    shape.read(step_path)
    print("Shape analysis:")
    print(f"Shape type: {shape.ShapeType}")
    print(f"SubShapes count - Faces: {len(shape.Faces)}, Shells: {len(shape.Shells)}, Solids: {len(shape.Solids)}")
    
    # Calculate bounding box
    bbox = shape.BoundBox
    print(f"Bounding Box: X({bbox.XMin} to {bbox.XMax}), Y({bbox.YMin} to {bbox.YMax}), Z({bbox.ZMin} to {bbox.ZMax})")
    print(f"Dimensions: Width={bbox.XLength:.2f} mm, Depth={bbox.YLength:.2f} mm, Height={bbox.ZLength:.2f} mm")
    
except Exception as e:
    print(f"Error loading STEP shape: {e}")
    sys.exit(1)
