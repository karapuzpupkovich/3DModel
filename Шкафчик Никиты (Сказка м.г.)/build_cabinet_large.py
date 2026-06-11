import os
import sys

PROJECT_DIR = os.path.dirname(__file__)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: FreeCAD and Part modules must be loaded from within FreeCAD.")
    sys.exit(1)


WOOD_COLOR = (0.91, 0.84, 0.72)
LEG_COLOR = (0.3, 0.3, 0.3)
DOOR_COLOR = (0.95, 0.95, 0.95)
CELL_COLORS = [
    (0.95, 0.75, 0.15),  # Yellow
    (0.85, 0.35, 0.25),  # Terracotta
    (0.35, 0.65, 0.55),  # Turquoise
    (0.85, 0.55, 0.15),  # Orange
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


def load_shape(path):
    shape = Part.Shape()
    shape.read(path)
    return shape


def main():
    save_path = os.path.join(PROJECT_DIR, "Cabinet_large.FCStd")
    print(f"Generating large cabinet model and saving to: {save_path}")

    doc = FreeCAD.newDocument("NikitasCabinetLarge")
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

    # Main Cabinet Frame
    left_wall = add_panel(doc, "LeftWall", thickness, depth, height, 0, 0, 0, WOOD_COLOR)
    right_wall = add_panel(doc, "RightWall", thickness, depth, height, width - thickness, 0, 0, WOOD_COLOR)
    top_panel = add_panel(doc, "TopPanel", width - 2 * thickness, depth, thickness, thickness, 0, height - thickness, WOOD_COLOR)
    bottom_panel = add_panel(doc, "BottomPanel", width - 2 * thickness, depth, thickness, thickness, 0, 0, WOOD_COLOR)
    back_panel = add_panel(doc, "BackWall", width - 2 * thickness, thickness, height - 2 * thickness, thickness, depth - thickness, thickness, WOOD_COLOR)
    shelf_1 = add_panel(doc, "Shelf1_Headwear", width - 2 * thickness, depth - thickness, thickness, thickness, 0, height - thickness - headwear_height - thickness, WOOD_COLOR)
    shelf_2 = add_panel(doc, "Shelf2_Spare", width - 2 * thickness, depth - thickness, thickness, thickness, 0, height - thickness - headwear_height - thickness - spare_height - thickness, WOOD_COLOR)
    shelf_3 = add_panel(doc, "Shelf3_Shoes", width - 2 * thickness, depth - thickness, thickness, thickness, 0, thickness + shoes_height, WOOD_COLOR)

    # Legs
    leg1 = add_panel(doc, "Leg1", 30, 30, leg_height, 20, 20, -leg_height, LEG_COLOR)
    leg2 = add_panel(doc, "Leg2", 30, 30, leg_height, width - 50, 20, -leg_height, LEG_COLOR)
    leg3 = add_panel(doc, "Leg3", 30, 30, leg_height, 20, depth - 50, -leg_height, LEG_COLOR)
    leg4 = add_panel(doc, "Leg4", 30, 30, leg_height, width - 50, depth - 50, -leg_height, LEG_COLOR)

    # Door
    door = doc.addObject("Part::Box", "Door")
    door.Length = width - 4
    door.Width = thickness
    door.Height = height - 4
    door.Placement = FreeCAD.Placement(FreeCAD.Vector(2, 0, 2), FreeCAD.Rotation(FreeCAD.Vector(0, 0, -1), 0))
    if door.ViewObject:
        door.ViewObject.ShapeColor = DOOR_COLOR
        door.ViewObject.Transparency = 50
    door.setExpression("Placement.Rotation.Angle", "Spreadsheet.DoorAngle")

    # Load shapes of the Large Cell and Bottom Support Plate
    cell_path = os.path.join(PROJECT_DIR, "Увеличенная_ячейка", "output", "HoneycombCell_large.step")
    plate_path = os.path.join(PROJECT_DIR, "Увеличенная_ячейка", "output", "BottomPlate.step")

    if not os.path.exists(cell_path) or not os.path.exists(plate_path):
        print("Error: large cell or bottom plate step files not found. Build them first!")
        sys.exit(1)

    cell_shape = load_shape(cell_path)
    plate_shape = load_shape(plate_path)

    # Add Bottom Support Plate to the document
    plate_obj = doc.addObject("Part::Feature", "BottomSupportPlate")
    plate_obj.Shape = plate_shape
    # Position: Centered horizontally at X=161.0, Y=20.0, Z=16.0 (resting on bottom shelf)
    plate_obj.Placement = FreeCAD.Placement(FreeCAD.Vector(161.0, 20.0, 16.0), FreeCAD.Rotation(0, 0, 0))
    if plate_obj.ViewObject:
        plate_obj.ViewObject.ShapeColor = (0.5, 0.5, 0.5)  # Neutral grey

    # Add 4 Large Cells in 2x2 grid
    # Center-to-center offsets: dX = 144.0, dZ = 97.0
    # Base cell height starts at Z = 16.0 + 4.8 = 20.8
    # Centers of bottom cells: Z = 20.8 + 48.5 = 69.3
    # Centers of top cells: Z = 69.3 + 97.0 = 166.3
    centers = [
        ("LargeCell_1", 89.0, 69.3),   # Bottom-Left
        ("LargeCell_2", 233.0, 69.3),  # Bottom-Right
        ("LargeCell_3", 89.0, 166.3),  # Top-Left
        ("LargeCell_4", 233.0, 166.3), # Top-Right
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
    group.Label = "Сборка Шкафчика (Большие Ячейки)"
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
        plate_obj,
        *cells,
    ]:
        group.addObject(obj)

    doc.recompute()
    doc.saveAs(save_path)
    print(f"Assembly built successfully and saved to: {save_path}")


if __name__ == "__main__":
    main()
