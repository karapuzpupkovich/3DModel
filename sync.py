import os
import re

with open(r'c:\3DModel\build_cabinet.py', 'r', encoding='utf-8') as f:
    build_code = f.read()

# Extract the relevant part (skip top imports)
match = re.search(r'doc = FreeCAD\.newDocument\(.*', build_code, re.DOTALL)
core_code = match.group(0) if match else build_code

wrapper = '''import socket
import json
import os

def run_freecad_code(code_str):
    """Sends python code to FreeCAD socket server and returns the result."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('localhost', 23456))
        payload = {
            "tool": "execute_python",
            "args": {
                "code": code_str
            }
        }
        s.sendall(json.dumps(payload).encode('utf-8'))
        response = s.recv(8192).decode('utf-8')
        return json.loads(response)
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        s.close()

def main():
    print("Подключение к FreeCAD и запуск построения 3D-модели...")
    
    # Python code to execute within FreeCAD
    freecad_code = """import FreeCAD
import Part
import os
import math

''' + core_code + '''

result = {
    "success": True,
    "result": f"Модель шкафчика успешно перестроена и сохранена в {save_path}"
}
import json
result = json.dumps(result)
"""
    response = run_freecad_code(freecad_code)
    
    if response.get("success"):
        print("\\nУспех!")
        print(response.get("result"))
    else:
        print("\\nОшибка при отправке или выполнении скрипта в FreeCAD:")
        print(response.get("error"))
        print("Пожалуйста, убедитесь, что FreeCAD запущен и активна панель AI Copilot.")

if __name__ == "__main__":
    main()
'''

with open(r'c:\3DModel\Шкафчик Никиты (Сказка м.г.)\create_cabinet_model.py', 'w', encoding='utf-8') as f:
    f.write(wrapper)
