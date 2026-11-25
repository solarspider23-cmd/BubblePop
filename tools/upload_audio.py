#!/usr/bin/env python3
"""Upload our own sound files (art/sounds/<Name>.wav) to Roblox as Audio and write
the sound id to art/sounds/<Name>.audio.json.

    python3 tools/upload_audio.py                 every art/sounds/*.wav not yet uploaded
    python3 tools/upload_audio.py Pop_Crisp       just one

Same needs as upload_model.py: the published place open in Studio (Edit mode) and
art/ approved under MCP Permissions.
"""
import glob
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import studio as S  # noqa: E402
from upload_model import ART, call, body_of  # noqa: E402

SOUNDS = os.path.join(ART, "sounds")


def upload(studio, sid, user_id, name):
    path = os.path.join(SOUNDS, name + ".wav")
    req = {"request": {
        "assetType": "Audio", "displayName": "BubblePop " + name, "description": "BubblePop sound " + name,
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


def main():
    names = sys.argv[1:] or [
        os.path.basename(f)[:-4] for f in sorted(glob.glob(os.path.join(SOUNDS, "*.wav")))
        if not os.path.exists(f[:-4] + ".audio.json")
    ]
    studio = S.Studio()
    try:
        sid = studio.studio_id()
        user_id = re.sub(r"\D", "", call(studio, sid, "execute_luau", {
            "code": 'return game:GetService("StudioService"):GetUserId()', "datamodel_type": "Edit",
        }))
        for name in names:
            asset, state = upload(studio, sid, user_id, name)
            if not asset:
                continue
            with open(os.path.join(SOUNDS, name + ".audio.json"), "w") as f:
                json.dump({"id": int(asset), "moderation": state}, f, indent=1)
            print("%s: sound %s (%s)" % (name, asset, state))
    finally:
        studio.close()


if __name__ == "__main__":
    main()
