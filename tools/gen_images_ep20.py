#!/usr/bin/env python3
"""Episode 20 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (8 shots = 8 sentences).
Output: ep20_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.

Lessons from ep16/ep17 applied from the start: the word "silhouette" /
"shadow" makes FLUX render a human figure — no shadow language at all
here. The phone sits ON the desk explicitly; its screen is plain dark
and off. The paper list shows ONLY checkbox marks (empty squares with
diagonal ticks), never words/letters/numbers. No readable text /
numbers / logos anywhere. One room throughout: desk on the RIGHT,
kitchen counter with sink on the LEFT, daylight from the left.
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
    "shot-01": "vertical 9:16, a bright home room in daylight, seen "
               "from a LOW eye-level viewpoint, a simple wooden table "
               "desk on the RIGHT side of the frame with FOUR STRAIGHT LEGS, "
               "NO crossbar, NO stretcher bar between the legs, NO "
               "horizontal bar under the desk, just four plain legs with "
               "open space under the top, the desk top LOW in the frame "
               "with its front edge about two-thirds down the frame, ONE "
               "single phone lying flat ON the desk NEAR THE FRONT EDGE "
               "of the desk top, close to the viewer, the phone screen "
               "plain dark and off with no glow, no readable text, no "
               "icons, no numbers, the edge of a paper list beside the "
               "phone on the desk, the paper showing ONLY empty square "
               "checkbox marks with diagonal tick marks and blank "
               "horizontal lines, absolutely no letters, no words, no "
               "numbers, no handwriting, no scribbles, no marks beside "
               "the lines, soft daylight coming from a window on the "
               "LEFT outside the frame, plain empty wall, clear empty "
               "floor space in the MIDDLE of the frame where a person "
               "would stand facing the desk, no second phone, no person "
               "holding a phone",
    "shot-02": "vertical 9:16, the same bright home room in daylight, "
               "seen from a LOW eye-level viewpoint, the same simple "
               "wooden table desk on the RIGHT side of the frame with "
               "FOUR STRAIGHT LEGS, NO crossbar, NO stretcher bar between "
               "the legs, NO horizontal bar under the desk, just four "
               "plain legs with open space under the top, the desk top LOW "
               "in the frame with its front edge about two-thirds down "
               "the frame, ONE single phone lying flat ON the desk NEAR "
               "THE FRONT EDGE of the desk top, close to the viewer, the "
               "phone screen plain dark and off, no readable text, no "
               "icons, no numbers, the edge of a paper list beside the "
               "phone, the paper showing ONLY empty square checkbox "
               "marks with diagonal tick marks and blank horizontal "
               "lines, absolutely no letters, no words, no numbers, no "
               "handwriting, no scribbles, no marks beside the lines, "
               "soft daylight from a window on the LEFT outside the "
               "frame, plain empty wall, clear empty floor space in the "
               "MIDDLE of the frame where a person would stand facing "
               "the desk, no second phone, no person",
    "shot-03": "vertical 9:16, a bright home room in daylight, a wooden "
               "desk occupying ONLY the RIGHT HALF of the frame, a paper "
               "list lying on the desk showing ONLY empty square checkbox "
               "marks with diagonal tick marks and blank horizontal "
               "lines, absolutely no letters, no words, no numbers, no "
               "handwriting, no scribbles, no marks beside the lines on "
               "the paper, ONE single phone lying flat beside the paper, "
               "the phone screen plain dark and off, no readable text, "
               "no icons, clear empty floor space on the LEFT HALF of "
               "the frame where a person would stand on the floor beside "
               "the desk leaning over the list, plain empty wall behind "
               "the desk, soft daylight from the left, no second phone, "
               "no second list, no person",
    "shot-04": "vertical 9:16, wide view of a bright home room in "
               "daylight, a wooden desk on the FAR RIGHT side of the "
               "frame with EXACTLY ONE single phone lying flat ON it and "
               "no other phone anywhere in the frame, only one phone in "
               "the whole scene, never two phones, a kitchen counter "
               "with a sink on the FAR LEFT side of the frame, the sink "
               "empty and clean with no dishes piled up, no readable "
               "labels, plain empty wall, large clear empty floor space "
               "in the MIDDLE of the room where a person would walk from "
               "right to left, soft daylight from the left, no person, "
               "no readable text",
    "shot-05": "vertical 9:16, the same bright home room in daylight, "
               "a kitchen counter with a sink on the LEFT side of the "
               "frame, the sink empty and clean, a wooden desk on the "
               "RIGHT side of the frame with ONE single phone lying flat "
               "ON it and a paper list beside it, the paper showing ONLY "
               "empty square checkbox marks with diagonal tick marks and "
               "blank horizontal lines, absolutely no letters, no words, "
               "no numbers, no handwriting, no scribbles, no marks beside "
               "the lines, soft daylight from the "
               "left, plain empty wall, clear empty floor space in the "
               "MIDDLE of the frame where a person would stand facing "
               "right toward the desk, no second phone, no person, no "
               "readable text",
    "shot-06": "vertical 9:16, the same bright home room in daylight, "
               "a kitchen counter with a sink on the LEFT side of the "
               "frame, the sink empty and clean, a wooden desk on the "
               "RIGHT side of the frame with ONE single phone lying flat "
               "ON it and a paper list beside it, the paper showing ONLY "
               "checkbox marks with no words, soft daylight from the "
               "left, plain empty wall, clear empty floor space in the "
               "MIDDLE of the frame where a person would stand facing "
               "right toward the desk, no second phone, no person, no "
               "readable text",
    "shot-07": "vertical 9:16, the same bright home room in daylight, "
               "a wooden desk on the RIGHT side of the frame with FOUR "
               "LEGS and OPEN SPACE under the desk top, no solid front "
               "panel, no modesty panel, the floor clearly visible "
               "under the desk, ONE single phone lying flat ON the desk "
               "and a paper list beside it, the paper showing ONLY "
               "empty square checkbox marks with diagonal tick marks and "
               "blank horizontal lines, absolutely no letters, no words, "
               "no numbers, no handwriting, no scribbles, no marks beside "
               "the lines, a kitchen counter with a "
               "sink visible in the background on the LEFT, the sink "
               "empty and clean, soft daylight from the left, plain "
               "empty wall, clear empty floor space in front of the "
               "desk where a person would sit on a chair, no second "
               "phone, no person, no readable text",
    "shot-08": "vertical 9:16, the same bright home room in the "
               "MORNING, warm golden morning light coming from a window "
               "on the LEFT, seen from a LOW eye-level viewpoint, a "
               "simple wooden table desk on the RIGHT side of the frame "
               "with FOUR LEGS and open space under the top, no solid "
               "front panel, the desk top LOW in the frame with its "
               "front edge about two-thirds down the frame, ONE single "
               "phone lying flat ON the desk NEAR THE FRONT EDGE of the "
               "desk top, close to the viewer, the phone screen plain "
               "dark and off, no readable text, a "
               "paper list lying on the desk to the RIGHT of the phone, "
               "completely separate from the phone, not touching it, not "
               "overlapping it, the paper showing ONLY empty square "
               "checkbox marks with one empty square at the TOP of the "
               "list and blank horizontal lines, absolutely no letters, "
               "no words, no numbers, no handwriting, no scribbles, no "
               "marks beside the lines on the paper, plain "
               "empty wall, clear empty floor space in the MIDDLE of the "
               "frame where a person would stand facing the desk, no "
               "second phone, no person",
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
                path = os.path.join("ep20_bgs", f"{key}.png")
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
    os.makedirs("ep20_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
