import os
path = 'C:/Users/Администратор/.gemini/antigravity-ide/brain/4b624e90-80b6-4c2d-8846-392b91f1ad98/.system_generated/tasks/task-1778.log'
if os.path.exists(path):
    print(open(path, encoding='utf-8').read())
else:
    print("Log file not found!")
