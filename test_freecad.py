import subprocess
import json
import time
import sys

def main():
    bridge_path = r"C:\Users\Администратор\.freecad-mcp\working_bridge.py"
    
    # Start the bridge server process
    print(f"Starting bridge server: {bridge_path}")
    process = subprocess.Popen(
        [sys.executable, bridge_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    def send_request(request):
        raw = json.dumps(request)
        print(f"\n---> Sending: {raw}")
        process.stdin.write(raw + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(f"<--- Received: {response.strip()}")
        return response

    try:
        # Step 1: Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        send_request(init_req)
        
        # Step 2: Initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        raw = json.dumps(initialized_notification)
        print(f"\n---> Sending: {raw}")
        process.stdin.write(raw + "\n")
        process.stdin.flush()
        time.sleep(0.5)

        # Step 3: Check FreeCAD Connection tool
        check_conn_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "check_freecad_connection",
                "arguments": {}
            }
        }
        send_request(check_conn_req)

        # Step 4: Create a 50x80x10mm box
        create_box_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "part_operations",
                "arguments": {
                    "operation": "box",
                    "length": 50,
                    "width": 80,
                    "height": 10
                }
            }
        }
        send_request(create_box_req)

        # Step 5: Verify the box properties using execute_python
        verify_req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "execute_python",
                "arguments": {
                    "code": "obj = doc.getObject('Box')\nresult = f'{obj.Label}: {obj.Length.Value}x{obj.Width.Value}x{obj.Height.Value}mm'"
                }
            }
        }
        send_request(verify_req)

    except Exception as e:
        print(f"Error during communication: {e}")
    finally:
        # Terminate
        print("\nTerminating process...")
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Stderr output:\n{stderr_output}")

if __name__ == "__main__":
    main()
