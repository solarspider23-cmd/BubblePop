#!/usr/bin/env python3
"""Talk to the open Roblox Studio through its built-in MCP server.

Studio must be open with "Enable Studio as MCP server" switched on
(click "MCP off" in the bottom-right corner of Studio).

    python3 tools/studio.py                    list the tools Studio offers
    python3 tools/studio.py luau 'return 1+1'  run Luau in Studio, print the result
    python3 tools/studio.py luau -f file.luau  the same, from a file
    python3 tools/studio.py luau --server '...' run it in the running play test
                                               (--client for the player's side)
    python3 tools/studio.py schema <tool>      show what a tool needs
    python3 tools/studio.py <tool> '<json>'    call any tool, e.g.
        python3 tools/studio.py get_console_output '{}'
        python3 tools/studio.py start_stop_play '{"mode":"start_play"}'

Use this for LOOKING and CHECKING (clipping, errors, screenshots). The game's
code still lives in src/ and is built with tools/build_place.py; anything
changed inside Studio is lost on the next build.
"""

import base64
import json
import os
import select
import subprocess
import sys
import tempfile
import time

BINARY = "/Applications/RobloxStudio.app/Contents/MacOS/StudioMCP"
TIMEOUT = 120


class Studio:
    def __init__(self):
        self.proc = subprocess.Popen(
            [BINARY], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True,
        )
        self.next_id = 0
        self.request("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "stealafish-tools", "version": "1"},
        })
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, message):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params=None):
        self.next_id += 1
        message = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params is not None:
            message["params"] = params
        self.send(message)
        while True:
            ready, _, _ = select.select([self.proc.stdout], [], [], TIMEOUT)
            if not ready:
                sys.exit("Studio did not answer. Is it open with MCP switched on?")
            line = self.proc.stdout.readline()
            if not line:
                sys.exit("Studio's MCP program closed. Is Studio open with MCP switched on?")
            try:
                reply = json.loads(line)
            except ValueError:
                continue
            if reply.get("id") == self.next_id:
                if "error" in reply:
                    sys.exit("Error: " + json.dumps(reply["error"]))
                return reply["result"]

    def call(self, tool, arguments):
        result = self.request("tools/call", {"name": tool, "arguments": arguments})
        texts = [c.get("text", "") for c in result.get("content", []) if c.get("type") == "text"]
        others = []
        for c in result.get("content", []):
            if c.get("type") == "image" and c.get("data"):
                # pictures (screen_capture) are saved next to the temp files
                ext = (c.get("mimeType") or "image/png").split("/")[-1]
                path = os.path.join(tempfile.gettempdir(), "studio_%d.%s" % (int(time.time() * 1000), ext))
                with open(path, "wb") as f:
                    f.write(base64.b64decode(c["data"]))
                others.append("image saved to " + path)
            elif c.get("type") != "text":
                others.append(c.get("type"))
        return "\n".join(texts), others, result.get("isError", False)

    def studio_id(self):
        # The proxy needs a moment to find Studio after it starts
        for _ in range(20):
            text, _, _ = self.call("list_roblox_studios", {})
            studios = json.loads(text).get("studios", [])
            if studios:
                # another game's Studio may be open too: prefer the BubblePop window
                for s in studios:
                    if "BubblePop" in (s.get("name") or "") or "BubblePop" in (s.get("file") or ""):
                        return s["id"]
                return studios[0]["id"]
            time.sleep(0.5)
        sys.exit("No Studio window found. Open StealAFish.rbxlx and switch MCP on.")

    def close(self):
        self.proc.kill()


def main():
    args = sys.argv[1:]
    studio = Studio()
    try:
        if not args:
            for tool in studio.request("tools/list")["tools"]:
                print(tool["name"], "-", (tool.get("description") or "").split("\n")[0][:100])
            return
        if args[0] == "schema":
            for tool in studio.request("tools/list")["tools"]:
                if tool["name"] == args[1]:
                    print(json.dumps(tool, indent=1))
            return
        if args[0] == "luau":
            where = "Edit"
            rest = args[1:]
            if rest[0] in ("--server", "--client"):
                where = rest[0][2:].capitalize()
                rest = rest[1:]
            code = open(rest[1]).read() if rest[0] == "-f" else rest[0]
            tool, arguments = "execute_luau", {"code": code, "datamodel_type": where}
        else:
            tool, arguments = args[0], json.loads(args[1]) if len(args) > 1 else {}
        if tool != "list_roblox_studios":
            arguments.setdefault("studio_id", studio.studio_id())
        text, others, is_error = studio.call(tool, arguments)
        print(text)
        if others:
            print("(also returned: " + ", ".join(others) + ")")
        if is_error:
            sys.exit(1)
    finally:
        studio.close()


if __name__ == "__main__":
    main()
