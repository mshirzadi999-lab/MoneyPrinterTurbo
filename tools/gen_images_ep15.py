#!/usr/bin/env python3
"""Episode 15 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). Nine distinct scenes mapped to 18 shots (same-scene
shots share one background by design: the calendar wall must stay
identical across shots 1/2/3, and shot 18 MUST be identical to shot 1
for the loop; split-frame and desk shots share their scene, framing
differences are zooms in the edit).
Output: ep15_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.
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
    # Shots 01, 02, 03, 18 (loop: 18 identical to 01).
    "wall-calendar": "vertical 9:16, interior wall of a study room in "
                     "warm soft morning light from a window on the right, "
                     "a large wall calendar on the wall with a grid of "
                     "empty blank squares, twelve of the squares marked "
                     "with simple green check marks and no red square, "
                     "absolutely no numbers, no dates, no text, no "
                     "letters, no words, plain empty wall space above and "
                     "below the calendar, clear empty floor at the bottom "
                     "of the frame, quiet proud mood of a completed "
                     "chain, no people, no furniture",
    # Shot 04.
    "couch-night": "vertical 9:16, living room at night, a plain couch "
                   "in the center of the frame with one cushion, a dim "
                   "bedside lamp glowing faint warm light on the left, a "
                   "dark window in the background, one single smartphone "
                   "lying on the couch cushion with a dark blank screen "
                   "showing only a faint reflection and no readable text, "
                   "empty seat space on the couch for a seated person, "
                   "deep blue-grey night palette, tired quiet mood, no "
                   "people, no book, no second phone",
    # Shot 05 (lamp dimming to darkness).
    "couch-dark": "vertical 9:16, living room at night growing darker, "
                  "the same plain couch in the center of the frame with "
                  "one cushion, the bedside lamp fading to near darkness, "
                  "very dim cold light, one single smartphone lying on "
                  "the couch cushion with a dark blank screen, empty "
                  "seat space on the couch, deep dark blue-grey palette, "
                  "heavy sleepy mood of giving in, no people, no book, "
                  "no second phone",
    # Shot 06.
    "couch-morning": "vertical 9:16, living room in warm morning light, "
                     "a plain couch in the center of the frame with one "
                     "cushion, soft golden sunlight from a window, one "
                     "single smartphone lying on the couch cushion with a "
                     "dark blank screen, empty seat space on the couch "
                     "for a seated person, warm bright palette, sleepy "
                     "morning mood, no people, no book, no second phone",
    # Shot 07 (calendar with one red square behind the couch).
    "couch-calendar": "vertical 9:16, medium shot of a living room in "
                      "warm morning light, a plain couch in the lower "
                      "half of the frame with one cushion, one single "
                      "smartphone lying on the couch cushion with a "
                      "softly glowing blank screen showing no readable "
                      "text, a large wall calendar on the wall behind "
                      "the couch with a grid of empty blank squares, "
                      "most squares marked with simple green check marks "
                      "and exactly one square in the middle marked with "
                      "a solid red square, absolutely no numbers, no "
                      "dates, no text, no letters, empty seat space on "
                      "the couch, warm morning palette, sudden waking "
                      "mood, no people, no book, no second phone",
    # Shots 08, 09, 10, 16, 17 (split frame; framing differs in edit).
    "split-frame": "vertical 9:16, interior wall split vertically down "
                   "the exact middle by one thin vertical line of soft "
                   "light, the left half of the frame in cold dim "
                   "blue-grey light, the right half in warm bright "
                   "morning light, plain neutral wall in both halves, a "
                   "small wooden side table in the left half holding one "
                   "single smartphone with a dark blank screen, empty "
                   "floor space in both halves for standing people, no "
                   "people, no text, no numbers, no letters, no labels",
    # Shots 11, 12, 13.
    "desk-morning": "vertical 9:16, study desk in warm morning light, "
                    "the desktop edge runs nearly horizontal across the "
                    "lower half of the frame, an open book with "
                    "completely blank pages on the desk, one plain "
                    "coffee cup on the desk, one single smartphone on "
                    "the desk with a softly glowing blank screen showing "
                    "no readable text, a large wall calendar on the wall "
                    "behind the desk with a grid of empty blank squares, "
                    "most squares marked with simple green check marks "
                    "and exactly one square marked with a solid red "
                    "square, absolutely no numbers, no dates, no text, "
                    "no letters, empty space behind the desk for a "
                    "seated person, warm morning palette, no people, no "
                    "second phone, no second cup",
    # Shot 14 (another day: brighter, fresh book, fresh ticks, no red).
    "desk-newday": "vertical 9:16, study desk on another brighter "
                   "morning, clear bright morning light from a window, "
                   "the desktop edge runs nearly horizontal across the "
                   "lower half of the frame, a fresh open book with "
                   "completely blank pages on the desk, one plain "
                   "coffee cup on the desk, one single smartphone on the "
                   "desk with a softly glowing blank screen showing no "
                   "readable text, a large wall calendar on the wall "
                   "behind the desk with a grid of empty blank squares "
                   "marked with many fresh simple green check marks and "
                   "no red square, absolutely no numbers, no dates, no "
                   "text, no letters, empty space behind the desk for a "
                   "seated person, bright hopeful palette, no people, "
                   "no second phone, no second cup",
    # Shot 15 (day, ordinary light, calendar unchanged with red square).
    "couch-day": "vertical 9:16, living room in ordinary plain "
                 "daylight, a plain couch in the center of the frame "
                 "with one cushion, neutral daylight from a window, one "
                 "single smartphone lying on the couch cushion with a "
                 "dark blank screen, a large wall calendar on the wall "
                 "behind the couch with a grid of empty blank squares "
                 "marked with green check marks and exactly one square "
                 "marked with a solid red square, absolutely no numbers, "
                 "no dates, no text, no letters, empty seat space on "
                 "the couch, calm ordinary daytime palette, stillness "
                 "of someone who has not moved, no people, no book, no "
                 "second phone",
}

# Shot file -> background key (18 shots, 9 generations).
SHOT_MAP = {
    "shot-01": "wall-calendar", "shot-02": "wall-calendar",
    "shot-03": "wall-calendar", "shot-04": "couch-night",
    "shot-05": "couch-dark", "shot-06": "couch-morning",
    "shot-07": "couch-calendar", "shot-08": "split-frame",
    "shot-09": "split-frame", "shot-10": "split-frame",
    "shot-11": "desk-morning", "shot-12": "desk-morning",
    "shot-13": "desk-morning", "shot-14": "desk-newday",
    "shot-15": "couch-day", "shot-16": "split-frame",
    "shot-17": "split-frame", "shot-18": "wall-calendar",
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
                path = os.path.join("ep15_bgs", f"{key}.png")
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
    os.makedirs("ep15_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
