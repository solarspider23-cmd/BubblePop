#!/usr/bin/env python3
"""Fill the uploaded HQ models into src/ReplicatedStorage/Shared/Config/Models.lua.

    python3 tools/fill_models.py

For every entry line in Models.lua, looks for an uploaded HQ model
(art/*_hq/<Name>.meshes.json, written by upload_model.py) named after the entry's
key or its file, and rewrites the line with its model id, the texture image id
(art/*_hq/<Name>.texture.json, from upload_textures.py) and the colours of its
glow / coloured parts (art/*_hq/<Name>.bounds.json). Entries with no HQ upload
are left alone. Safe to run again after more uploads.
"""

import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ART = os.path.join(ROOT, "art")
MODELS = os.path.join(ROOT, "src", "ReplicatedStorage", "Shared", "Config", "Models.lua")

# Entry keys whose HQ model has a different name
ALIAS = {"plain": "EggCommon", "sparkle": "EggEpic"}

LINE = re.compile(r'^(\t)(\w+) = \{ file = "([^"]+)", assetId = \d+, scale = ([\d.]+).*\},(\s*(?:--.*)?)$')


def hq_index():
    index = {}
    for f in glob.glob(os.path.join(ART, "*_hq", "*.meshes.json")):
        name = os.path.relpath(f, ART)[: -len(".meshes.json")]
        index.setdefault(os.path.basename(name), name)
    return index


def lua_parts(bounds):
    out = []
    for part, info in sorted(bounds.items()):
        if not isinstance(info, dict) or "texture" in info:
            continue
        color = info.get("color")
        if not (isinstance(color, list) and len(color) == 3):
            continue
        material = "Neon" if info.get("neon") else info.get("material")
        bits = ["color = { %d, %d, %d }" % tuple(int(c) for c in color)]
        if isinstance(material, str) and re.fullmatch(r"[A-Za-z]+", material):
            bits.append('material = "%s"' % material)
        out.append("%s = { %s }" % (part, ", ".join(bits)))
    return out


def main():
    index = hq_index()
    lines = open(MODELS).read().split("\n")
    filled = 0
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if not m:
            continue
        indent, key, file, scale, tail = m.groups()
        tail = tail or ""
        base = os.path.splitext(os.path.basename(file))[0]
        name = None
        for cand in (ALIAS.get(key), base, base.replace("Creature_", ""), key):
            if cand and cand in index:
                name = index[cand]
                break
        if not name:
            continue
        mesh = json.load(open(os.path.join(ART, name + ".meshes.json")))
        model = int(mesh.get("model") or 0)
        if model <= 0:
            continue
        fields = ['file = "art/%s.fbx"' % name, "assetId = %d" % model, "scale = %s" % scale]
        tex_path = os.path.join(ART, name + ".texture.json")
        if os.path.exists(tex_path):
            image = json.load(open(tex_path)).get("image")
            if image:
                fields.append("texture = %d" % int(image))
        bounds_path = os.path.join(ART, name + ".bounds.json")
        if os.path.exists(bounds_path):
            parts = lua_parts(json.load(open(bounds_path)))
            if parts:
                fields.append("parts = { %s }" % ", ".join(parts))
        lines[i] = "%s%s = { %s },%s" % (indent, key, ", ".join(fields), tail)
        filled += 1
    open(MODELS, "w").write("\n".join(lines))
    print("Filled %d entries in Models.lua" % filled)


if __name__ == "__main__":
    main()
