#!/usr/bin/env python3
"""Episode 24 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per sentence-shot (12 shots = 12
sentences); shot-06 and shot-12 REUSE the shot-05 background
(directing: S6/S12 are the same sit_desk framing as S5 — same room,
same desk, cold day-10 light, closed notebook), so only 10 keys are
generated here: shot-01..shot-05, shot-07..shot-11.
Output: ep24_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.

Lessons from ep16/ep17/ep20 applied from the start: the word
"silhouette" / "shadow" makes FLUX render a human figure — no shadow
language at all here. The notebook sits ON the desk explicitly; day 1
it is OPEN with blank pages, day 10 it is CLOSED with a plain cover.
The wall planner above the desk shows ONLY empty rectangular boxes
and blank horizontal lines, never words/letters/numbers. No readable
text / numbers / logos anywhere. One room throughout: desk on the
RIGHT, daylight from the left; day 1 warm bright morning light, day
10 the same light colder and dimmer. One desk, one notebook, one
wall planner — never a duplicate of any of them.
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

# Shared room beats, composed per shot below.
ROOM_DAY1 = ("the same bright home room in daylight, a simple wooden "
             "desk on the RIGHT side of the frame with FOUR STRAIGHT "
             "LEGS, NO crossbar, NO stretcher bar between the legs, NO "
             "horizontal bar under the desk, just four plain legs with "
             "open space under the top, the desk top LOW in the frame "
             "with its front edge about two-thirds down the frame")
ROOM_DAY10 = ("the same home room in dim cold daylight, the same simple "
              "wooden desk on the RIGHT side of the frame with FOUR "
              "STRAIGHT LEGS, NO crossbar, NO stretcher bar between the "
              "legs, NO horizontal bar under the desk, just four plain "
              "legs with open space under the top, the desk top LOW in "
              "the frame with its front edge about two-thirds down the "
              "frame")
WALL_PLAN = ("a wall planner hanging on the wall ABOVE the desk, the "
             "planner showing ONLY empty rectangular boxes and blank "
             "horizontal lines, absolutely no letters, no words, no "
             "numbers, no handwriting, no scribbles, no marks beside "
             "the lines")
NOTEBOOK_OPEN = ("ONE single notebook lying OPEN on the desk, the open "
                 "notebook showing ONLY blank empty pages, no writing, "
                 "no letters, no words, no numbers, no drawings, only "
                 "one notebook in the whole scene, never two notebooks")
NOTEBOOK_CLOSED = ("ONE single notebook lying CLOSED flat on the desk, "
                   "a plain cover with no text, no letters, no logo, no "
                   "numbers, only one notebook in the whole scene, "
                   "never two notebooks")
LIGHT_WARM = ("warm bright morning light coming from a window on the "
              "LEFT outside the frame, soft daylight from the left")
LIGHT_COLD = ("cold dim muted daylight coming from a window on the LEFT "
              "outside the frame, the same light as the morning but "
              "colder and dimmer, pale grey-blue light from the left")

PROMPTS = {
    "shot-01": "vertical 9:16, " + ROOM_DAY1 + ", " + NOTEBOOK_OPEN +
               ", " + WALL_PLAN + ", " + LIGHT_WARM + ", plain empty "
               "wall on the left, clear empty floor space in the "
               "CENTER-LEFT of the frame where a person would stand "
               "facing the camera, no second notebook, no person",
    "shot-02": "vertical 9:16, " + ROOM_DAY1 + ", " + NOTEBOOK_OPEN +
               ", " + WALL_PLAN + ", " + LIGHT_WARM + ", plain empty "
               "wall on the left, clear empty floor space in front of "
               "the desk where a person would sit on a chair facing "
               "the desk, no second notebook, no person",
    "shot-03": "vertical 9:16, a bright home room in daylight, a wooden "
               "desk occupying ONLY the RIGHT HALF of the frame, " +
               NOTEBOOK_OPEN + ", " + WALL_PLAN + ", a patch of warm "
               "morning light falling on the desk surface and the "
               "floor, soft daylight from the left, clear empty floor "
               "space on the LEFT HALF of the frame where a person "
               "would stand on the floor beside the desk looking at "
               "the notebook, plain empty wall behind the desk, no "
               "second notebook, no person",
    "shot-04": "vertical 9:16, " + ROOM_DAY1 + ", " + NOTEBOOK_OPEN +
               ", " + WALL_PLAN + ", " + LIGHT_WARM + ", plain empty "
               "wall on the left, clear empty floor space beside the "
               "desk where a person would stand on the floor leaning "
               "over the notebook, no second notebook, no person",
    "shot-05": "vertical 9:16, " + ROOM_DAY10 + ", " + NOTEBOOK_CLOSED +
               ", " + WALL_PLAN + ", " + LIGHT_COLD + ", plain empty "
               "wall on the left, clear empty floor space in front of "
               "the desk where a person would sit on a chair facing "
               "the desk, no second notebook, no person",
    "shot-07": "vertical 9:16, " + ROOM_DAY10 + ", " + NOTEBOOK_CLOSED +
               ", " + WALL_PLAN + ", " + LIGHT_COLD + ", plain empty "
               "wall on the left, clear empty floor space beside the "
               "desk where a person would stand on the floor facing "
               "the desk, no second notebook, no person",
    "shot-08": "vertical 9:16, " + ROOM_DAY10 + ", " + NOTEBOOK_CLOSED +
               ", " + WALL_PLAN + ", " + LIGHT_COLD + ", plain empty "
               "wall on the left, clear empty floor space beside the "
               "desk where a person would stand on the floor facing "
               "the desk, no second notebook, no person",
    "shot-09": "vertical 9:16, " + ROOM_DAY10 + ", " + NOTEBOOK_CLOSED +
               ", " + WALL_PLAN + ", " + LIGHT_COLD + ", plain empty "
               "wall on the left, clear empty floor space in the "
               "CENTER-LEFT of the frame where a person would stand "
               "facing the camera, no second notebook, no person",
    "shot-10": "vertical 9:16, " + ROOM_DAY10 + ", " + NOTEBOOK_CLOSED +
               ", " + WALL_PLAN + ", " + LIGHT_COLD + ", plain empty "
               "wall on the left, large clear empty floor space on the "
               "LEFT side of the frame, no second notebook, no person",
    "shot-11": "vertical 9:16, wide view of the same home room in dim "
               "cold daylight, a wooden desk on the FAR RIGHT side of "
               "the frame with " + NOTEBOOK_CLOSED + ", " + WALL_PLAN +
               ", " + LIGHT_COLD + ", plain empty wall, large clear "
               "empty floor space on the LEFT side of the room where a "
               "person would walk from right to left, no second "
               "notebook, no person, no readable text",
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
                path = os.path.join("ep24_bgs", f"{key}.png")
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
    os.makedirs("ep24_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
