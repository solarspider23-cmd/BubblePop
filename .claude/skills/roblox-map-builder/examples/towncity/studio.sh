#!/bin/sh
# close-up QA: ./studio.sh <outdir> "expr" ...
SK="$(cd "$(dirname "$0")/../.." && pwd)"   # skill root
out=$1; shift
"${BLENDER:-blender}" -b --factory-startup --python "$SK/scripts/prop_studio.py" -- --module ${MOD:-town_kit} --out "$out" --res 800 "$@" 2>&1 | grep -E 'STUDIO|Error|Traceback|line [0-9]+|CONTACT|rror'
"${PYTHON:-python}" "$SK/scripts/contact_sheet.py" "$out" "$out/sheet.png" >/dev/null
