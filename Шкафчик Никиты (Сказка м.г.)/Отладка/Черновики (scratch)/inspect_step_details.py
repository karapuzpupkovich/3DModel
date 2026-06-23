import sys, os
PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part

step_path = os.path.join(PROJECT_DIR, "honeycomb_cell", "output", "HoneycombCell.step")
if not os.path.exists(step_path):
    print("STEP file does not exist")
    sys.exit(1)

shape = Part.Shape()
shape.read(step_path)

print("="*60)
print(f"Inspecting STEP file: {step_path}")
print("IsValid:", shape.isValid())

# Let's count cylindrical faces
cyl_count = 0
other_count = 0
for face in shape.Faces:
    geom = face.Surface
    if "Cylinder" in str(geom):
        cyl_count += 1
    else:
        other_count += 1

print(f"Cylindrical faces: {cyl_count}")
print(f"Other faces: {other_count}")
print("="*60)
