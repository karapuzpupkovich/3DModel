import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part

from Стандартная_ячейка.builder import HoneycombBuildReport, create_Стандартная_ячейка_shape
from Стандартная_ячейка.config import DEFAULT_CONFIG


WOOD_COLOR = (0.91, 0.84, 0.72)
LEG_COLOR = (0.3, 0.3, 0.3)
DOOR_COLOR = (0.95, 0.95, 0.95)
CELL_COLORS = [
    (0.95, 0.75, 0.15),
    (0.85, 0.35, 0.25),
    (0.35, 0.65, 0.55),
    (0.85, 0.55, 0.15),
    (0.45, 0.75, 0.35),
]


def add_panel(doc, name, length, width, height, x, y, z, color):
    obj = doc.addObject("Part::Box", name)
    obj.Length = length
    obj.Width = width
    obj.Height = height
    obj.Placement = FreeCAD.Placement(FreeCAD.Vector(x, y, z), FreeCAD.Rotation(0, 0, 0))
    if obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def load_or_build_cell_shape(log=print):
    step_path = os.path.join(PROJECT_DIR, "Стандартная_ячейка", "output", "HoneycombCell.step")
    source_paths = [
        os.path.join(PROJECT_DIR, "Стандартная_ячейка", "builder.py"),
        os.path.join(PROJECT_DIR, "Стандартная_ячейка", "config.py"),
    ]
    if os.path.exists(step_path):
        try:
            step_mtime = os.path.getmtime(step_path)
            source_mtime = max(os.path.getmtime(path) for path in source_paths)
            if step_mtime < source_mtime:
                log("Exported STEP is stale, rebuilding cell geometry from source")
                raise ValueError("stale exported STEP")
            shape = Part.Shape()
            shape.read(step_path)
            if shape.isValid():
                log(f"Loading exported cell from: {step_path}")
                return shape, HoneycombBuildReport(valid=True)
            log("Exported STEP is invalid, rebuilding cell geometry")
        except Exception as exc:
            if str(exc) != "stale exported STEP":
                log(f"Failed to load exported cell: {exc}")
            log("Rebuilding cell geometry from source")
    return create_Стандартная_ячейка_shape(DEFAULT_CONFIG, enable_perforation=True, log=log)


def build_cabinet_document(log=print):
    doc = FreeCAD.newDocument("NikitasCabinet")
    sheet = doc.addObject("Spreadsheet::Sheet", "Spreadsheet")
    sheet.set("B1", "0")
    sheet.setAlias("B1", "DoorAngle")

    width = 322
    height = 1295
    depth = 350
    thickness = 16
    leg_height = 100
    headwear_height = 150
    spare_height = 115
    shoes_height = 200

    left_wall = add_panel(doc, "LeftWall", thickness, depth, height, 0, 0, 0, WOOD_COLOR)
    right_wall = add_panel(doc, "RightWall", thickness, depth, height, width - thickness, 0, 0, WOOD_COLOR)
    top_panel = add_panel(doc, "TopPanel", width - 2 * thickness, depth, thickness, thickness, 0, height - thickness, WOOD_COLOR)
    bottom_panel = add_panel(doc, "BottomPanel", width - 2 * thickness, depth, thickness, thickness, 0, 0, WOOD_COLOR)
    back_panel = add_panel(doc, "BackWall", width - 2 * thickness, thickness, height - 2 * thickness, thickness, depth - thickness, thickness, WOOD_COLOR)
    shelf_1 = add_panel(doc, "Shelf1_Headwear", width - 2 * thickness, depth - thickness, thickness, thickness, 0, height - thickness - headwear_height - thickness, WOOD_COLOR)
    shelf_2 = add_panel(doc, "Shelf2_Spare", width - 2 * thickness, depth - thickness, thickness, thickness, 0, height - thickness - headwear_height - thickness - spare_height - thickness, WOOD_COLOR)
    shelf_3 = add_panel(doc, "Shelf3_Shoes", width - 2 * thickness, depth - thickness, thickness, thickness, 0, thickness + shoes_height, WOOD_COLOR)

    leg1 = add_panel(doc, "Leg1", 30, 30, leg_height, 20, 20, -leg_height, LEG_COLOR)
    leg2 = add_panel(doc, "Leg2", 30, 30, leg_height, width - 50, 20, -leg_height, LEG_COLOR)
    leg3 = add_panel(doc, "Leg3", 30, 30, leg_height, 20, depth - 50, -leg_height, LEG_COLOR)
    leg4 = add_panel(doc, "Leg4", 30, 30, leg_height, width - 50, depth - 50, -leg_height, LEG_COLOR)

    door = doc.addObject("Part::Box", "Door")
    door.Length = width - 4
    door.Width = thickness
    door.Height = height - 4
    door.Placement = FreeCAD.Placement(FreeCAD.Vector(2, 0, 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, -1), 0))
    if door.ViewObject:
        door.ViewObject.ShapeColor = DOOR_COLOR
        door.ViewObject.Transparency = 50
    door.setExpression("Placement.Rotation.Angle", "Spreadsheet.DoorAngle")

    cell_shape, report = load_or_build_cell_shape(log=log)

    centers = [
        ("ShoeCell_1", 83.5, 64.0),
        ("ShoeCell_2", 83.5, 160.0),
        ("ShoeCell_3", 161.0, 112.0),
        ("ShoeCell_4", 238.5, 64.0),
        ("ShoeCell_5", 238.5, 160.0),
    ]

    cells = []
    for index, (name, center_x, center_z) in enumerate(centers):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = cell_shape.copy()
        rotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)
        obj.Placement = FreeCAD.Placement(FreeCAD.Vector(center_x, 20.0, center_z), rotation)
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = CELL_COLORS[index]
        cells.append(obj)

    group = doc.addObject("App::DocumentObjectGroup", "CabinetAssembly")
    group.Label = "Сборка Шкафчика"
    for obj in [
        left_wall,
        right_wall,
        top_panel,
        bottom_panel,
        back_panel,
        shelf_1,
        shelf_2,
        shelf_3,
        leg1,
        leg2,
        leg3,
        leg4,
        door,
        *cells,
    ]:
        group.addObject(obj)

    doc.recompute()
    return doc, report


def main():
    save_path = os.path.join(PROJECT_DIR, "Cabinet.FCStd")
    doc, report = build_cabinet_document(log=print)
    doc.saveAs(save_path)
    print(f"Valid cell shape: {report.valid}")
    if report.total_holes:
        print(f"Total holes in source cell: {report.total_holes}")
    print(f"Saved cabinet to: {save_path}")


if __name__ == "__main__":
    main()
