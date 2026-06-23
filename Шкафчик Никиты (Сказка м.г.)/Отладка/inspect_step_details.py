import FreeCAD
import Part
import sys

print("Analyzing STEP file details...")
step_path = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)\Референсы\Shoerack_honeycomb.STEP"

try:
    shape = Part.Shape()
    shape.read(step_path)
    
    # Let's check if the shape is a compound or single solid
    print(f"Shape Type: {shape.ShapeType}")
    
    # Let's count sub-shapes
    solids = shape.Solids
    print(f"Number of solids: {len(solids)}")
    
    # If there's 1 solid, let's check its volume and area
    if len(solids) > 0:
        main_solid = solids[0]
        print(f"Solid Volume: {main_solid.Volume:.2f} mm^3")
        print(f"Solid Surface Area: {main_solid.Area:.2f} mm^2")
        
        # Let's check the bounding box of each face to see if we can find horizontal/vertical walls
        faces = main_solid.Faces
        print(f"Total faces: {len(faces)}")
        
        # Count face types (Plane, Cylinder, etc.)
        face_types = {}
        for f in faces:
            ftype = type(f.Geometry).__name__ if f.Geometry else "None"
            face_types[ftype] = face_types.get(ftype, 0) + 1
        print("Face geometry types:")
        for ftype, count in face_types.items():
            print(f"  {ftype}: {count}")
            
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
