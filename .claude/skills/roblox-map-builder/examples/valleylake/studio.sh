#!/bin/sh
# close-up QA: ./studio.sh <outdir> "expr" ...
SK="$(cd "$(dirname "$0")/../.." && pwd)"   # skill root
out=$1; shift
"${BLENDER:-blender}" -b --factory-startup --python "$SK/scripts/prop_studio.py" -- --module valley_props --out "$out" --res 800 "$@" 2>&1 | grep -E 'STUDIO|Error|Traceback|line [0-9]+|CONTACT|rror'
