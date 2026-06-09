import socket
import json
import sys

def run_file_in_freecad(file_path):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('localhost', 23456))
        # Use simple code that fits in a single TCP packet (< 4096 bytes)
        code_str = f"import sys; exec(open({repr(file_path)}, encoding='utf-8').read())"
        payload = {
            "tool": "execute_python",
            "args": {
                "code": code_str
            }
        }
        s.sendall(json.dumps(payload).encode('utf-8'))
        response = s.recv(8192).decode('utf-8')
        res_json = json.loads(response)
        if res_json.get("success"):
            print("FreeCAD Output:", res_json.get("result"))
        else:
            print("FreeCAD Error:", res_json.get("error"))
    except Exception as e:
        print("Error connecting/executing:", e)
    finally:
        s.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_in_freecad.py <file_path>")
        sys.exit(1)
    run_file_in_freecad(sys.argv[1])
