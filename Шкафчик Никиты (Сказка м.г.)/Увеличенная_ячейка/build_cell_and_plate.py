import os
import sys

# Ensure parent directory is in path for relative imports
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
    import Part
    import Mesh
except ImportError:
    print("Error: must run inside FreeCAD command line.")
    sys.exit(1)

from Увеличенная_ячейка.builder import (
    create_large_cell_shape,
    create_bottom_plate_shape,
    create_split_plate_left_shape,
    create_split_plate_right_shape,
    create_short_plate_with_name_shape
)
from Увеличенная_ячейка.config import DEFAULT_CONFIG


def export_shape(shape, name, output_dir):
    doc = FreeCAD.newDocument(name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()

    fcstd = os.path.join(output_dir, f"{name}.FCStd")
    doc.saveAs(fcstd)
    print(f"Saved {name} FCStd to: {fcstd}")

    step = os.path.join(output_dir, f"{name}.step")
    shape.exportStep(step)
    print(f"Saved {name} STEP to: {step}")

    stl = os.path.join(output_dir, f"{name}.stl")
    Mesh.export([obj], stl)
    print(f"Saved {name} STL to: {stl}")
    
    FreeCAD.closeDocument(name)


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Building large honeycomb cell...")
    cell_shape, report = create_large_cell_shape(DEFAULT_CONFIG, enable_perforation=True, log=print)
    print(f"Cell valid: {report.valid}, total holes: {report.total_holes}")
    export_shape(cell_shape, "HoneycombCell_large", output_dir)

    print("\nBuilding bottom support plate (Original 288mm)...")
    plate_shape = create_bottom_plate_shape(DEFAULT_CONFIG, log=print)
    export_shape(plate_shape, "BottomPlate", output_dir)

    print("\nBuilding Left Split support plate (144mm)...")
    split_L_shape = create_split_plate_left_shape(DEFAULT_CONFIG, log=print)
    export_shape(split_L_shape, "BottomPlate_split_L", output_dir)

    print("\nBuilding Right Split support plate (144mm)...")
    split_R_shape = create_split_plate_right_shape(DEFAULT_CONFIG, log=print)
    export_shape(split_R_shape, "BottomPlate_split_R", output_dir)

    print("\nBuilding Short support plate with engraving (250mm)...")
    short_name_shape = create_short_plate_with_name_shape(DEFAULT_CONFIG, log=print)
    export_shape(short_name_shape, "BottomPlate_short_name", output_dir)

    print("\nAll models generated successfully!")


if __name__ == "__main__":
    main()
