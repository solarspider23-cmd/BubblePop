#!/usr/bin/env python3
"""Upload the baked colour textures of the HQ models (art/*_hq/<Name>.png) and
write the image id to art/*_hq/<Name>.texture.json.

    python3 tools/upload_textures.py              every HQ texture not yet uploaded
    python3 tools/upload_textures.py props_hq/Treadmill

Same needs as upload_model.py (place saved to Roblox, art/ approved for uploads).
Each PNG goes up as a Decal; Studio loads the decal once to read the image id
inside it, which is what a MeshPart's TextureID needs.
"""

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as S  # noqa: E402
from upload_model import ART, call, body_of  # noqa: E402
import time  # noqa: E402


def upload_decal(studio, sid, user_id, name):
    path = os.path.join(ART, name + ".png")
    req = {"request": {
        "assetType": "Decal", "displayName": os.path.basename(name), "description": "Steal a Fish " + name,
        "creationContext": {"creator": {"userId": str(user_id)}},
    }}
    text = call(studio, sid, "open_cloud_invoke", {
        "method": "POST", "endpoint": "/assets/v1/assets", "body": json.dumps(req),
        "files": [{"name": "fileContent", "path": path}], "scopes": ["asset:read", "asset:write"],
    })
    op = body_of(text).get("operationId")
    if not op:
        print("Upload of %s gave no operation: %s" % (name, text))
        return None, None
    for _ in range(60):
        time.sleep(2)
        reply = body_of(call(studio, sid, "open_cloud_invoke", {
            "method": "GET", "endpoint": "/assets/v1/operations/" + op, "scopes": ["asset:read"],
        }))
        if reply.get("done"):
            resp = reply.get("response", {})
            return resp.get("assetId"), resp.get("moderationResult", {}).get("moderationState")
    return None, None


def image_of(studio, sid, decal_id):
    code = ('local m = game:GetService("InsertService"):LoadAsset(%s) local t = "" '
            'for _, d in m:GetDescendants() do if d:IsA("Decal") then t = d.Texture end end '
            'm:Destroy() return t' % decal_id)
    for _ in range(10):
        text = call(studio, sid, "execute_luau", {"code": code, "datamodel_type": "Edit"})
        digits = re.findall(r"\d{6,}", text)
        if digits:
            return int(digits[-1])
        time.sleep(3)
    return None


def main():
    names = sys.argv[1:]
    if not names:
        for f in sorted(glob.glob(os.path.join(ART, "*_hq", "*.png"))):
            name = os.path.relpath(f, ART)[:-4]
            if os.path.exists(os.path.join(ART, name + ".fbx")) and not os.path.exists(
                    os.path.join(ART, name + ".texture.json")):
                names.append(name)
        print("%d textures to upload" % len(names))
    studio = S.Studio()
    try:
        sid = studio.studio_id()
        user_id = re.sub(r"\D", "", call(studio, sid, "execute_luau", {
            "code": 'return game:GetService("StudioService"):GetUserId()', "datamodel_type": "Edit",
        }))
        for name in names:
            decal, state = upload_decal(studio, sid, user_id, name)
            if not decal:
                continue
            image = image_of(studio, sid, decal)
            with open(os.path.join(ART, name + ".texture.json"), "w") as f:
                json.dump({"decal": int(decal), "image": image, "moderation": state}, f, indent=1)
            print("%s: decal %s image %s (%s)" % (name, decal, image, state))
    finally:
        studio.close()


if __name__ == "__main__":
    main()
