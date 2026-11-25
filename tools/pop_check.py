#!/usr/bin/env python3
"""Play-test check for popping: rebuilds, reopens Studio, starts a play test,
walks the player near a wall, holds the mouse for a few seconds and reports
how many bubbles the server counted, plus any errors in Studio's Output.

    python3 tools/pop_check.py            full check (rebuild + reload)
    python3 tools/pop_check.py --no-reload  use the play test already running
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def studio(*args, timeout=60):
    r = subprocess.run(["python3", str(ROOT / "tools" / "studio.py"), *args],
                       capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip()


def client(code):
    return studio("luau", "--client", code).splitlines()[-1]


if "--no-reload" not in sys.argv:
    studio("start_stop_play", '{"is_start": false}')
    subprocess.run([str(ROOT / "tools" / "studio_reload.sh")], check=True)
    for _ in range(20):
        time.sleep(6)
        if '"Edit"' in studio("list_roblox_studios", "{}"):
            break
    time.sleep(3)
    print(studio("start_stop_play", '{"is_start": true}'))
    time.sleep(10)

print("camera:", client('return game.Players.LocalPlayer.CameraMode.Name'))
client('local S=game.ReplicatedStorage.Shared; local L=require(S.Rules.RoomLayout).new(require(S.Config.Room)); '
       'local r=game.Players.LocalPlayer.Character.HumanoidRootPart; r.CFrame=CFrame.new(0.3,3,-L.half+6); return "moved"')
time.sleep(1)
before = client('return game.Players.LocalPlayer.leaderstats.Pops.Value')
studio("user_mouse_input", '{"datamodel_type":"Client","actions":[{"action":"moveTo","x":400,"y":300},'
       '{"action":"mouseButtonDown","mouse_button":"left"},{"action":"wait","wait_time_ms":3000},'
       '{"action":"mouseButtonUp","mouse_button":"left"}]}')
time.sleep(1)
after = client('return game.Players.LocalPlayer.leaderstats.Pops.Value')
print(f"click pops in 3 s: {int(after) - int(before)} (expect about {int(3 / 0.56)})")
out = studio("get_console_output", "{}")
errors = [l for l in out.splitlines() if "error" in l.lower() or "exception" in l.lower()]
print("errors:", "\n".join(errors) if errors else "none")
