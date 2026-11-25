#!/usr/bin/env python3
"""Upload art/<Name>.fbx to Roblox through the open Studio and write the
mesh ids of its parts to art/<Name>.meshes.json.

    python3 tools/upload_model.py Treadmill           upload art/Treadmill.fbx
    python3 tools/upload_model.py Stall FuseMachine   several at once
    python3 tools/upload_model.py creatures_hq/Beluga one in a subfolder
    python3 tools/upload_model.py --all-hq             every art/*_hq model not yet uploaded

Studio must be open on the saved place (Steal a Fish, saved to Roblox) with MCP on, and
art/ must be an approved upload directory (Assistant Settings > MCP
Permissions). The FBX goes up as a Model; Studio then loads it once to read
the MeshId and size of every MeshPart inside. The world code can make MeshParts
from those ids with AssetService:CreateMeshPartAsync.
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as S  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ART = os.path.abspath(os.path.join(ROOT, "art"))


def call(studio, sid, tool, args):
    args = dict(args, studio_id=sid)
    text, _, is_error = studio.call(tool, args)
    if is_error:
        sys.exit("%s failed: %s" % (tool, text))
    return text


def body_of(text):
    # open_cloud_invoke answers "METHOD url -> 200 OK\n\n{json}"
    i = text.find("{")
    return json.loads(text[i:]) if i >= 0 else {}


def upload(studio, sid, user_id, name):
    path = os.path.join(ART, name + ".fbx")
    if not os.path.exists(path):
        sys.exit("No such file: " + path)
    req = {"request": {
        "assetType": "Model", "displayName": name, "description": "BubblePop " + name,
        "creationContext": {"creator": {"userId": str(user_id)}},
    }}
    text = call(studio, sid, "open_cloud_invoke", {
        "method": "POST", "endpoint": "/assets/v1/assets", "body": json.dumps(req),
        "files": [{"name": "fileContent", "path": path}], "scopes": ["asset:read", "asset:write"],
    })
    op = body_of(text).get("operationId")
    if not op:
        sys.exit("Upload of %s gave no operation: %s" % (name, text))
    for _ in range(60):
        time.sleep(2)
        reply = body_of(call(studio, sid, "open_cloud_invoke", {
            "method": "GET", "endpoint": "/assets/v1/operations/" + op, "scopes": ["asset:read"],
        }))
        if reply.get("done"):
            resp = reply.get("response", {})
            state = resp.get("moderationResult", {}).get("moderationState")
            return resp.get("assetId"), state
    sys.exit("Upload of %s did not finish" % name)


def mesh_ids(studio, sid, asset_id):
    code = (
        'local m = game:GetService("InsertService"):LoadAsset(%s) local out = {} '
        'for _, d in m:GetDescendants() do if d:IsA("MeshPart") then '
        'table.insert(out, string.format("%%s|%%s|%%.4f|%%.4f|%%.4f|%%.4f|%%.4f|%%.4f", d.Name, d.MeshId, '
        'd.Size.X, d.Size.Y, d.Size.Z, d.Position.X, d.Position.Y, d.Position.Z)) '
        'end end m:Destroy() return table.concat(out, "\\n")' % asset_id
    )
    text = call(studio, sid, "execute_luau", {"code": code, "datamodel_type": "Edit"})
    parts = {}
    for line in text.splitlines():
        bits = line.strip().split("|")
        if len(bits) == 8 and "rbxassetid://" in bits[1]:
            parts[bits[0]] = {
                "meshId": int(re.sub(r"\D", "", bits[1])),
                "size": [float(bits[2]), float(bits[3]), float(bits[4])],
                # where the part sat in the loaded model: only the distances
                # between parts mean anything; check
                # them against art/<Name>.bounds.json
                "position": [float(bits[5]), float(bits[6]), float(bits[7])],
            }
    return parts


def main():
    names = sys.argv[1:]
    if names == ["--all-hq"]:
        # every HQ model in art/*_hq/, skipping ones already uploaded
        import glob
        names = []
        for f in sorted(glob.glob(os.path.join(ART, "*_hq", "*.fbx"))):
            name = os.path.relpath(f, ART)[:-4]
            if not os.path.exists(os.path.join(ART, name + ".meshes.json")):
                names.append(name)
        print("%d HQ models to upload" % len(names))
    if not names:
        sys.exit(__doc__)
    studio = S.Studio()
    try:
        sid = studio.studio_id()
        user_id = re.sub(r"\D", "", call(studio, sid, "execute_luau", {
            "code": 'return game:GetService("StudioService"):GetUserId()', "datamodel_type": "Edit",
        }))
        for name in names:
            asset_id, state = upload(studio, sid, user_id, name)
            parts = mesh_ids(studio, sid, asset_id)
            out = {"model": int(asset_id), "moderation": state, "parts": parts}
            with open(os.path.join(ART, name + ".meshes.json"), "w") as f:
                json.dump(out, f, indent=1)
            print("%s: model %s (%s), %d parts -> art/%s.meshes.json" % (name, asset_id, state, len(parts), name))
    finally:
        studio.close()


if __name__ == "__main__":
    main()
