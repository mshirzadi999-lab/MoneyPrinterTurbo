#!/usr/bin/env python3
"""Episode 4 TEST backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (characters composited later,
locally). Only the 3 stage-6 test frames: t1 (present-self alone, heavy
grey bedroom), t4 (future-self entrance: grey room + door with warm
light shaft), t12 (finale: sunrise-flooded warm room).
Output: ep4_bgs/<key>.png. Env: CF account/token pairs 1..3. ONLY=keys.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

STYLE = ("hand-painted cinematic matte painting, painterly illustration "
         "with clearly visible broad brushstrokes and dry-brush texture, "
         "stylized simplified shapes, soft painted edges, flat washes of "
         "color, gouache painting look, 2D animation background art, "
         "absolutely NOT photorealistic, not a photograph, no photographic "
         "detail, no camera look, no letters, no words, no numbers, "
         "no watermark, empty scene, no people, no characters, no text")

PROMPTS = {
    "t1": "vertical 9:16, small dim bedroom before dawn, an unmade bed "
          "with a rumpled grey blanket taking the lower middle of the "
          "frame, plain wooden chair in a dark corner, window with closed "
          "blinds leaking thin cold grey light, heavy still air, muted "
          "grey-blue palette, oppressive quiet mood of a man crushed by "
          "his own thoughts",
    "t4": "vertical 9:16, the same dim grey bedroom interior, unmade bed "
          "along the left wall, heavy cold grey shadows, on the right a "
          "wooden door slightly open with a dramatic exaggerated shaft "
          "of warm golden light spilling through the doorway across the "
          "floor into the grey room, strong contrast of cold grey gloom "
          "and the first warm hopeful light, a clear empty floor space "
          "in the middle and right of the room, all walls completely "
          "plain and bare, absolutely no light switches, no wall plates, "
          "no sockets, no fixtures, no markings on any wall",
    "s06a": "vertical 9:16, corner of a dim grey room, on the wooden "
            "floor a tall wobbly half-built tower of plain unmarked "
            "wooden toy blocks leaning dangerously to one side, a few "
            "plain blocks scattered at its base, the blocks completely "
            "blank with no letters, no numbers, no symbols, no prints, "
            "clear empty floor space beside the tower, muted cold "
            "grey-blue palette, heavy mood of fearing a collapse",
    "s06b": "vertical 9:16, a bare dim wall in a dark room at night, "
            "huge vague blurred human-shaped SHADOWS cast across the "
            "wall as if unseen people stood just out of frame, shadows "
            "only, absolutely no actual people and no figures, "
            "oppressive cold blue-grey darkness, a narrow strip of "
            "empty floor at the bottom, mood of being silently judged",
    "s06c": "vertical 9:16, a plain wooden desk in a dim room seen "
            "from the front, on the desk a half-finished jigsaw puzzle "
            "with scattered plain muted pieces showing no readable "
            "picture, beside it a half-knitted grey sweater still on "
            "two knitting needles with a ball of yarn, everything "
            "unfinished and abandoned mid-work, no letters, no words, "
            "no printed images anywhere, cold muted light, clear empty "
            "space behind the desk",
    "s11b": "vertical 9:16, extreme low angle close view of an empty "
            "wooden plank floor in a warm dim room, planks running "
            "away in strong perspective, one long pool of warm amber "
            "evening light lying across the boards, the whole frame "
            "filled with empty floor, quiet hopeful mood",
    "s11c": "vertical 9:16, the same small bedroom at night but warm "
            "and cozy, an unmade bed along the left wall with a soft "
            "blanket, warm amber light pooling across the room from "
            "the right side, deep soft shadows, clear empty floor "
            "space in the middle and right of the room, all walls "
            "completely plain and bare, intimate hopeful night mood",
    "t12": "vertical 9:16, small room interior at sunrise transformed by "
           "warmth, a large window with warm golden sunlight flooding "
           "in, long soft golden shadows across a wooden floor, dust "
           "motes floating in the light beams, warm amber and honey "
           "palette, airy feeling of release, relief and quiet hope, "
           "clear empty floor space in the middle of the room",
}

PAIRS = (("CF_ACCOUNT_ID", "CF_API_TOKEN"),
         ("CF_ACCOUNT_ID_2", "CF_API_TOKEN_2"),
         ("CF_ACCOUNT_ID_3", "CF_API_TOKEN_3"))
ACCOUNTS = []
for _a, _t in PAIRS:
    _av = (os.environ.get(_a) or "").strip()
    _tv = (os.environ.get(_t) or "").strip()
    if _av and _tv:
        ACCOUNTS.append((_av, _tv))

KLEIN = "@cf/black-forest-labs/flux-2-klein-4b"


def _post(acc, tok, model, data, ctype):
    url = ("https://api.cloudflare.com/client/v4/accounts/"
           f"{acc}/ai/run/{model}")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def _extract(ctype, body):
    if ctype.startswith("image/"):
        return body
    data = json.loads(body.decode("utf-8"))
    if not data.get("success", False):
        raise RuntimeError(f"cloudflare error: {data.get('errors')}")
    b64 = (data.get("result") or {}).get("image")
    if not b64:
        raise RuntimeError("response has no result.image")
    return base64.b64decode(b64)


def _multipart(fields):
    boundary = "----cfform" + uuid.uuid4().hex
    out = []
    for name, value in fields:
        out.append(f"--{boundary}\r\n".encode())
        out.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        out.append(str(value).encode("utf-8"))
        out.append(b"\r\n")
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def gen_klein(acc, tok, prompt):
    body, ctype = _multipart(
        [("prompt", prompt), ("width", "768"), ("height", "1344")])
    rtype, rbody = _post(acc, tok, KLEIN, body, ctype)
    return _extract(rtype, rbody)


def gen_one(key, prompt):
    last = None
    for attempt in range(4):
        for i, (acc, tok) in enumerate(ACCOUNTS):
            try:
                img = gen_klein(acc, tok, prompt)
                path = os.path.join("ep4_bgs", f"{key}.png")
                with open(path, "wb") as f:
                    f.write(img)
                print(f"{key}: OK via account {i + 1} "
                      f"({len(img)} bytes)", flush=True)
                return True
            except Exception as e:  # noqa: BLE001 - next account / retry
                last = e
                print(f"{key}: account {i + 1} failed: {e}", flush=True)
        time.sleep(10 * (attempt + 1))
    print(f"{key}: ALL FAILED: {last}", flush=True)
    return False


def main():
    if not ACCOUNTS:
        print("no Cloudflare accounts configured")
        return 2
    os.makedirs("ep4_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
