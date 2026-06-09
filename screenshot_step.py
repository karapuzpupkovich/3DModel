import socket
import json
import sys

code = """
import FreeCAD
import FreeCADGui
import Part
import os

print("Importing STEP in GUI...")
step_path = r"C:\\3DModel\\Шкафчик Никиты (Сказка м.г.)\\Shoerack_honeycomb.STEP"
png_path = r"C:\\3DModel\\step_view.png"

# Close any existing TempStep doc
try:
    FreeCAD.closeDocument("TempStep")
except:
    pass

doc = FreeCAD.newDocument("TempStep")
shape = Part.read(step_path)
obj = doc.addObject("Part::Feature", "StepModel")
obj.Shape = shape
doc.recompute()

# Ensure we have active view
view = FreeCADGui.activeDocument().activeView()
if view:
    view.viewIsometric()
    view.fitAll()
    view.saveImage(png_path, 1024, 768, "White")
    print(f"Screenshot saved to {png_path}")
    result = "Screenshot saved successfully."
else:
    print("No active view found!")
    result = "Error: No active view."

FreeCAD.closeDocument("TempStep")
result
"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('localhost', 23456))
    payload = {
        "tool": "execute_python",
        "args": {
            "code": code
        }
    }
    s.sendall(json.dumps(payload).encode('utf-8'))
    response = s.recv(8192).decode('utf-8')
    print("Response from FreeCAD:")
    print(response)
except Exception as e:
    print(f"Failed to connect to FreeCAD GUI socket: {e}")
    sys.exit(1)
finally:
    s.close()
