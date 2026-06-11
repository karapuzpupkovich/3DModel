import json
import os
import socket
import sys


PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
BUILD_SCRIPT = os.path.join(PROJECT_DIR, "build_cabinet.py")


def run_freecad_code(code_str: str):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("localhost", 23456))
        payload = {"tool": "execute_python", "args": {"code": code_str}}
        client.sendall(json.dumps(payload).encode("utf-8"))
        response = client.recv(8192).decode("utf-8")
        return json.loads(response)
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        client.close()


def main() -> None:
    print("Подключение к FreeCAD и запуск построения 3D-модели...")
    freecad_code = f"import runpy, sys; sys.path.insert(0, r'{PROJECT_DIR}'); runpy.run_path(r'{BUILD_SCRIPT}', run_name='__main__')"
    response = run_freecad_code(freecad_code)
    if response.get("success"):
        print("\nУспех!")
        print(response.get("result"))
    else:
        print("\nОшибка при отправке или выполнении скрипта в FreeCAD:")
        print(response.get("error"))
        print("Пожалуйста, убедитесь, что FreeCAD запущен и активна панель AI Copilot.")
        sys.exit(1)


if __name__ == "__main__":
    main()
