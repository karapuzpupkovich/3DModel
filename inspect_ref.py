import FreeCAD
import Mesh
import Part
import sys

print("Loading Reference STL...")
stl_path = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)\Референс.stl"

try:
    mesh = Mesh.Mesh(stl_path)
    print("Mesh analysis:")
    print(f"Number of points: {len(mesh.Points)}")
    print(f"Number of facets: {len(mesh.Facets)}")
    
    # Calculate bounding box
    bbox = mesh.BoundBox
    print(f"Bounding Box: X({bbox.XMin} to {bbox.XMax}), Y({bbox.YMin} to {bbox.YMax}), Z({bbox.ZMin} to {bbox.ZMax})")
    print(f"Dimensions: Width={bbox.XLength:.2f} mm, Depth={bbox.YLength:.2f} mm, Height={bbox.ZLength:.2f} mm")
    
except Exception as e:
    print(f"Error loading mesh: {e}")
    sys.exit(1)
