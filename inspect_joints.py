import FreeCAD
import Part
import sys

print("Loading Shoerack_honeycomb.STEP...")
step_path = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)\Shoerack_honeycomb.STEP"

try:
    shape = Part.Shape()
    shape.read(step_path)
    
    faces = shape.Faces
    print(f"Total faces: {len(faces)}")
    
    face_areas = sorted([f.Area for f in faces])
    print(f"Smallest face area: {face_areas[0]:.4f} mm^2")
    print(f"Largest face area: {face_areas[-1]:.4f} mm^2")
    
    planes = []
    cylinders = []
    others = 0
    
    for f in faces:
        try:
            geom = f.Geometry
            if geom:
                gtype = type(geom).__name__
                if gtype == "GeomPlane":
                    planes.append(f)
                elif gtype == "GeomCylinder":
                    cylinders.append(f)
                else:
                    others += 1
            else:
                others += 1
        except Exception:
            others += 1
            
    print(f"Planar faces: {len(planes)}")
    print(f"Cylindrical faces: {len(cylinders)}")
    print(f"Other/unhandled faces: {others}")
    
    # Let's count planes with specific normals
    normals = []
    for p in planes:
        try:
            uv = p.ParameterRange
            u = (uv[0] + uv[1]) / 2.0
            v = (uv[2] + uv[3]) / 2.0
            n = p.normalAt(u, v)
            nr = (round(n.x, 2), round(n.y, 2), round(n.z, 2))
            normals.append(nr)
        except Exception:
            pass
            
    unique_normals = set(normals)
    print(f"Unique plane normals: {len(unique_normals)}")
    for n in sorted(list(unique_normals))[:20]:
        print(f"  {n}")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
