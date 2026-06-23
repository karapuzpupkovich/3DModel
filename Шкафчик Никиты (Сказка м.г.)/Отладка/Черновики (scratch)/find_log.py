import os

brain_dir = 'C:/Users/Администратор/.gemini/antigravity-ide/brain/4b624e90-80b6-4c2d-8846-392b91f1ad98'
print("Searching in:", brain_dir)

if os.path.exists(brain_dir):
    for root, dirs, files in os.walk(brain_dir):
        for file in files:
            if file.endswith('.log'):
                path = os.path.join(root, file)
                print("Found log:", path)
                print("--- Content ---")
                try:
                    print(open(path, encoding='utf-8', errors='ignore').read()[:500])
                except Exception as e:
                    print("Error reading:", e)
                print("---------------")
else:
    print("Brain directory not found!")
