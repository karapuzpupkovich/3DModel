import os
import sys

# Ensure parent directory is in path for relative imports
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: must run inside FreeCAD command line.")
    sys.exit(1)

from Увеличенная_ячейка.builder import create_large_cell_shape, create_bottom_plate_shape
from Увеличенная_ячейка.config import DEFAULT_CONFIG


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Building large honeycomb cell...")
    cell_shape, report = create_large_cell_shape(DEFAULT_CONFIG, enable_perforation=True, log=print)
    print(f"Cell valid: {report.valid}, total holes: {report.total_holes}")

    cell_doc = FreeCAD.newDocument("LargeCell")
    cell_obj = cell_doc.addObject("Part::Feature", "HoneycombCell_Large")
    cell_obj.Shape = cell_shape
    cell_doc.recompute()
    
    cell_fcstd = os.path.join(output_dir, "HoneycombCell_large.FCStd")
    cell_doc.saveAs(cell_fcstd)
    print(f"Saved cell FCStd to: {cell_fcstd}")

    cell_step = os.path.join(output_dir, "HoneycombCell_large.step")
    cell_shape.exportStep(cell_step)
    print(f"Saved cell STEP to: {cell_step}")

    cell_stl = os.path.join(output_dir, "HoneycombCell_large.stl")
    cell_shape.exportStl(cell_stl)
    print(f"Saved cell STL to: {cell_stl}")

    print("\nBuilding bottom support plate...")
    plate_shape = create_bottom_plate_shape(DEFAULT_CONFIG, log=print)
    print(f"Plate valid: {plate_shape.isValid()}")

    plate_doc = FreeCAD.newDocument("BottomPlate")
    plate_obj = plate_doc.addObject("Part::Feature", "BottomPlate")
    plate_obj.Shape = plate_shape
    plate_doc.recompute()

    plate_fcstd = os.path.join(output_dir, "BottomPlate.FCStd")
    plate_doc.saveAs(plate_fcstd)
    print(f"Saved plate FCStd to: {plate_fcstd}")

    plate_step = os.path.join(output_dir, "BottomPlate.step")
    plate_shape.exportStep(plate_step)
    print(f"Saved plate STEP to: {plate_step}")

    plate_stl = os.path.join(output_dir, "BottomPlate.stl")
    plate_shape.exportStl(plate_stl)
    print(f"Saved plate STL to: {plate_stl}")

    print("\nAll models generated successfully!")


if __name__ == "__main__":
    main()
