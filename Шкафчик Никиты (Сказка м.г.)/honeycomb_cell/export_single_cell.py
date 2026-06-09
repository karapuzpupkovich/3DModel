import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

print("=" * 60)
print("  Building single honeycomb cell")
print("=" * 60)

try:
    import FreeCAD
    import Mesh
    import Part
except ImportError:
    print("Error: This script must run inside a FreeCAD environment.")
    sys.exit(1)

from honeycomb_cell.builder import create_honeycomb_cell_shape
from honeycomb_cell.config import DEFAULT_CONFIG


def main() -> None:
    doc = FreeCAD.newDocument("HoneycombCell")
    shape, report = create_honeycomb_cell_shape(DEFAULT_CONFIG, enable_perforation=True, log=print)

    obj = doc.addObject("Part::Feature", "HoneycombCell")
    obj.Shape = shape
    if obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.75, 0.75, 0.78)

    doc.recompute()

    output_dir = os.path.join(PROJECT_DIR, "honeycomb_cell", "output")
    os.makedirs(output_dir, exist_ok=True)

    fcstd_path = os.path.join(output_dir, "HoneycombCell.FCStd")
    step_path = os.path.join(output_dir, "HoneycombCell.step")
    stl_path = os.path.join(output_dir, "HoneycombCell.stl")

    doc.saveAs(fcstd_path)
    Part.export([obj], step_path)
    mesh = Mesh.export([obj], stl_path)
    _ = mesh

    print(f"Valid shape: {report.valid}")
    print(f"Total holes: {report.total_holes}")
    for face_index in sorted(report.holes_by_face):
        print(f"  Face {face_index}: {report.holes_by_face[face_index]} holes")
    print(f"Saved FCStd to: {fcstd_path}")
    print(f"Saved STEP to: {step_path}")
    print(f"Saved STL to: {stl_path}")
    print("=" * 60)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
