#!/usr/bin/env python3
"""Episode 21 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (12 shots = 12 sentences).
Framings 1a/1b and 3a/3b (5-second rule splits) REUSE the shot-01
and shot-03 backgrounds with different crops in compositing, so only
12 keys are generated here: shot-01..shot-12.
Output: ep21_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.

One apartment throughout: living room in the CENTER with a rug, a
window on the LEFT wall, a hallway to the RIGHT ending in a CLOSED
dark wooden door, a kitchen with a fridge in the LEFT background,
an entryway with shoes in the RIGHT foreground near the hallway, a
wall clock on the LEFT wall (visible ONLY in shot 9). Light
progression (directing): shots 1-3 cold bright morning, shots 4-5
strong direct midday, shots 6-8 warm afternoon, shots 9-10 orange
sunset, shots 11-12 night with the house lights on. The closed door
is always darker than the rest of the house.

Lessons from ep16/ep17/ep20/ep23/ep24 applied from the start: the
word "silhouette" / "shadow" makes FLUX render a human figure -- no
shadow language at all here. The vacuum cleaner is IN the background
ONLY in shots 1 and 2 (standing on the rug, handle upright, ONE
vacuum only); in shot 11 it is a foreground occluder drawn in
compositing code, so the shot-11 background must NOT contain a
vacuum. The clock appears ONLY in shot 9, blank face with hands
only, no numbers. The fridge door is OPEN only in shot 5, with
empty shelves and plain geometric shapes, no labels. No readable
text / numbers / logos anywhere, no second vacuum, no second
fridge, no second clock, no second rug.
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

ROOM = ("the same small apartment living room, a rug in the CENTER "
        "foreground, a window on the LEFT wall, a hallway opening on "
        "the RIGHT side of the frame leading to a CLOSED dark wooden "
        "door at the far end of the hallway, plain walls, a plain "
        "empty wall band across the very TOP of the frame")
NOBANS = ("no second vacuum cleaner, no second rug, no second door, "
          "no clock, no readable text, no numbers, no logos, "
          "no people, no characters")
LIGHT_MORNING = ("cold bright morning light coming from the window on "
                 "the LEFT, fresh clear morning mood")
LIGHT_NOON = ("strong direct midday light coming from the window on "
              "the LEFT, bright and sharp")
LIGHT_AFTERNOON = ("warm afternoon light coming from the window on the "
                   "LEFT, golden and calm")
LIGHT_SUNSET = ("soft orange sunset light coming from the window on "
                "the LEFT, warm evening mood")
LIGHT_NIGHT = ("night, the house lights are ON, warm artificial light, "
               "dark windows, quiet night mood")

VACUUM = ("ONE single upright vacuum cleaner standing on the rug in "
          "the CENTER foreground of the frame, its body low on the rug "
          "and its long handle standing upright, the handle clearly "
          "visible rising to about chest height, only one vacuum "
          "cleaner in the whole scene, never two")

PROMPTS = {
    "shot-01": "vertical 9:16, " + ROOM + ", " + LIGHT_MORNING + ", "
               + VACUUM + ", clear empty floor space on the rug around "
               "the vacuum cleaner where a person would stand in "
               "profile facing right toward the hallway, the closed "
               "dark wooden door visible at the far end of the hallway "
               "in the depth of the frame, tense opening mood, "
               + NOBANS,
    "shot-02": "vertical 9:16, " + ROOM + ", " + LIGHT_MORNING + ", "
               "the morning light slightly warmer than the first shot, "
               + VACUUM + ", clear empty floor space on the rug around "
               "the vacuum cleaner where a person would walk in "
               "profile from left to right pushing the vacuum cleaner, "
               + NOBANS,
    "shot-03": "vertical 9:16, a view down the hallway of the same "
               "apartment, a CLOSED dark wooden door at the far end of "
               "the hallway in the CENTER-RIGHT of the frame, plain "
               "empty hallway walls, dimmer light than the living room, "
               "the hallway darker than the rest of the house, plain "
               "floor, clear empty floor space in the CENTER of the "
               "frame where a person would stand in profile facing "
               "right toward the door, heavy thoughtful mood, a plain "
               "empty wall band across the very TOP of the frame, "
               "no door number, no door plate, no readable text, "
               "no numbers, no logos, no people, no characters",
    "shot-04": "vertical 9:16, " + ROOM + ", a BIG window on the LEFT "
               "wall, " + LIGHT_NOON + ", the window glass clean and "
               "shining, the window frame plain with no writing, clear "
               "empty floor space in the CENTER of the frame in front "
               "of the window where a person would stand in profile "
               "facing left toward the window, " + NOBANS,
    "shot-05": "vertical 9:16, the kitchen of the same apartment, a "
               "tall fridge with its door OPEN, the open fridge "
               "interior showing plain empty shelves with simple "
               "geometric shapes and no labels, cold white light "
               "spilling out of the open fridge onto the floor, "
               + LIGHT_NOON + ", clear empty floor space in front of "
               "the open fridge where a person would stand in profile "
               "facing left toward the fridge, a plain empty wall band "
               "across the very TOP of the frame, no food with fine "
               "detail, no labels, no magnets, no readable text, "
               "no numbers, no logos, no people, no characters",
    "shot-06": "vertical 9:16, the entryway of the same apartment, a "
               "row of simple plain shoes lined up on the floor, one "
               "pair in the middle being arranged and the rest neatly "
               "lined up, " + LIGHT_AFTERNOON + ", the light softer "
               "and dimmer than midday, clear empty floor space in the "
               "CENTER of the frame where a person would stand in "
               "profile facing right toward the shoes, a plain empty "
               "wall band across the very TOP of the frame, no tall "
               "boots, no writing on the shoes, no readable text, "
               "no numbers, no logos, no people, no characters",
    "shot-07": "vertical 9:16, " + ROOM + ", " + LIGHT_AFTERNOON + ", "
               "the afternoon light turning cooler than the previous "
               "shot, the rug clean, simple plain furniture, quiet "
               "empty space around the CENTER of the frame where a "
               "person would stand facing the camera, still and empty "
               "mood, " + NOBANS,
    "shot-08": "vertical 9:16, a corner of a room in the same "
               "apartment, a plain empty wall and a clean floor, "
               + LIGHT_AFTERNOON + ", the late afternoon light lower "
               "and warmer, a patch of daylight on the floor, clear "
               "empty floor space in the CENTER of the frame where a "
               "person would stand in profile facing right toward the "
               "corner, a plain empty wall band across the very TOP of "
               "the frame, no clock, no extra objects in the corner, "
               "no readable text, no numbers, no logos, no people, "
               "no characters",
    "shot-09": "vertical 9:16, the LEFT wall of the same apartment "
               "with ONE single round wall clock, the clock face BLANK "
               "with only the hands and no numbers, no roman numerals, "
               "no arabic numerals, " + LIGHT_SUNSET + ", a soft "
               "reflection of the sunset light on clean glass in the "
               "foreground, clear empty floor space in the CENTER of "
               "the frame where a person would stand in profile facing "
               "left toward the clock, a plain empty wall band across "
               "the very TOP of the frame, no second clock, no readable "
               "text, no numbers, no logos, no people, no characters",
    "shot-10": "vertical 9:16, the SAME hallway view as the third "
               "shot, a CLOSED dark wooden door at the far end of the "
               "hallway in the CENTER-RIGHT of the frame, plain empty "
               "hallway walls, the house now bright with ceiling lights "
               "ON and orange sunset light from the windows, but the "
               "door still CLOSED and dark, the same dark wooden door, "
               "plain floor, clear empty floor space in the CENTER of "
               "the frame where a person would stand in profile facing "
               "right toward the door, a plain empty wall band across "
               "the very TOP of the frame, no door number, no door "
               "plate, no readable text, no numbers, no logos, "
               "no people, no characters",
    "shot-11": "vertical 9:16, " + ROOM + ", " + LIGHT_NIGHT + ", "
               "clear empty floor space in the CENTER of the frame "
               "where a person would stand facing the camera, the rug "
               "visible in the foreground, NO vacuum cleaner anywhere "
               "in the scene, " + NOBANS,
    "shot-12": "vertical 9:16, a WIDER view of the same apartment "
               "living room, " + LIGHT_NIGHT + ", relatively dark and "
               "calm final night light, the CLOSED dark wooden door of "
               "the hallway visible in the DEEP RIGHT background, "
               "faint in the depth of the frame but still recognizable, "
               "clear empty floor space in the CENTER of the frame "
               "where a person would stand facing the camera, a plain "
               "empty wall band across the very TOP of the frame, "
               "no readable text, no numbers, no logos, no people, "
               "no characters",
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
                path = os.path.join("ep21_bgs", f"{key}.png")
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
    os.makedirs("ep21_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
