# -*- coding: utf-8 -*-
"""
Параметрический генератор усиленного крепления шторки багажника Renault Duster.

Что делает скрипт:
  * перестраивает профиль крепления под внутренний радиус 8 мм;
  * переносит отверстие Ø5 в вершину дуговой части;
  * усиливает опасные зоны за счет более толстой дуги и полки;
  * экспортирует STL, STEP, FCStd, SVG-чертеж и Markdown-спецификацию.

Запуск:
  "C:/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" build_cargo_cover_bracket.py
"""

import html
import math
import os
import textwrap

import FreeCAD as App
import MeshPart
import Part


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_NAME = "DusterCargoCoverBracket"
OBJECT_NAME = "CargoCoverBracket"

STL_PATH = os.path.join(ROOT_DIR, "Крепление_шторки.stl")
STEP_PATH = os.path.join(ROOT_DIR, "Крепление_шторки.step")
FCSTD_PATH = os.path.join(ROOT_DIR, "Крепление_шторки.FCStd")
SVG_PATH = os.path.join(ROOT_DIR, "Чертеж_крепления.svg")
MD_PATH = os.path.join(ROOT_DIR, "размеры_и_описание.md")

# Основные размеры, мм
LENGTH = 110.0
WIDTH = 30.0
BASE_THICKNESS = 4.0
INNER_RADIUS = 8.0
OUTER_RADIUS = INNER_RADIUS + BASE_THICKNESS
RIGHT_END_RADIUS = 10.0
HOOK_CENTER_X = OUTER_RADIUS
HOOK_CENTER_Y = BASE_THICKNESS
HOOK_LIP = OUTER_RADIUS - INNER_RADIUS
LIP_DROP = BASE_THICKNESS
HOLE_DIAMETER = 5.0
HOLE_RADIUS = HOLE_DIAMETER / 2.0
HOLE_CENTER_X = HOOK_CENTER_X
HOLE_CENTER_Z = WIDTH / 2.0
OVERALL_HEIGHT = HOOK_CENTER_Y + OUTER_RADIUS
CROWN_THICKNESS = OUTER_RADIUS - INNER_RADIUS
HOLE_TOP_Y = OVERALL_HEIGHT
HOLE_BOTTOM_Y = HOOK_CENTER_Y + INNER_RADIUS

SHOULDER_RUN = 10.0
SHOULDER_END_X = HOOK_CENTER_X + INNER_RADIUS + SHOULDER_RUN

# Оценочные нагрузки
STATIC_LOAD_MIN = 10.0
STATIC_LOAD_MAX = 20.0
DYNAMIC_LOAD_MAX = 60.0
IMPACT_LOAD_MAX = 70.0



# Параметры листа SVG
SHEET_W = 1400
SHEET_H = 920
SCALE = 5.0

PROFILE_ORIGIN_X = 140.0
PROFILE_ORIGIN_Y = 300.0
TOP_ORIGIN_X = 140.0
TOP_ORIGIN_Y = 720.0
END_ORIGIN_X = 900.0
END_ORIGIN_Y = 300.0

MODEL_COLOR = "#111111"
DIM_COLOR = "#1f77b4"
HIDDEN_COLOR = "#7f8c8d"
CENTER_COLOR = "#c0392b"
NOTE_FILL = "#f5f5f0"


def vec(x, y, z=0.0):
    return App.Vector(float(x), float(y), float(z))


def arc_points(cx, cy, radius, start_deg, end_deg, segments):
    points = []
    for index in range(segments + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * index / float(segments))
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def shoulder_tangent_point():
    dx = SHOULDER_END_X - HOOK_CENTER_X
    x_local = (OUTER_RADIUS * OUTER_RADIUS) / dx
    y_local = math.sqrt(max(OUTER_RADIUS * OUTER_RADIUS - x_local * x_local, 0.0))
    x_val = HOOK_CENTER_X + x_local
    y_val = HOOK_CENTER_Y + y_local
    angle_deg = math.degrees(math.atan2(y_local, x_local))
    return x_val, y_val, angle_deg


def build_profile_face():
    polygon = Part.makePolygon([vec(x_val, y_val) for x_val, y_val in profile_outline_points()])
    return Part.Face(polygon)


def build_upper_semidisc_face(radius):
    left = vec(HOOK_CENTER_X - radius, HOOK_CENTER_Y)
    right = vec(HOOK_CENTER_X + radius, HOOK_CENTER_Y)
    top = vec(HOOK_CENTER_X, HOOK_CENTER_Y + radius)
    wire = Part.Wire([
        Part.LineSegment(left, right).toShape(),
        Part.Arc(right, top, left).toShape(),
    ])
    return Part.Face(wire)


def build_rectangle_face(x0, x1, y0, y1):
    wire = Part.makePolygon([
        vec(x0, y0),
        vec(x1, y0),
        vec(x1, y1),
        vec(x0, y1),
        vec(x0, y0),
    ])
    return Part.Face(wire)


def build_tail_rounding_cutters():
    margin = 1.0
    y_plane = -margin
    height = OVERALL_HEIGHT + 2.0 * margin
    quarter = RIGHT_END_RADIUS / math.sqrt(2.0)

    lower_edges = [
        Part.LineSegment(vec(LENGTH - RIGHT_END_RADIUS, y_plane, 0.0), vec(LENGTH, y_plane, 0.0)).toShape(),
        Part.LineSegment(vec(LENGTH, y_plane, 0.0), vec(LENGTH, y_plane, RIGHT_END_RADIUS)).toShape(),
        Part.Arc(
            vec(LENGTH, y_plane, RIGHT_END_RADIUS),
            vec(LENGTH - RIGHT_END_RADIUS + quarter, y_plane, RIGHT_END_RADIUS - quarter),
            vec(LENGTH - RIGHT_END_RADIUS, y_plane, 0.0),
        ).toShape(),
    ]

    upper_edges = [
        Part.LineSegment(vec(LENGTH, y_plane, WIDTH - RIGHT_END_RADIUS), vec(LENGTH, y_plane, WIDTH)).toShape(),
        Part.LineSegment(vec(LENGTH, y_plane, WIDTH), vec(LENGTH - RIGHT_END_RADIUS, y_plane, WIDTH)).toShape(),
        Part.Arc(
            vec(LENGTH - RIGHT_END_RADIUS, y_plane, WIDTH),
            vec(LENGTH - RIGHT_END_RADIUS + quarter, y_plane, WIDTH - RIGHT_END_RADIUS + quarter),
            vec(LENGTH, y_plane, WIDTH - RIGHT_END_RADIUS),
        ).toShape(),
    ]

    lower = Part.Face(Part.Wire(lower_edges)).extrude(vec(0.0, height, 0.0))
    upper = Part.Face(Part.Wire(upper_edges)).extrude(vec(0.0, height, 0.0))
    return lower.fuse(upper)


def build_solid():
    hole_margin = 1.0
    solid = build_profile_face().extrude(vec(0.0, 0.0, WIDTH))
    solid = solid.removeSplitter()
    hole_cutter = Part.makeCylinder(
        HOLE_RADIUS,
        OVERALL_HEIGHT + 2.0 * hole_margin,
        vec(HOLE_CENTER_X, OVERALL_HEIGHT + hole_margin, HOLE_CENTER_Z),
        vec(0.0, -1.0, 0.0),
    )
    solid = solid.cut(hole_cutter)
    solid = solid.removeSplitter()
    solid = solid.cut(build_tail_rounding_cutters())
    solid = solid.removeSplitter()
    return solid


def profile_outline_points():
    tangent_x, tangent_y, tangent_angle = shoulder_tangent_point()
    points = [
        (0.0, 0.0),
        (0.0, BASE_THICKNESS),
    ]
    points.extend(arc_points(HOOK_CENTER_X, HOOK_CENTER_Y, OUTER_RADIUS, 180.0, tangent_angle, 44)[1:])
    points.append((SHOULDER_END_X, BASE_THICKNESS))
    points.extend([
        (LENGTH, BASE_THICKNESS),
        (LENGTH, 0.0),
        (HOOK_CENTER_X + INNER_RADIUS, 0.0),
        (HOOK_CENTER_X + INNER_RADIUS, BASE_THICKNESS),
    ])
    points.extend(arc_points(HOOK_CENTER_X, HOOK_CENTER_Y, INNER_RADIUS, 0.0, 180.0, 40)[1:])
    points.extend([
        (HOOK_LIP, 0.0),
        (0.0, 0.0),
    ])
    return points


def top_outline_points():
    points = [(0.0, 0.0), (LENGTH - RIGHT_END_RADIUS, 0.0)]
    points.extend(arc_points(LENGTH - RIGHT_END_RADIUS, RIGHT_END_RADIUS, RIGHT_END_RADIUS, -90.0, 0.0, 14)[1:])
    points.append((LENGTH, WIDTH - RIGHT_END_RADIUS))
    points.extend(
        arc_points(
            LENGTH - RIGHT_END_RADIUS,
            WIDTH - RIGHT_END_RADIUS,
            RIGHT_END_RADIUS,
            0.0,
            90.0,
            14,
        )[1:]
    )
    points.append((0.0, WIDTH))
    points.append((0.0, 0.0))
    return points


def svg_point(origin_x, origin_y, x_val, y_val):
    return origin_x + x_val * SCALE, origin_y - y_val * SCALE


def poly_path(points, origin_x, origin_y):
    if not points:
        return ""
    screen_points = [svg_point(origin_x, origin_y, px, py) for px, py in points]
    head = "M %.2f,%.2f" % screen_points[0]
    tail = ["L %.2f,%.2f" % point for point in screen_points[1:]]
    return " ".join([head] + tail)


def svg_line(x1, y1, x2, y2, stroke, width=1.0, dash=None, marker_start=False, marker_end=False):
    attrs = [
        "x1=\"%.2f\"" % x1,
        "y1=\"%.2f\"" % y1,
        "x2=\"%.2f\"" % x2,
        "y2=\"%.2f\"" % y2,
        "stroke=\"%s\"" % stroke,
        "stroke-width=\"%.1f\"" % width,
    ]
    if dash:
        attrs.append("stroke-dasharray=\"%s\"" % dash)
    if marker_start:
        attrs.append("marker-start=\"url(#arrow)\"")
    if marker_end:
        attrs.append("marker-end=\"url(#arrow)\"")
    return "<line %s />" % " ".join(attrs)


def svg_text(x_pos, y_pos, text, size=12, color="#000000", anchor="middle", weight="normal"):
    return (
        "<text x=\"%.2f\" y=\"%.2f\" font-family=\"Arial, sans-serif\" "
        "font-size=\"%d\" font-weight=\"%s\" fill=\"%s\" text-anchor=\"%s\">%s</text>"
    ) % (x_pos, y_pos, size, weight, color, anchor, html.escape(text))


def svg_path(d_value, stroke=MODEL_COLOR, width=2.0, fill="none", dash=None):
    attrs = [
        "d=\"%s\"" % d_value,
        "stroke=\"%s\"" % stroke,
        "stroke-width=\"%.1f\"" % width,
        "fill=\"%s\"" % fill,
        "stroke-linejoin=\"round\"",
        "stroke-linecap=\"round\"",
    ]
    if dash:
        attrs.append("stroke-dasharray=\"%s\"" % dash)
    return "<path %s />" % " ".join(attrs)


def add_horizontal_dimension(elements, x1, x2, base_y, dim_y, label):
    elements.append(svg_line(x1, base_y, x1, dim_y, DIM_COLOR, width=1.0))
    elements.append(svg_line(x2, base_y, x2, dim_y, DIM_COLOR, width=1.0))
    elements.append(svg_line(x1, dim_y, x2, dim_y, DIM_COLOR, width=1.0, marker_start=True, marker_end=True))
    elements.append(svg_text((x1 + x2) / 2.0, dim_y - 6.0, label, size=12, color=DIM_COLOR))


def add_vertical_dimension(elements, x_base, y1, y2, dim_x, label, anchor="end"):
    elements.append(svg_line(x_base, y1, dim_x, y1, DIM_COLOR, width=1.0))
    elements.append(svg_line(x_base, y2, dim_x, y2, DIM_COLOR, width=1.0))
    elements.append(svg_line(dim_x, y1, dim_x, y2, DIM_COLOR, width=1.0, marker_start=True, marker_end=True))
    text_x = dim_x - 8.0 if anchor == "end" else dim_x + 8.0
    text_anchor = "end" if anchor == "end" else "start"
    elements.append(svg_text(text_x, (y1 + y2) / 2.0 + 4.0, label, size=12, color=DIM_COLOR, anchor=text_anchor))


def add_leader(elements, points, label, anchor="start"):
    for index in range(len(points) - 1):
        x1, y1 = points[index]
        x2, y2 = points[index + 1]
        elements.append(
            svg_line(
                x1,
                y1,
                x2,
                y2,
                DIM_COLOR,
                width=1.0,
                marker_end=index == 0,
            )
        )
    text_x, text_y = points[-1]
    shift = 6.0 if anchor == "start" else -6.0
    text_anchor = "start" if anchor == "start" else "end"
    elements.append(svg_text(text_x + shift, text_y - 4.0, label, size=12, color=DIM_COLOR, anchor=text_anchor))


def render_svg():
    profile_pts = profile_outline_points()
    top_pts = top_outline_points()
    tangent_x, tangent_y, _ = shoulder_tangent_point()

    profile_path = poly_path(profile_pts, PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y)
    top_path = poly_path(top_pts, TOP_ORIGIN_X, TOP_ORIGIN_Y)

    px0, py0 = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, 0.0, 0.0)
    px1, py1 = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, LENGTH, 0.0)
    p_top_y = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, 0.0, OVERALL_HEIGHT)[1]
    base_top_y = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, 0.0, BASE_THICKNESS)[1]
    hole_centerline_x = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, HOOK_CENTER_X, 0.0)[0]
    hole_profile_left_x = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, HOOK_CENTER_X - HOLE_RADIUS, 0.0)[0]
    hole_profile_right_x = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, HOOK_CENTER_X + HOLE_RADIUS, 0.0)[0]
    hole_profile_top_y = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, 0.0, HOLE_TOP_Y)[1]
    hole_profile_bottom_y = svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, 0.0, HOLE_BOTTOM_Y)[1]

    top_left_x, top_bottom_y = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, 0.0, 0.0)
    top_right_x = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, LENGTH, 0.0)[0]
    top_top_y = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, 0.0, WIDTH)[1]
    hole_top_cx, hole_top_cy = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, HOLE_CENTER_X, HOLE_CENTER_Z)
    hole_left_x = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, HOLE_CENTER_X - HOLE_RADIUS, 0.0)[0]
    hole_right_x = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, HOLE_CENTER_X + HOLE_RADIUS, 0.0)[0]
    top_mid_z_y = svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, 0.0, HOLE_CENTER_Z)[1]

    end_left_x, end_bottom_y = svg_point(END_ORIGIN_X, END_ORIGIN_Y, 0.0, 0.0)
    end_right_x = svg_point(END_ORIGIN_X, END_ORIGIN_Y, WIDTH, 0.0)[0]
    end_top_y = svg_point(END_ORIGIN_X, END_ORIGIN_Y, 0.0, OVERALL_HEIGHT)[1]
    hole_end_left_x = svg_point(END_ORIGIN_X, END_ORIGIN_Y, HOLE_CENTER_Z - HOLE_RADIUS, 0.0)[0]
    hole_end_right_x = svg_point(END_ORIGIN_X, END_ORIGIN_Y, HOLE_CENTER_Z + HOLE_RADIUS, 0.0)[0]
    hole_end_top_y = svg_point(END_ORIGIN_X, END_ORIGIN_Y, 0.0, HOLE_TOP_Y)[1]
    hole_end_bottom_y = svg_point(END_ORIGIN_X, END_ORIGIN_Y, 0.0, HOLE_BOTTOM_Y)[1]

    elements = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"%d\" height=\"%d\" viewBox=\"0 0 %d %d\">" % (
            SHEET_W,
            SHEET_H,
            SHEET_W,
            SHEET_H,
        ),
        "<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\" />",
        "<rect x=\"20\" y=\"20\" width=\"1360\" height=\"880\" stroke=\"#000000\" stroke-width=\"1\" fill=\"none\" />",
        "<rect x=\"30\" y=\"30\" width=\"1340\" height=\"860\" stroke=\"#000000\" stroke-width=\"2\" fill=\"none\" />",
        "<defs>",
        "  <marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"5\" refY=\"5\" markerWidth=\"6\" markerHeight=\"6\" orient=\"auto-start-reverse\">",
        "    <path d=\"M 0 2 L 10 5 L 0 8 z\" fill=\"%s\" />" % DIM_COLOR,
        "  </marker>",
        "</defs>",
    ]

    elements.append(svg_text(410.0, 78.0, "Крепление шторки багажника Renault Duster", size=22, weight="bold"))
    elements.append(svg_text(410.0, 104.0, "Rвн = 8 мм, стенка 4 мм, отверстие Ø5 вертикально", size=13))
    elements.append(svg_text(360.0, 130.0, "Главный вид (профиль)", size=14, weight="bold"))

    elements.append(svg_path(profile_path))
    elements.append(svg_line(hole_profile_left_x, hole_profile_top_y, hole_profile_left_x, hole_profile_bottom_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_profile_right_x, hole_profile_top_y, hole_profile_right_x, hole_profile_bottom_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_profile_left_x, hole_profile_top_y, hole_profile_right_x, hole_profile_top_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_profile_left_x, hole_profile_bottom_y, hole_profile_right_x, hole_profile_bottom_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_centerline_x, p_top_y - 20.0, hole_centerline_x, py0 + 20.0, CENTER_COLOR, width=1.0, dash="10,4,2,4"))

    add_horizontal_dimension(elements, px0, px1, py0, py0 + 58.0, "110")
    add_vertical_dimension(elements, px0, p_top_y, py0, px0 - 58.0, "16", anchor="end")
    add_vertical_dimension(elements, px1, base_top_y, py0, px1 + 40.0, "4", anchor="start")
    add_horizontal_dimension(elements, px0, hole_centerline_x, py0, py0 + 100.0, "12")
    add_leader(
        elements,
        [
            svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, HOOK_CENTER_X - INNER_RADIUS * 0.35, HOOK_CENTER_Y + INNER_RADIUS * 0.92),
            (px0 - 34.0, p_top_y + 30.0),
            (px0 - 90.0, p_top_y + 10.0),
        ],
        "R8",
        anchor="end",
    )
    add_leader(
        elements,
        [
            svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, HOOK_CENTER_X - OUTER_RADIUS * 0.58, HOOK_CENTER_Y + OUTER_RADIUS * 0.82),
            (px0 - 10.0, p_top_y - 5.0),
            (px0 - 90.0, p_top_y - 30.0),
        ],
        "R12",
        anchor="end",
    )
    add_leader(
        elements,
        [
            svg_point(PROFILE_ORIGIN_X, PROFILE_ORIGIN_Y, tangent_x + 2.0, tangent_y - 0.6),
            (px0 + 240.0, p_top_y - 30.0),
            (px0 + 355.0, p_top_y - 30.0),
        ],
        "Плавное усиление сопряжения",
        anchor="start",
    )

    elements.append(svg_text(365.0, 470.0, "Вид сверху", size=14, weight="bold"))
    elements.append(svg_path(top_path))
    elements.append(
        "<circle cx=\"%.2f\" cy=\"%.2f\" r=\"%.2f\" stroke=\"%s\" stroke-width=\"2\" fill=\"none\" />"
        % (hole_top_cx, hole_top_cy, HOLE_RADIUS * SCALE, MODEL_COLOR)
    )
    elements.append(svg_line(hole_top_cx, top_top_y - 18.0, hole_top_cx, top_bottom_y + 18.0, CENTER_COLOR, width=1.0, dash="10,4,2,4"))
    elements.append(svg_line(top_left_x - 18.0, hole_top_cy, top_right_x + 18.0, hole_top_cy, CENTER_COLOR, width=1.0, dash="10,4,2,4"))
    add_vertical_dimension(elements, top_left_x, top_top_y, top_bottom_y, top_left_x - 46.0, "30", anchor="end")
    add_horizontal_dimension(elements, top_left_x, hole_top_cx, top_bottom_y, top_bottom_y + 74.0, "12")
    add_vertical_dimension(elements, hole_top_cx, hole_top_cy, top_bottom_y, top_right_x + 44.0, "15", anchor="start")
    add_leader(
        elements,
        [
            svg_point(TOP_ORIGIN_X, TOP_ORIGIN_Y, LENGTH - RIGHT_END_RADIUS * 0.23, WIDTH - RIGHT_END_RADIUS * 0.23),
            (top_right_x + 40.0, top_top_y - 40.0),
            (top_right_x + 110.0, top_top_y - 40.0),
        ],
        "2x R10",
        anchor="start",
    )
    add_leader(
        elements,
        [
            (hole_top_cx + HOLE_RADIUS * SCALE * 0.3, hole_top_cy - HOLE_RADIUS * SCALE * 0.9),
            (hole_top_cx + 46.0, hole_top_cy - 56.0),
            (hole_top_cx + 112.0, hole_top_cy - 56.0),
        ],
        "Ø5",
        anchor="start",
    )
    elements.append(svg_text((top_left_x + top_right_x) / 2.0, top_bottom_y + 42.0, "Отверстие показано в истинном размере, ось вдоль высоты детали", size=11, color=HIDDEN_COLOR))

    elements.append(svg_text(975.0, 130.0, "Вид с торца", size=14, weight="bold"))
    elements.append(
        "<rect x=\"%.2f\" y=\"%.2f\" width=\"%.2f\" height=\"%.2f\" stroke=\"%s\" stroke-width=\"2\" fill=\"none\" />"
        % (end_left_x, end_top_y, WIDTH * SCALE, OVERALL_HEIGHT * SCALE, MODEL_COLOR)
    )
    elements.append(svg_line(hole_end_left_x, hole_end_top_y, hole_end_left_x, hole_end_bottom_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_end_right_x, hole_end_top_y, hole_end_right_x, hole_end_bottom_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_end_left_x, hole_end_top_y, hole_end_right_x, hole_end_top_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(hole_end_left_x, hole_end_bottom_y, hole_end_right_x, hole_end_bottom_y, HIDDEN_COLOR, width=1.0, dash="6,4"))
    elements.append(svg_line(svg_point(END_ORIGIN_X, END_ORIGIN_Y, HOLE_CENTER_Z, 0.0)[0], end_top_y - 18.0, svg_point(END_ORIGIN_X, END_ORIGIN_Y, HOLE_CENTER_Z, 0.0)[0], end_bottom_y + 18.0, CENTER_COLOR, width=1.0, dash="10,4,2,4"))
    add_horizontal_dimension(elements, end_left_x, end_right_x, end_bottom_y, end_bottom_y + 52.0, "30")
    add_vertical_dimension(elements, end_left_x, end_top_y, end_bottom_y, end_right_x + 44.0, "16", anchor="start")

    notes_x = 780.0
    notes_y = 500.0
    notes_w = 540.0
    notes_h = 250.0
    elements.append(
        "<rect x=\"%.2f\" y=\"%.2f\" width=\"%.2f\" height=\"%.2f\" rx=\"12\" ry=\"12\" fill=\"%s\" stroke=\"#cccccc\" stroke-width=\"1.5\" />"
        % (notes_x, notes_y, notes_w, notes_h, NOTE_FILL)
    )
    elements.append(svg_text(notes_x + 20.0, notes_y + 28.0, "Конструктивные изменения", size=14, weight="bold", anchor="start"))
    note_lines = [
        "1. Внутренний радиус крюка уменьшен до 8 мм по запросу.",
        "2. Отверстие Ø5 сделано вертикальным и перенесено в вершину дуги.",
        "3. Толщина стенки и полки везде сохранена 4 мм.",
        "4. Усиление выполнено плавным касательным плечом в правом сопряжении.",
        "5. Хвост детали завершен скруглением 2x R10 без острых углов.",
        "6. Печать: на боковой грани, PETG/ASA, не менее 5 периметров.",
    ]
    for index, line in enumerate(note_lines):
        elements.append(svg_text(notes_x + 20.0, notes_y + 58.0 + index * 28.0, line, size=12, anchor="start"))

    title_x = 920.0
    title_y = 790.0
    elements.append("<rect x=\"780\" y=\"770\" width=\"560\" height=\"100\" stroke=\"#000000\" stroke-width=\"2\" fill=\"none\" />")
    elements.append("<line x1=\"1030\" y1=\"770\" x2=\"1030\" y2=\"870\" stroke=\"#000000\" stroke-width=\"1\" />")
    elements.append("<line x1=\"780\" y1=\"810\" x2=\"1340\" y2=\"810\" stroke=\"#000000\" stroke-width=\"1\" />")
    elements.append(svg_text(800.0, 795.0, "Деталь", size=10, anchor="start"))
    elements.append(svg_text(800.0, 830.0, "Крепление шторки багажника", size=13, weight="bold", anchor="start"))
    elements.append(svg_text(800.0, 850.0, "Renault Duster · усиленная версия", size=11, anchor="start"))
    elements.append(svg_text(1050.0, 795.0, "Масштаб", size=10, anchor="start"))
    elements.append(svg_text(1050.0, 830.0, "5:1", size=13, weight="bold", anchor="start"))
    elements.append(svg_text(1150.0, 795.0, "Лист", size=10, anchor="start"))
    elements.append(svg_text(1150.0, 830.0, "1 / 1", size=13, weight="bold", anchor="start"))
    elements.append(svg_text(1050.0, 852.0, "Все размеры в мм", size=10, anchor="start"))

    elements.append("</svg>")

    with open(SVG_PATH, "w", encoding="utf-8") as svg_file:
        svg_file.write("\n".join(elements) + "\n")


def write_markdown(shape):
    volume_cm3 = shape.Volume / 1000.0
    mass_petg = volume_cm3 * 1.27
    mass_asa = volume_cm3 * 1.07
    bb = shape.BoundBox

    content = textwrap.dedent(
        f"""
        # Описание и размеры: Крепление для шторки Renault Duster

        Этот файл описывает обновленную, усиленную версию крепления (кронштейна) для шторки багажника Renault Duster.
        Геометрия пересобрана параметрически, а выпускные файлы STL, STEP, FCStd и SVG-чертеж генерируются скриптом [build_cargo_cover_bracket.py](build_cargo_cover_bracket.py).

        ## Назначение детали

        Деталь работает как опорный крюк для торцевой штанги шторки багажника. На нее действует не только статический вес шторки,
        но и динамические нагрузки от тряски кузова, захлопывания двери багажника, вибраций и рывка при снятии/установке шторки.
        Поэтому для обновленной версии были усилены именно те зоны, где у FDM-детали обычно возникает усталостный излом.

        ## Что изменено

        - Внутренний радиус крюка изменен до 8 мм по запросу.
        - Отверстие Ø5 перенесено в вершину дуги и сделано вертикальным.
        - Толщина стенки и полки сохранена 4 мм по всей базовой геометрии.
        - Усиление перенесено только в правое сопряжение крюка с полкой в виде плавного касательного плеча.
        - На хвосте сохранены мягкие окончания с 2x R10, чтобы снизить концентрацию напряжений и убрать острые кромки.

        ## Основные размеры и параметры

        | Параметр | Значение | Комментарий |
        | :--- | :--- | :--- |
        | Габаритная длина | 110 мм | От края губки до хвоста |
        | Габаритная ширина | 30 мм | Постоянная ширина экструзии |
        | Габаритная высота | 16 мм | От нижней базы до вершины внешней дуги |
        | Толщина стенки и полки | 4 мм | Сохранена по запросу |
        | Внутренний радиус крюка | 8 мм | Посадка под охватываемый элемент Ø16 мм |
        | Внешний радиус крюка | 12 мм | Обеспечивает стенку 4 мм |
        | Толщина короны | 4 мм | Между внутренней и внешней дугой |
        | Толщина левой губки | 4 мм | Совпадает с разностью радиусов |
        | Локальное усиление сопряжения | Плечо 10 мм | Плавный касательный переход без отдельного бугра |
        | Отверстие | Ø5 мм | Вертикальное |
        | Положение отверстия | В вершине дуги | Центр: X = 12 мм, Z = 15 мм |
        | Скругления хвоста | 2x R10 | В плане, на правом торце |

        ## Анализ нагрузки и почему усиление нужно именно здесь

        Деталь воспринимает комбинированную нагрузку как короткая консоль:

        - Статическая нагрузка от одного торца шторки обычно лежит в диапазоне примерно {STATIC_LOAD_MIN:.0f}...{STATIC_LOAD_MAX:.0f} Н.
        - В движении автомобиля, при хлопке двери багажника и при установке шторки разумно закладывать кратковременные пики до {DYNAMIC_LOAD_MAX:.0f} Н.
        - При неаккуратной установке возможен локальный удар порядка {IMPACT_LOAD_MAX:.0f} Н по нижней губке и внутренней дуге.

        Критические зоны для такой геометрии:

        - вершина дуги вокруг вертикального отверстия;
        - переход дуги в прямую полку справа;
        - корень нижней губки слева.

        Что сделано для усиления:

        - Базовая стенка оставлена 4 мм, поэтому посадочная геометрия осталась компактной.
        - Усиление перенесено только в правый корень сопряжения: плавное касательное плечо распределяет напряжение без отдельного локального бугра.
        - Вертикальное отверстие поставлено в вершину дуги и по центру ширины, поэтому нагрузка вводится симметрично и не ослабляет боковую стенку сильнее нужного.
        - Скругления 2x R10 на хвосте уменьшают риск появления трещины от случайного надлома на конце детали.

        ## Допущение, которое обязательно проверить

        Новая геометрия с внутренним радиусом 8 мм рассчитана под опираемый элемент диаметром около 16 мм.
        Если фактическая штанга или палец шторки ближе к прежней версии Ø32 мм, эта редакция не подойдет без повторной корректировки радиуса.

        ## Рекомендации по 3D-печати

        - Материал: PETG, ASA или ABS. PLA не рекомендуется для салона автомобиля.
        - Ориентация: печать на боковой плоской грани, чтобы слои шли вдоль дуги крюка и усиленного сопряжения.
        - Высота слоя: 0.20 мм.
        - Периметры: не менее 5.
        - Верх/низ: не менее 6 сплошных слоев.
        - Заполнение: 45-60%, лучше gyroid или cubic.
        - Для максимальной живучести желательно включить модификатор с 100% заполнением в зоне вершины и правого сопряжения.

        ## Выпускные файлы

        - STL: [Крепление_шторки.stl](Крепление_шторки.stl)
        - STEP: [Крепление_шторки.step](Крепление_шторки.step)
        - FreeCAD: [Крепление_шторки.FCStd](Крепление_шторки.FCStd)
        - Чертеж: [Чертеж_крепления.svg](Чертеж_крепления.svg)
        - Генератор: [build_cargo_cover_bracket.py](build_cargo_cover_bracket.py)

        ## Контрольная сводка по твердому телу

        - Валидность тела: {shape.isValid()}
        - Объем: {shape.Volume:.1f} мм^3 ({volume_cm3:.2f} см^3)
        - Габаритный контейнер: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} мм
        - Оценочная масса: PETG ≈ {mass_petg:.1f} г, ASA ≈ {mass_asa:.1f} г
        """
    ).strip() + "\n"

    with open(MD_PATH, "w", encoding="utf-8") as md_file:
        md_file.write(content)


def export_files(shape):
    if DOC_NAME in App.listDocuments().keys():
        App.closeDocument(DOC_NAME)

    doc = App.newDocument(DOC_NAME)
    obj = doc.addObject("Part::Feature", OBJECT_NAME)
    obj.Label = "Крепление шторки"
    obj.Shape = shape
    doc.recompute()

    doc.saveAs(FCSTD_PATH)
    shape.exportStep(STEP_PATH)

    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=0.05,
        AngularDeflection=0.25,
        Relative=False,
    )
    mesh.write(STL_PATH)
    return doc


def main():
    shape = build_solid()
    if not shape.isValid():
        App.Console.PrintWarning("Тело невалидно, пробую исправить...\n")
        shape.fix(1e-6, 1e-6, 1e-6)

    if not shape.isValid():
        raise RuntimeError("Построенное тело осталось невалидным")

    export_files(shape)
    render_svg()
    write_markdown(shape)

    bb = shape.BoundBox
    App.Console.PrintMessage(
        "Готово: valid=%s | solids=%d | volume=%.1f mm^3 | bbox=%.1f x %.1f x %.1f mm\n"
        % (shape.isValid(), len(shape.Solids), shape.Volume, bb.XLength, bb.YLength, bb.ZLength)
    )
    App.Console.PrintMessage("Экспортированы STL, STEP, FCStd, SVG и Markdown.\n")


if __name__ == "__main__":
    main()