#!/usr/bin/env python3
"""Episode 23 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (11 shots = 11 sentences).
Output: ep23_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.

Single night kitchen throughout: tall fridge on the LEFT (vertical
handle on the RIGHT edge of its door, no magnets/stickers/photos),
stainless steel sink on the RIGHT, LOW in the frame, empty basin,
hallway door in the DEEP CENTER-RIGHT with faint warm light, plain
tiled floor, plain empty wall band across the very TOP of the frame
(card safe zone). Light progression (directing): shots 1-3 hallway
light only, fridge closed and dark; shots 4-8 fridge door OPEN with
cold white light spilling out; shot 9 door half-closed, light
dimming; shots 10-11 fridge closed again, hallway light only.

Lessons from ep16/ep17/ep20/ep24 applied from the start: the word
"silhouette" / "shadow" makes FLUX render a human figure — no shadow
language at all here (the cast-shadow arc is drawn in compositing
code, not in the background). The spoon is NEVER in the background:
it is held by the character and drawn in compositing code, so every
prompt bans spoons, forks and all cutlery. One plain unlabeled
ice-cream container visible ONLY in shot 5, inside the open fridge.
No readable text / numbers / logos anywhere, no clock, no magnets.
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

ROOM = ("the same small home kitchen at night, a tall plain fridge on "
        "the LEFT side of the frame with a vertical handle on the RIGHT "
        "edge of its door, a stainless steel sink on the RIGHT side of "
        "the frame LOW in the frame with an empty basin, a hallway door "
        "in the DEEP CENTER-RIGHT of the frame with faint warm light "
        "coming through it, plain tiled floor, a plain empty wall band "
        "across the very TOP of the frame")
NOBANS = ("no spoon, no fork, no cutlery anywhere, no second spoon, "
          "no magnets, no stickers, no photos on the fridge, no clock, "
          "no readable text, no numbers, no logos, no people, "
          "no characters")
LIGHT_HALL = ("only faint warm light coming from the hallway door, the "
              "fridge CLOSED and dark, dim quiet night mood")
LIGHT_FRIDGE = ("the fridge door OPEN, cold white light spilling out of "
                "the open fridge onto the floor and the wall, faint warm "
                "light still coming from the hallway door, cold white "
                "and warm light mixed")

PROMPTS = {
    "shot-01": "vertical 9:16, " + ROOM + ", " + LIGHT_HALL + ", clear "
               "empty floor space in the CENTER of the frame between "
               "the fridge and the sink where a person would stand "
               "facing the camera, tense opening mood, " + NOBANS,
    "shot-02": "vertical 9:16, " + ROOM + ", " + LIGHT_HALL + ", clear "
               "empty floor space in the CENTER-LEFT of the frame in "
               "front of the fridge where a person would stand in "
               "profile looking left toward the fridge, quiet listening "
               "mood, " + NOBANS,
    "shot-03": "vertical 9:16, " + ROOM + ", " + LIGHT_HALL + ", the "
               "fridge door handle clearly visible on the RIGHT edge of "
               "the fridge door at about chest height, clear empty floor "
               "space in front of the fridge where a person would stand "
               "in profile reaching for the handle, " + NOBANS,
    "shot-04": "vertical 9:16, " + ROOM + ", " + LIGHT_FRIDGE + ", the "
               "open fridge interior showing plain empty shelves with "
               "no containers and no labels, clear empty floor space in "
               "front of the open fridge where a person would stand "
               "facing the camera, " + NOBANS,
    "shot-05": "vertical 9:16, " + ROOM + ", " + LIGHT_FRIDGE + ", "
               "inside the open fridge ONE single plain round ice-cream "
               "container with NO label, NO text, NO lid markings, the "
               "only container in the fridge, the cold white light "
               "falling on the container, clear empty floor space in "
               "front of the open fridge where a person would stand in "
               "profile, " + NOBANS,
    "shot-06": "vertical 9:16, " + ROOM + ", " + LIGHT_FRIDGE + ", the "
               "open fridge interior showing plain empty shelves with "
               "no containers and no labels, a closer view of the open "
               "fridge and the floor in front of it where a person "
               "would stand facing the camera, " + NOBANS,
    "shot-07": "vertical 9:16, " + ROOM + ", " + LIGHT_FRIDGE + ", the "
               "open fridge on the LEFT of the frame, a wider view of "
               "the kitchen with clear empty floor space in the CENTER "
               "where a person would stand in profile looking right, "
               "long dark night mood, " + NOBANS,
    "shot-08": "vertical 9:16, " + ROOM + ", " + LIGHT_FRIDGE + ", the "
               "open fridge interior showing plain empty shelves with "
               "no containers and no labels, a closer view of the "
               "center of the kitchen where a person would stand facing "
               "the camera, still and quiet mood, " + NOBANS,
    "shot-09": "vertical 9:16, " + ROOM + ", the fridge door HALF-CLOSED "
               "and closing, the cold white light from inside the fridge "
               "dim and fading, faint warm light from the hallway door, "
               "clear empty floor space in front of the fridge where a "
               "person would stand in profile pushing the door, "
               + NOBANS,
    "shot-10": "vertical 9:16, " + ROOM + ", " + LIGHT_HALL + ", the "
               "stainless steel sink on the RIGHT clearly visible with "
               "its empty basin, clear empty floor space above the sink "
               "where a person would stand in profile looking right "
               "toward the sink, quiet still mood, " + NOBANS,
    "shot-11": "vertical 9:16, " + ROOM + ", " + LIGHT_HALL + ", a wider "
               "view of the same dim kitchen, clear empty floor space in "
               "the CENTER of the frame where a person would stand "
               "facing the camera, calm released ending mood, " + NOBANS,
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
                path = os.path.join("ep23_bgs", f"{key}.png")
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
    os.makedirs("ep23_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
