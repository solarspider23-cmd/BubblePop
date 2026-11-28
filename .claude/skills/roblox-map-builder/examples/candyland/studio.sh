#!/bin/bash
# close-up QA renders: ./studio.sh "prop()" ...  -> studio/<Prop>_front|back.png + studio/sheet.png
cd "$(dirname "$0")"
B="${BLENDER:-blender}"; SK="$(cd ../.. && pwd)"   # skill root
"$B" -b --factory-startup --python "$SK/scripts/prop_studio.py" -- --module candy_studio --out studio --res 700 "$@" 2>&1 | grep -E "STUDIO|Error|Traceback|line [0-9]+"
