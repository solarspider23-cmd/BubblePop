#!/usr/bin/env python3
"""Builds BubblePop.rbxlx (a Roblox place file) from the scripts in src/.

Run:  python3 tools/build_place.py
Then open BubblePop.rbxlx in Roblox Studio (File > Open from File).
"""
import re
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "BubblePop.rbxlx"

_ref = 0


def ref():
    global _ref
    _ref += 1
    return f"RBX{_ref:08d}"


def script_item(cls, name, path):
    source = path.read_text(encoding="utf-8")
    if "]]>" in source:
        raise SystemExit(f"{path} contains ']]>', which breaks the place file")
    return (
        f'<Item class="{cls}" referent="{ref()}"><Properties>'
        f'<string name="Name">{escape(name)}</string>'
        f"<ProtectedString name=\"Source\"><![CDATA[{source}]]></ProtectedString>"
        f"</Properties></Item>"
    )


def container(cls, name, children):
    return (
        f'<Item class="{cls}" referent="{ref()}"><Properties>'
        f'<string name="Name">{escape(name)}</string></Properties>'
        + "".join(children)
        + "</Item>"
    )


def spawn_location():
    return (
        f'<Item class="SpawnLocation" referent="{ref()}"><Properties>'
        '<string name="Name">SpawnLocation</string>'
        '<bool name="Anchored">true</bool>'
        '<CoordinateFrame name="CFrame"><X>0</X><Y>0.2</Y><Z>0</Z>'
        "<R00>1</R00><R01>0</R01><R02>0</R02><R10>0</R10><R11>1</R11><R12>0</R12>"
        "<R20>0</R20><R21>0</R21><R22>1</R22></CoordinateFrame>"
        '<Vector3 name="size"><X>8</X><Y>0.4</Y><Z>8</Z></Vector3>'
        '<float name="Transparency">1</float>'
        '<bool name="CanCollide">false</bool>'
        "</Properties></Item>"
    )


def tree_items(folder):
    """Scripts in a folder, with sub-folders as Roblox Folders.
    *.server.lua -> Script, *.client.lua -> LocalScript, *.lua -> ModuleScript"""
    items = []
    for p in sorted(folder.iterdir()):
        if p.is_dir():
            items.append(container("Folder", p.name, tree_items(p)))
        elif p.name.endswith(".server.lua"):
            items.append(script_item("Script", p.name.removesuffix(".server.lua"), p))
        elif p.name.endswith(".client.lua"):
            items.append(script_item("LocalScript", p.name.removesuffix(".client.lua"), p))
        elif p.suffix == ".lua":
            items.append(script_item("ModuleScript", p.stem, p))
    return items


shared_dir = SRC / "ReplicatedStorage" / "Shared"
modules = tree_items(shared_dir)

# Never build a place that fails the code check or the save tests
if "--skip-checks" not in sys.argv:
    check = subprocess.run([sys.executable, str(ROOT / "tools" / "check_code.py")])
    if check.returncode != 0:
        raise SystemExit("Build stopped: code check failed")

server_items = tree_items(SRC / "ServerScriptService")

client_dir = SRC / "StarterPlayer" / "StarterPlayerScripts"
client_items = tree_items(client_dir)

def lighting():
    # Technology 4 = Future: real-time lights and shadows from every light
    # source (neon strips, floodlights, portals). Scripts can't set this.
    return (
        f'<Item class="Lighting" referent="{ref()}"><Properties>'
        '<string name="Name">Lighting</string>'
        '<token name="Technology">4</token>'
        "</Properties></Item>"
    )


def saved_models():
    """Models saved from Studio as art/*.rbxmx (right-click > Save to File)
    go into ServerStorage, so rebuilding this file doesn't lose them.
    Returns (items xml, shared strings xml)."""
    items, shared = [], []
    for path in sorted((ROOT / "art").glob("*.rbxmx")):
        text = path.read_text(encoding="utf-8")
        body = text[text.index(">", text.index("<roblox")) + 1 : text.rindex("</roblox>")]
        body = re.sub(r"<External>.*?</External>|<Meta[^>]*>.*?</Meta>", "", body, flags=re.S)
        m = re.search(r"<SharedStrings>(.*?)</SharedStrings>", body, flags=re.S)
        if m:
            shared.append(m.group(1))
            body = body[: m.start()] + body[m.end() :]
        items.append(body)
        print(f"Including {path.name} in ServerStorage")
    return "".join(items), "".join(shared)


art_items, art_shared = saved_models()

parts = [
    container("Workspace", "Workspace", [spawn_location()]),
    lighting(),
    container("ReplicatedStorage", "ReplicatedStorage", [container("Folder", "Shared", modules)]),
    container("ServerScriptService", "ServerScriptService", server_items),
    container("ServerStorage", "ServerStorage", [art_items]),
    container(
        "StarterPlayer",
        "StarterPlayer",
        [
            container("StarterPlayerScripts", "StarterPlayerScripts", client_items)
        ],
    ),
]

xml = (
    '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">'
    + "".join(parts)
    + (f"<SharedStrings>{art_shared}</SharedStrings>" if art_shared else "")
    + "</roblox>\n"
)
OUT.write_text(xml, encoding="utf-8")
print(f"Wrote {OUT.name} ({len(modules)} shared modules, {len(server_items)} server scripts, {len(client_items)} client scripts)")
