#!/usr/bin/env python3
"""Episode 18 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). 13 backgrounds for 13 shots (shot 3 splits into
03a + 03b). Output: ep18_bgs/<key>.png. Env: CF account/token pairs
1..3. ONLY=keys.

Setting (all shots): ONE living room at night — table + chair +
wall clock + door; dim lamp light; warm lamp light on the empty
chair (shot 10) and on the hero (shot 12). Same STYLE string as
ep17 (hand-painted cinematic matte painting, no text/numbers/people).

Per-shot musts from directing-fa.md: clock with NO readable numbers
(lines/dots only); papers + ONE book + ONE cold cup on the table
(no readable text on papers/book, no steam, no writing on cup);
door visible for shots 1 and 11; empty chair warm-lit for shot 10;
NO people in any background (character is composited locally later).

Lessons carried over: never describe a shadow/silhouette as a
figure (ep16/17 — "silhouette" renders a human); the cup only stays
plain when the prompt says no writing and no logo; objects only stay
ON furniture when the prompt says they lie/sit ON it.
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
         "no watermark, no signature, no scribble, empty scene, no people, no characters, no text")

# Shared room description: one living room at night. NOTE: no clock
# and no door in ROOM — FLUX renders a numbered clock and extra doors
# from any mention, so clock/door are added explicitly only where the
# directing needs them (01: clock+door; 06: door; 09: clock; 11: door).
ROOM = ("the same living room at night, a wooden table and a chair, "
        "dim lamplight, dark blue-grey night tones")
CLOCK = ("a wall clock with NO readable numbers, only plain short "
         "lines and dots for the hour marks, clock hands visible, "
         "no brand, no logo, no digits")
TABLESET = ("scattered papers, ONE single book and ONE single plain "
            "cold cup on the table, the papers and the book cover with "
            "no readable text and no writing, the cup with no writing "
            "and no logo and no steam, only one cup and only one book "
            "in the whole scene")

NOPEOPLE = ("absolutely no person, no head, no hair, no face, no "
            "shoulders, no back of a person, no silhouette of a "
            "person, nobody sitting or standing anywhere")

# FLUX ignores "seen from the side" for chairs (v2 drew front-facing
# chairs twice); describe the side-profile SHAPE instead: tall
# vertical back slat on one side, horizontal seat plank extending
# to the other side.
SIDECHAIR_L = ("a wooden chair in side profile, its back a tall "
                "vertical slat on the LEFT, its seat a horizontal "
                "plank extending to the RIGHT")
SIDECHAIR_R = ("a wooden chair in side profile, its back a tall "
                "vertical slat on the RIGHT, its seat a horizontal "
                "plank extending to the LEFT")

PROMPTS = {
    "shot-01": "vertical 9:16, " + ROOM + ", a door on the RIGHT side "
               "of the frame, the table and chair on the LEFT side of "
               "the frame with dim lamplight focused on the table, "
               + CLOCK + " on the wall behind the table, the room "
               "dark and quiet at midnight, clear empty floor space "
               "in the MIDDLE of the frame where a person would enter "
               "from the door and stand facing the table, no second "
               "chair, no readable text",
    "shot-02": "vertical 9:16, " + ROOM + ", medium close view, a "
               "wooden table on the LEFT with a dim lamp on it, "
               + SIDECHAIR_L + ", at the near end of the table, the "
               "chair completely empty, dark wall behind the chair, "
               "dim lamplight from the LEFT, large clear empty space "
               "in the MIDDLE of the frame where a person would sit "
               "leaning back in the chair, no clock on the wall, no "
               "door, no readable text, " + NOPEOPLE,
    "shot-03a": "vertical 9:16, " + ROOM + ", medium view of the "
                "table in the foreground, " + TABLESET + ", the papers "
                "completely blank white paper with only faint grey "
                "horizontal lines, no words, no letters, no headings, "
                + SIDECHAIR_R + ", at the far end of the table, the "
                "chair completely empty, dim lamplight from the LEFT, "
                "clear empty space behind the table where a person "
                "would sit at the table with hands on the table "
                "beside the papers, no hand, no fingers, no arm, no "
                "part of a person on the table, no clock on the wall, "
                "no second cup, no second book, " + NOPEOPLE,
    "shot-03b": "vertical 9:16, close-up view looking down at a wooden "
                "tabletop filling the whole frame, scattered papers, "
                "ONE single book only and ONE single plain cold cup "
                "on the table, only one book in the whole scene, no "
                "second book, the papers blank with only faint grey "
                "lines, no readable words, no letters, the book cover "
                "plain with no writing, the cup with no writing and "
                "no logo and no steam, the book and the cold cup "
                "close to the camera, the top edge of the empty "
                "chair back barely visible at the very top edge of "
                "the frame, dim lamplight from the LEFT, no wall, no "
                "clock, no door, no sofa, no second cup, " + NOPEOPLE,
    "shot-04": "vertical 9:16, a plain dark empty wall filling the "
               "frame, the edge of a wooden table at the very bottom "
               "of the frame, dim lamplight from the upper LEFT, "
               "large clear empty space in the MIDDLE of the frame "
               "where a person would sit at the table, focus on the "
               "torso, no chair, no clock, no door, no objects on "
               "the wall, no readable text, " + NOPEOPLE,
    "shot-05": "vertical 9:16, a very dark empty wall filling the "
               "whole frame, only a faint dim lamplight wash on one "
               "side, large clear empty space in the MIDDLE of the "
               "frame where a person would sit close to the camera, "
               "no clock, no door, no table, no chairs, no readable "
               "text, no numbers, no objects, " + NOPEOPLE,
    "shot-06": "vertical 9:16, " + ROOM + ", wide view of the whole "
               "living room, a door on the LEFT side of the frame, "
               "the table on the RIGHT side of the frame with a stack "
               "of papers on it, " + SIDECHAIR_R + ", at the right "
               "end of the table, only ONE single chair in the whole "
               "scene, no second chair, no clock on the wall, dim "
               "lamplight, clear empty floor space on the LEFT where "
               "a person would stand near the door and clear empty "
               "space on the RIGHT where a person would sit at the "
               "table, no readable text, " + NOPEOPLE,
    "shot-07": "vertical 9:16, " + ROOM + ", " + SIDECHAIR_L + ", "
               "standing against a dark wall, the chair completely "
               "empty, dim lamplight from the RIGHT side of the "
               "frame falling on the chair, large clear empty space "
               "in the MIDDLE of the frame where a person would sit "
               "facing left, no clock on the wall, no door, no table, "
               "no second chair, no readable text, no signature, no "
               "scribble, " + NOPEOPLE,
    "shot-08": "vertical 9:16, " + ROOM + ", the same living room, "
               "the table on the RIGHT side of the frame, "
               + SIDECHAIR_R + ", at the right end of the table, "
               "only ONE single chair in the whole scene, dim "
               "lamplight, clear empty floor space on the LEFT and in "
               "the MIDDLE of the frame where a person would stand "
               "and where a person would sit at the table, no clock "
               "on the wall, no door, no window, no sofa, no curtains, "
               "no floor lamp, no second chair, no readable text, "
               + NOPEOPLE,
    "shot-09": "vertical 9:16, " + ROOM + ", the wall behind the "
               "chair with ONE single wall clock high on the wall, "
               "the clock face plain white with only twelve short "
               "thin tick marks and two hands, completely blank "
               "otherwise, no digits, no numbers, no Roman numerals, "
               "no brand, no logo, a wooden chair seen from the side "
               "at the table, its back on the LEFT and its seat "
               "extending to the RIGHT, the chair completely empty, "
               "the table in the foreground, dim lamplight, clear "
               "empty space behind the table where a person would sit "
               "at the table with the clock behind his head, only "
               "one clock and only one chair, no readable text, "
               + NOPEOPLE,
    "shot-10": "vertical 9:16, " + ROOM + ", the table and the EMPTY "
               "chair in the foreground, warm lamplight shining on "
               "the empty chair, the chair clearly empty, the chair "
               "seen from the side with its back on the RIGHT and "
               "its seat extending to the LEFT, dim lamplight in the "
               "rest of the room, clear empty floor space beside the "
               "chair where a person would stand looking at the "
               "chair, only one chair in the whole scene, no clock "
               "on the wall, no door, no readable text, " + NOPEOPLE,
    "shot-11": "vertical 9:16, " + ROOM + ", the door of the room at "
               "the far end of the frame on the LEFT side, slightly "
               "open with warm light from the hallway behind it, a "
               "plain hallway wall beside the door, dim lamplight, "
               "clear empty floor space in the MIDDLE of the frame "
               "where a person would walk toward the door on the "
               "left, no table, no chairs, no clock, no readable "
               "text, no second door, " + NOPEOPLE,
    "shot-12": "vertical 9:16, " + ROOM + ", the same table and "
               "chair, warm lamplight shining on the chair, the room "
               "empty and calm and quiet, dim warm light, clear empty "
               "space on the chair where a person would sit, only one "
               "chair in the whole scene, no clock on the wall, no "
               "readable text, " + NOPEOPLE,
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
                path = os.path.join("ep18_bgs", f"{key}.png")
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
    os.makedirs("ep18_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
