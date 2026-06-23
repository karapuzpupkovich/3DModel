import traceback
import sys
import os
try:
    sys.path.insert(0, os.path.abspath('Шкафчик Никиты (Сказка м.г.)'))
    import Увеличенная_ячейка.build_cell_and_plate as b
    b.main()
except Exception as e:
    traceback.print_exc()
