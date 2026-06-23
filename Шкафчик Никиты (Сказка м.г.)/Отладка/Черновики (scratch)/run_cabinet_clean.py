import os
import sys

PROJECT_DIR = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from honeycomb_cell.cabinet_builder import main as _cabinet_main

try:
    _cabinet_main()
    print("Cabinet built successfully and exited cleanly.")
    sys.stdout.flush()
    sys.exit(0)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
