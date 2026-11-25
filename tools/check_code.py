#!/usr/bin/env python3
"""Checks every script before a build. Fails (exit 1) on:
  * syntax errors
  * unknown globals (usually a typo or a variable a module forgot to import)
  * any failing test in tests/

Run:  python3 tools/check_code.py   (build_place.py runs it automatically)
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "tools" / "bin"

# Globals Roblox provides that plain Luau doesn't know about
ROBLOX_GLOBALS = set(
    """game workspace script plugin shared Instance Vector3 Vector2 Vector3int16 Vector2int16
    CFrame Color3 UDim UDim2 Enum Random task typeof RaycastParams OverlapParams TweenInfo
    NumberSequence NumberSequenceKeypoint ColorSequence ColorSequenceKeypoint NumberRange Rect
    Ray BrickColor PhysicalProperties Font DateTime Region3 Axes Faces warn tick time delay
    spawn wait settings elapsedTime Content Path2DControlPoint utf8""".split()
)

UNKNOWN = re.compile(r"Unknown global '([^']+)'")


def analyze():
    problems = []
    for path in sorted((ROOT / "src").rglob("*.lua")):
        out = subprocess.run(
            [str(BIN / "luau-analyze"), str(path)], capture_output=True, text=True
        ).stdout
        for line in out.splitlines():
            m = UNKNOWN.search(line)
            if m and m.group(1) in ROBLOX_GLOBALS:
                continue
            if m or "SyntaxError" in line:
                problems.append(line.replace(str(ROOT) + "/", ""))
    return problems


def run_tests():
    ok = True
    for test in sorted((ROOT / "tests").glob("*.luau")):
        result = subprocess.run(
            [str(BIN / "luau"), str(test.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True,
        )
        print((result.stdout + result.stderr).strip())
        ok = ok and result.returncode == 0
    return ok


def main():
    problems = analyze()
    for p in problems:
        print(p)
    tests_ok = run_tests()
    if problems or not tests_ok:
        print("CHECK FAILED: fix the problems above before shipping")
        return 1
    print("Code check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
