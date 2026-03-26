#!/usr/bin/env python3
from PIL import Image
import sys

gif_path = sys.argv[1]
out_path = sys.argv[2]

img = Image.open(gif_path)
img.seek(0)  # first frame
img = img.convert('RGB')
img.save(out_path)
print(f"Saved first frame to {out_path}")
