import FreeCAD
import Part
import sys
import time

step_path = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)\Shoerack_honeycomb.STEP"
print(f"Loading {step_path}...")
sys.stdout.flush()

try:
    shape = Part.Shape()
    shape.read(step_path)
    solid = shape.Solids[0]
    
    faces = sorted(solid.Faces, key=lambda f: f.Area, reverse=True)
    
    print("Joint-related faces (Area between 200 and 3000 mm^2):")
    sys.stdout.flush()
    
    count = 0
    for idx, f in enumerate(faces):
        if 200.0 <= f.Area <= 3500.0:
            bbox = f.BoundBox
            n_str = "N/A"
            try:
                uv = f.ParameterRange
                u = (uv[0] + uv[1]) / 2.0
                v = (uv[2] + uv[3]) / 2.0
                n = f.normalAt(u, v)
                n_str = f"({n.x:.4f}, {n.y:.4f}, {n.z:.4f})"
            except:
                pass
            
            print(f"  Face #{idx}: Area={f.Area:.2f} mm^2, Normal={n_str}, BBox: X({bbox.XMin:.1f} to {bbox.XMax:.1f}), Y({bbox.YMin:.1f} to {bbox.YMax:.1f}), Z({bbox.ZMin:.1f} to {bbox.ZMax:.1f})")
            sys.stdout.flush()
            count += 1
            if count >= 30:
                break
                
except Exception as e:
    print(f"Error: {e}")
    sys.stdout.flush()

time.sleep(2)
sys.exit(0)
