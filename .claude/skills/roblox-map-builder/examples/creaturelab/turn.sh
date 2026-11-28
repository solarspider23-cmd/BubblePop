#!/bin/sh
# ./turn.sh outdir "expr" : 4-angle turntable + 2x2 sheet
out=$1; expr=$2
"${BLENDER:-blender}" -b --factory-startup --python turntable.py -- "$expr" "$out" 2>&1 | grep -E 'TURN|Error|Traceback|line [0-9]+'
"${PYTHON:-python}" -c "
import glob,sys
from PIL import Image
fs=sorted(glob.glob('$out/*_[0-3].png')); im=Image.new('RGB',(1400,1400))
for i,f in enumerate(fs[:4]): im.paste(Image.open(f).convert('RGB'),((i%2)*700,(i//2)*700))
im.save('$out/sheet.png')"
