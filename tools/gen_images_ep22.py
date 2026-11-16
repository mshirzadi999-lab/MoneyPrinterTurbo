#!/usr/bin/env python3
"""Episode 22 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (12 shots = 12 sentences;
the 3 intra-shot cuts are second framings of the SAME scene in
compositing, not new scenes). Output: ep22_bgs/<key>.png. Env: CF
account/token pairs 1..3. ONLY=keys.

One open room throughout: a simple wooden work desk on the RIGHT,
plain empty wall on the LEFT, daylight from a window on the LEFT
outside the frame, light floor. The rings are NEVER in the
background: they are worn by the character and drawn in compositing
code (exact alignment with the torso, identical physical size in
every shot, crack in shot 12) — so every prompt bans rings, hoops
and bands. The paper appears ONLY in shots 10/11, on the desk:
blank in shot 10, with ONE tick (square + diagonal line, no words)
in shot 11.

Lessons from ep16/ep17/ep20/ep23/ep24 applied from the start: the
word "silhouette" / "shadow" makes FLUX render a human figure — no
shadow language at all here. No readable text / numbers / logos
anywhere. One desk, one paper, no second desk, no second paper.
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

ROOM = ("the same bright home room in daylight, a simple wooden work "
        "desk on the RIGHT side of the frame, plain empty wall on the "
        "LEFT side of the frame, soft daylight coming from a window on "
        "the LEFT outside the frame, light wooden floor")
NOBANS = ("no rings, no hoops, no bands, no rope, no circular objects "
          "around anything, no second desk, no readable text, no "
          "numbers, no logos, no people, no characters")

PROMPTS = {
    "shot-01": "vertical 9:16, " + ROOM + ", a wide view of the room, "
               "the desk on the RIGHT with its front edge about "
               "two-thirds down the frame, clear empty floor space in "
               "the CENTER and LEFT of the frame where a person would "
               "walk from the desk toward the left, ordinary daytime "
               "mood, " + NOBANS,
    "shot-02": "vertical 9:16, " + ROOM + ", the desk on the RIGHT, "
               "clear empty floor space in the CENTER of the frame "
               "where a person would stand in profile facing right "
               "toward the desk, quiet tense mood, " + NOBANS,
    "shot-03": "vertical 9:16, " + ROOM + ", a closer medium view of "
               "the room, the desk at the RIGHT edge of the frame, "
               "plain empty wall behind, clear empty floor space in "
               "the CENTER where a person would stand in profile "
               "facing right, the wall filling most of the frame, "
               + NOBANS,
    "shot-04": "vertical 9:16, " + ROOM + ", a medium view of the desk "
               "on the RIGHT with open space under the desk top and "
               "the floor clearly visible under it, a plain chair "
               "shape tucked under the desk, clear space in front of "
               "the desk where a person would sit facing right, flat "
               "drained mood, no paper on the desk, " + NOBANS,
    "shot-05": "vertical 9:16, " + ROOM + ", wide empty floor space in "
               "the CENTER of the room, the desk only at the FAR RIGHT "
               "edge of the frame, plain empty wall, heavy slow mood, "
               + NOBANS,
    "shot-06": "vertical 9:16, " + ROOM + ", the desk on the RIGHT, "
               "clear empty floor space in the CENTER where a person "
               "would stand in profile facing right toward the desk, "
               "still frozen mood, " + NOBANS,
    "shot-07": "vertical 9:16, " + ROOM + ", wide empty floor space in "
               "the CENTER of the room, the desk on the RIGHT, plain "
               "empty wall on the LEFT, restless hurried mood, "
               + NOBANS,
    "shot-08": "vertical 9:16, " + ROOM + ", a wider view of the room, "
               "the desk SMALLER and FARTHER on the RIGHT with clear "
               "empty floor space between the center and the desk, "
               "plain empty wall, drained quiet mood, " + NOBANS,
    "shot-09": "vertical 9:16, " + ROOM + ", a closer medium view, "
               "plain empty wall filling the whole background, soft "
               "daylight from the left, no desk in the frame, clear "
               "empty floor space at the bottom where a person would "
               "stand facing the camera, tense frustrated mood, "
               + NOBANS,
    "shot-10": "vertical 9:16, " + ROOM + ", the desk on the RIGHT "
               "with ONE single small blank paper lying flat ON the "
               "desk, the paper completely blank with no marks, no "
               "letters, no lines, clear space in front of the desk "
               "where a person would sit facing right, gentle hopeful "
               "mood, " + NOBANS,
    "shot-11": "vertical 9:16, " + ROOM + ", the same framing as a "
               "desk on the RIGHT with ONE single small paper lying "
               "flat ON the desk, the paper showing ONLY one small "
               "empty square with ONE diagonal tick mark inside it "
               "and nothing else, absolutely no letters, no words, no "
               "numbers, no handwriting, clear space in front of the "
               "desk where a person would sit facing right, quiet "
               "satisfied mood, " + NOBANS,
    "shot-12": "vertical 9:16, " + ROOM + ", a wide view of the room, "
               "the desk on the RIGHT, plain empty wall on the LEFT, "
               "soft daylight from the left, slightly softer and "
               "calmer light than a bright midday, clear empty floor "
               "space in the CENTER where a person would stand in "
               "profile facing right toward the desk, calm ending "
               "mood, " + NOBANS,
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
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            .encode())
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
                path = os.path.join("ep22_bgs", f"{key}.png")
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
    os.makedirs("ep22_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
