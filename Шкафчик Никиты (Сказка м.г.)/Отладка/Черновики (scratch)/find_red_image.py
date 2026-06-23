import os
import glob
from PIL import Image

artifact_dir = r"C:\Users\Администратор\.gemini\antigravity-ide\brain\4b624e90-80b6-4c2d-8846-392b91f1ad98"
files = glob.glob(os.path.join(artifact_dir, "media__*.*")) + glob.glob(os.path.join(artifact_dir, ".tempmediaStorage", "media_*.*"))

print("Searching for images with red annotations...")
for f in files:
    try:
        img = Image.open(f).convert("RGB")
        # Sample pixels to find red (R > 200, G < 50, B < 50)
        width, height = img.size
        # Resize to speed up check
        img_small = img.resize((100, 100))
        has_red = False
        for x in range(100):
            for y in range(100):
                r, g, b = img_small.getpixel((x, y))
                if r > 180 and g < 60 and b < 60:
                    has_red = True
                    break
            if has_red:
                break
        if has_red:
            print(f"FOUND RED in: {os.path.basename(f)}")
    except Exception as e:
        print(f"Error checking {f}: {e}")
