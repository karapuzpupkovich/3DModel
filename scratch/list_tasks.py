import os
brain_dir = 'C:/Users/Администратор/.gemini/antigravity-ide/brain/4b624e90-80b6-4c2d-8846-392b91f1ad98/.system_generated/tasks'
if os.path.exists(brain_dir):
    print("Files in tasks dir:")
    for f in sorted(os.listdir(brain_dir)):
        if "1829" in f:
            print("Found 1829 file:", f)
            print("Size:", os.path.getsize(os.path.join(brain_dir, f)))
else:
    print("Tasks dir not found!")
