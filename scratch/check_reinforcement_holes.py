import sys, os
PROJECT_DIR = r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import FreeCAD
import Part
import math
from honeycomb_cell.builder import create_honeycomb_cell_shape
from honeycomb_cell.config import DEFAULT_CONFIG

shape, report = create_honeycomb_cell_shape(DEFAULT_CONFIG, enable_perforation=True, log=print)

# Let's count how many cutters are generated for faces 2 and 3, and their U coordinates
from honeycomb_cell.builder import _build_perforation_cutters, _build_outer_vertices
vertices_out = _build_outer_vertices(DEFAULT_CONFIG)
cutters_by_face, report = _build_perforation_cutters(vertices_out, DEFAULT_CONFIG, print)

for face_index in (2, 3):
    cutters = cutters_by_face[face_index]
    print(f"\nFace {face_index} total cutters: {len(cutters)}")
    inside_reinf = 0
    outside_reinf = 0
    u_values = []
    
    # We can reconstruct the U values by looking at the generation logic
    # In builder.py:
    # groove_min_abs_u = max(config.perforation_groove_clearance, config.female_w_tip/2.0 + joint_center_margin)
    # reinforcement width is config.reinforcement_w1 = 52.0 (half width 26.0)
    # max_u is about 33.7
    cfg = DEFAULT_CONFIG
    max_u = (vertices_out[face_index] - vertices_out[(face_index + 1) % 6]).Length / 2.0
    max_u_limit = max_u - cfg.perforation_edge_min
    
    ridge_half_width = cfg.male_w1 / 2.0
    perforation_half_span = cfg.perforation_radius + cfg.perforation_chamfer
    joint_center_margin = cfg.perforation_joint_edge_min + perforation_half_span
    groove_min_abs_u = max(cfg.perforation_groove_clearance, cfg.female_w_tip / 2.0 + joint_center_margin)
    
    for row in range(cfg.perforation_rows):
        from honeycomb_cell.builder import _build_u_positions
        u_positions = _build_u_positions(max_u_limit, row, cfg.perforation_spacing_u)
        seen = set()
        for u in u_positions:
            if abs(u) > max_u_limit:
                continue
            rounded_u = round(u, 4)
            if rounded_u in seen:
                continue
            seen.add(rounded_u)
            if abs(u) < groove_min_abs_u:
                continue
            u_values.append(u)
            if abs(u) <= cfg.reinforcement_w1 / 2.0:
                inside_reinf += 1
            else:
                outside_reinf += 1
                
    print(f"  Inside reinforcement pad (|u| <= {cfg.reinforcement_w1/2.0}): {inside_reinf}")
    print(f"  Outside reinforcement pad (|u| > {cfg.reinforcement_w1/2.0}): {outside_reinf}")
    print(f"  U coordinates: {sorted(list(set(u_values)))}")
