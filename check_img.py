# -*- coding: utf-8 -*-
from PIL import Image
import os

paths = [
    r"C:\Users\Administrator\Desktop\学练考\_shitu_images\image5.png",
    r"C:\Users\Administrator\Desktop\学练考\image5.png",
    r"C:\Users\Administrator\Desktop\学练考\static\images\geo_maps\image5.png",
]
for p in paths:
    if os.path.exists(p):
        img = Image.open(p)
        print(f"Found: {p}")
        print(f"  Size: {img.size}")
        print(f"  Mode: {img.mode}")
        break
else:
    print("Not found in expected paths")
    # list what exists
    base = r"C:\Users\Administrator\Desktop\学练考"
    for root, dirs, files in os.walk(base):
        if "image5" in str(files):
            print(f"In {root}: {files}")
