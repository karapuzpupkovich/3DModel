import os
import sys
import importlib.util

PROJECT_DIR = os.path.join(os.path.dirname(__file__), "Шкафчик Никиты (Сказка м.г.)")
RENDER_MODULE_PATH = os.path.join(PROJECT_DIR, "honeycomb_cell", "render_stl_views.py")

spec = importlib.util.spec_from_file_location("render_stl_views_module", RENDER_MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
render_stl_views = module.render_stl_views

stl_path = os.path.join(PROJECT_DIR, "honeycomb_cell", "output", "HoneycombCell.stl")
output_path = os.path.join(PROJECT_DIR, "honeycomb_cell", "output", "HoneycombCell_views.png")
render_stl_views(stl_path, output_path)
print(output_path)
