#!/bin/sh
# close-up QA renders: ./studio.sh "forklift(1, 'wrapped')" ...  -> studio/<Prop>_front|back.png
cd "$(dirname "$0")"; SK="$(cd ../.. && pwd)"
"${BLENDER:-blender}" -b --factory-startup --python "$SK/scripts/prop_studio.py" -- --module wh_props --out studio --res 700 "$@" 2>&1 | grep -E "STUDIO|Error|Traceback|line [0-9]+"
