import math
import os
import sys

# Ensure parent directory is in path for relative imports
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from PIL import Image, ImageDraw, ImageFont
from Стандартная_ячейка.render_stl_views import load_stl, project_triangle, rotate_point, _triangle_normal


def draw_arrow(draw, p1, p2, color=(180, 40, 40), width=1.5, size=6):
    draw.line([p1, p2], fill=color, width=int(width))
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy) or 1e-6
    ux = dx / length
    uy = dy / length
    vx = -uy
    vy = ux
    
    ah1_1 = (p1[0] + ux * size + vx * (size * 0.4), p1[1] + uy * size + vy * (size * 0.4))
    ah1_2 = (p1[0] + ux * size - vx * (size * 0.4), p1[1] + uy * size - vy * (size * 0.4))
    draw.line([p1, ah1_1], fill=color, width=int(width))
    draw.line([p1, ah1_2], fill=color, width=int(width))
    
    ah2_1 = (p2[0] - ux * size + vx * (size * 0.4), p2[1] - uy * size + vy * (size * 0.4))
    ah2_2 = (p2[0] - ux * size - vx * (size * 0.4), p2[1] - uy * size - vy * (size * 0.4))
    draw.line([p2, ah2_1], fill=color, width=int(width))
    draw.line([p2, ah2_2], fill=color, width=int(width))


def render_view_params(draw, triangles, box, title, *, rot_z_deg=0.0, rot_x_deg=0.0, rot_y_deg=0.0):
    x0, y0, x1, y1 = box
    width = x1 - x0
    height = y1 - y0
    transformed = [project_triangle(triangle, rot_z_deg=rot_z_deg, rot_x_deg=rot_x_deg, rot_y_deg=rot_y_deg) for triangle in triangles]

    min_x = min(point[0] for rotated, _ in transformed for point in rotated)
    max_x = max(point[0] for rotated, _ in transformed for point in rotated)
    min_y = min(point[1] for rotated, _ in transformed for point in rotated)
    max_y = max(point[1] for rotated, _ in transformed for point in rotated)

    scale = min((width - 150) / max(max_x - min_x, 1e-6), (height - 150) / max(max_y - min_y, 1e-6))
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    screen_cx = x0 + width / 2.0
    screen_cy = y0 + height / 2.0 + 10

    font = ImageFont.load_default()
    draw.rectangle(box, fill=(250, 250, 250), outline=(210, 210, 210), width=1)
    draw.text((x0 + 15, y0 + 15), title, fill=(20, 20, 20), font=font)

    for rotated, depth in sorted(transformed, key=lambda item: item[1]):
        normal = _triangle_normal(rotated)
        normal_length = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) or 1.0
        light = abs(normal[2]) / normal_length
        shade = int(140 + 85 * light)
        points_2d = []
        for px, py, _ in rotated:
            sx = screen_cx + (px - center_x) * scale
            sy = screen_cy - (py - center_y) * scale
            points_2d.append((sx, sy))
        draw.polygon(points_2d, fill=(shade, shade, shade), outline=(90, 90, 90))
        
    return scale, center_x, center_y, screen_cx, screen_cy


def to_screen(pt_3d, view_rot_deg, scale, cx, cy, scx, scy):
    rot = rotate_point(pt_3d, rot_x_deg=view_rot_deg[0], rot_y_deg=view_rot_deg[1], rot_z_deg=view_rot_deg[2])
    sx = scx + (rot[0] - cx) * scale
    sy = scy - (rot[1] - cy) * scale
    return (sx, sy)


def render_cell_drawings(stl_path: str, output_path: str) -> None:
    triangles = load_stl(stl_path)
    image = Image.new("RGB", (1800, 1400), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    box_front = (940, 40, 1760, 680)
    rot_x_front = 90.0
    rot_y_front = 0.0
    rot_z_front = 0.0
    
    box_side = (40, 720, 860, 1360)
    rot_x_side = 90.0
    rot_y_side = 90.0
    rot_z_side = 0.0

    print("Rendering Isometric view (Cell)...")
    render_view_params(draw, triangles, (40, 40, 860, 680), "Isometric View", rot_z_deg=45.0, rot_x_deg=35.264)
    
    print("Rendering Front view (Cell)...")
    sc_f, cx_f, cy_f, scx_f, scy_f = render_view_params(draw, triangles, box_front, "Front View (XY Projection)", rot_x_deg=rot_x_front)
    
    print("Rendering Side view (Cell)...")
    sc_s, cx_s, cy_s, scx_s, scy_s = render_view_params(draw, triangles, box_side, "Side View (ZY Projection)", rot_y_deg=rot_y_side, rot_x_deg=rot_x_side)
    
    print("Rendering Top view (Cell)...")
    render_view_params(draw, triangles, (940, 720, 1760, 1360), "Top View (ZX Projection)", rot_z_deg=0.0, rot_x_deg=0.0)

    p_left_out = (-72.0, 0.0, 100.0)
    p_right_out = (72.0, 0.0, 100.0)
    p_top_out = (0.0, 48.5, 100.0)
    p_bottom_out = (0.0, -48.5, 100.0)
    p_top_in = (0.0, 46.2, 100.0)
    
    sf_left = to_screen(p_left_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_right = to_screen(p_right_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_top = to_screen(p_top_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_bottom = to_screen(p_bottom_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_top_in = to_screen(p_top_in, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)

    font = ImageFont.load_default()
    dim_color = (180, 40, 40)
    line_color = (100, 100, 100)

    # Width Dimension (144.0 mm)
    y_off_w = sf_bottom[1] + 60
    draw.line([(sf_left[0], sf_left[1]), (sf_left[0], y_off_w + 10)], fill=line_color, width=1)
    draw.line([(sf_right[0], sf_right[1]), (sf_right[0], y_off_w + 10)], fill=line_color, width=1)
    draw_arrow(draw, (sf_left[0], y_off_w), (sf_right[0], y_off_w), dim_color)
    draw.text(((sf_left[0] + sf_right[0]) / 2 - 25, y_off_w - 18), "144.0 mm", fill=dim_color, font=font)

    # Height Dimension (97.0 mm)
    x_off_h = sf_left[0] - 60
    draw.line([(sf_left[0], sf_bottom[1]), (x_off_h - 10, sf_bottom[1])], fill=line_color, width=1)
    draw.line([(sf_left[0], sf_top[1]), (x_off_h - 10, sf_top[1])], fill=line_color, width=1)
    draw_arrow(draw, (x_off_h, sf_bottom[1]), (x_off_h, sf_top[1]), dim_color)
    draw.text((x_off_h - 55, (sf_bottom[1] + sf_top[1]) / 2 - 8), "97.0 mm", fill=dim_color, font=font)

    # Wall Thickness (2.3 mm)
    x_off_t = sf_right[0] + 40
    draw.line([(sf_right[0], sf_top[1]), (x_off_t, sf_top[1])], fill=line_color, width=1)
    draw.line([(sf_right[0], sf_top_in[1]), (x_off_t, sf_top_in[1])], fill=line_color, width=1)
    draw_arrow(draw, (x_off_t - 15, sf_top[1]), (x_off_t - 15, sf_top_in[1]), dim_color, size=3)
    draw.text((x_off_t, (sf_top[1] + sf_top_in[1]) / 2 - 8), "t = 2.3 mm", fill=dim_color, font=font)

    # Length (200.0 mm)
    p_len_start = (0.0, 48.5, 0.0)
    p_len_end = (0.0, 48.5, 200.0)
    ss_start = to_screen(p_len_start, (rot_x_side, rot_y_side, rot_z_side), sc_s, cx_s, cy_s, scx_s, scy_s)
    ss_end = to_screen(p_len_end, (rot_x_side, rot_y_side, rot_z_side), sc_s, cx_s, cy_s, scx_s, scy_s)
    
    y_off_len = ss_start[1] + 60
    draw.line([(ss_start[0], ss_start[1]), (ss_start[0], y_off_len + 10)], fill=line_color, width=1)
    draw.line([(ss_end[0], ss_end[1]), (ss_end[0], y_off_len + 10)], fill=line_color, width=1)
    draw_arrow(draw, (ss_start[0], y_off_len), (ss_end[0], y_off_len), dim_color)
    draw.text(((ss_start[0] + ss_end[0]) / 2 - 25, y_off_len - 18), "200.0 mm", fill=dim_color, font=font)

    image.save(output_path)
    print(f"Cell views saved to: {output_path}")


def render_plate_drawings(stl_path: str, output_path: str) -> None:
    triangles = load_stl(stl_path)
    image = Image.new("RGB", (1800, 1000), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    box_front = (940, 40, 1760, 480)
    rot_x_front = 90.0
    rot_y_front = 0.0
    rot_z_front = 0.0
    
    box_side = (40, 520, 860, 960)
    rot_x_side = 90.0
    rot_y_side = 90.0
    rot_z_side = 0.0

    print("Rendering Isometric view (Plate)...")
    render_view_params(draw, triangles, (40, 40, 860, 480), "Isometric View", rot_z_deg=45.0, rot_x_deg=35.264)
    
    print("Rendering Front view (Plate)...")
    sc_f, cx_f, cy_f, scx_f, scy_f = render_view_params(draw, triangles, box_front, "Front View (XY Projection)", rot_x_deg=rot_x_front)
    
    print("Rendering Side view (Plate)...")
    sc_s, cx_s, cy_s, scx_s, scy_s = render_view_params(draw, triangles, box_side, "Side View (ZY Projection)", rot_y_deg=rot_y_side, rot_x_deg=rot_x_side)
    
    print("Rendering Top view (Plate)...")
    render_view_params(draw, triangles, (940, 520, 1760, 960), "Top View (ZX Projection)", rot_z_deg=0.0, rot_x_deg=0.0)

    p_left_out = (-144.0, 0.0, 100.0)
    p_right_out = (144.0, 0.0, 100.0)
    p_top_out = (0.0, 0.0, 100.0)
    p_bottom_out = (0.0, -4.8, 100.0)
    
    sf_left = to_screen(p_left_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_right = to_screen(p_right_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_top = to_screen(p_top_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)
    sf_bottom = to_screen(p_bottom_out, (rot_x_front, rot_y_front, rot_z_front), sc_f, cx_f, cy_f, scx_f, scy_f)

    font = ImageFont.load_default()
    dim_color = (180, 40, 40)
    line_color = (100, 100, 100)

    # Width Dimension (288.0 mm)
    y_off_w = sf_bottom[1] + 60
    draw.line([(sf_left[0], sf_left[1]), (sf_left[0], y_off_w + 10)], fill=line_color, width=1)
    draw.line([(sf_right[0], sf_right[1]), (sf_right[0], y_off_w + 10)], fill=line_color, width=1)
    draw_arrow(draw, (sf_left[0], y_off_w), (sf_right[0], y_off_w), dim_color)
    draw.text(((sf_left[0] + sf_right[0]) / 2 - 25, y_off_w - 18), "288.0 mm", fill=dim_color, font=font)

    # Height Dimension (4.8 mm)
    x_off_h = sf_left[0] - 60
    draw.line([(sf_left[0], sf_bottom[1]), (x_off_h - 10, sf_bottom[1])], fill=line_color, width=1)
    draw.line([(sf_left[0], sf_top[1]), (x_off_h - 10, sf_top[1])], fill=line_color, width=1)
    draw_arrow(draw, (x_off_h, sf_bottom[1]), (x_off_h, sf_top[1]), dim_color, size=3)
    draw.text((x_off_h - 55, (sf_bottom[1] + sf_top[1]) / 2 - 8), "4.8 mm", fill=dim_color, font=font)

    # Length (200.0 mm)
    p_len_start = (0.0, 0.0, 0.0)
    p_len_end = (0.0, 0.0, 200.0)
    ss_start = to_screen(p_len_start, (rot_x_side, rot_y_side, rot_z_side), sc_s, cx_s, cy_s, scx_s, scy_s)
    ss_end = to_screen(p_len_end, (rot_x_side, rot_y_side, rot_z_side), sc_s, cx_s, cy_s, scx_s, scy_s)
    
    y_off_len = ss_start[1] + 60
    draw.line([(ss_start[0], ss_start[1]), (ss_start[0], y_off_len + 10)], fill=line_color, width=1)
    draw.line([(ss_end[0], ss_end[1]), (ss_end[0], y_off_len + 10)], fill=line_color, width=1)
    draw_arrow(draw, (ss_start[0], y_off_len), (ss_end[0], y_off_len), dim_color)
    draw.text(((ss_start[0] + ss_end[0]) / 2 - 25, y_off_len - 18), "200.0 mm", fill=dim_color, font=font)

    image.save(output_path)
    print(f"Plate views saved to: {output_path}")


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    
    cell_stl = os.path.join(output_dir, "HoneycombCell_large.stl")
    cell_img = os.path.join(output_dir, "HoneycombCell_large_dimensioned.png")
    render_cell_drawings(cell_stl, cell_img)
    
    plate_stl = os.path.join(output_dir, "BottomPlate.stl")
    plate_img = os.path.join(output_dir, "BottomPlate_dimensioned.png")
    render_plate_drawings(plate_stl, plate_img)


if __name__ == "__main__":
    main()
