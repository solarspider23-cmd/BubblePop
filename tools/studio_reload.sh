#!/bin/sh
# Build the place and load it into Roblox Studio WITHOUT leaving old Studio
# windows open. Each `open BubblePop.rbxlx` starts a whole new Studio (about
# 1 GB of memory each), so the old ones are closed first.
# usage: tools/studio_reload.sh          build, close Studio, open the new build
#        tools/studio_reload.sh --play   ...and start a play test
cd "$(dirname "$0")/.." || exit 1
python3 tools/build_place.py || exit 1
pkill -f "RobloxStudio.app/Contents/MacOS/RobloxStudio" 2>/dev/null
i=0
while pgrep -f "RobloxStudio.app/Contents/MacOS/RobloxStudio" >/dev/null && [ $i -lt 20 ]; do
  sleep 1; i=$((i + 1))
done
pkill -9 -f "RobloxStudio.app/Contents/MacOS/RobloxStudio" 2>/dev/null
sleep 3 # macOS refuses to open the app while it is still shutting down
open BubblePop.rbxlx || { sleep 5; open BubblePop.rbxlx; }
if [ "$1" = "--play" ]; then
  sleep 25
  python3 tools/studio.py start_stop_play '{"is_start": true}'
fi
