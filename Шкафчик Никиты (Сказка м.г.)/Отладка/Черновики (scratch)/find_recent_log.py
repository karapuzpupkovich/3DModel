import os

brain_dir = 'C:/Users/Администратор/.gemini/antigravity-ide/brain/4b624e90-80b6-4c2d-8846-392b91f1ad98/.system_generated/tasks'
print("Searching in:", brain_dir)

if os.path.exists(brain_dir):
    for file in sorted(os.listdir(brain_dir)):
        if file.endswith('.log'):
            try:
                task_num = int(file.replace('task-', '').replace('.log', ''))
                if task_num >= 1700:
                    path = os.path.join(brain_dir, file)
                    print(f"\n--- {file} ({path}) ---")
                    print(open(path, encoding='utf-8', errors='ignore').read())
                    print("------------------------")
            except ValueError:
                pass
else:
    print("Tasks directory not found!")
