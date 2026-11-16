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
         "no watermark, empty scene, no people, no characters, no text")

# Shared room description: one living room at night.
ROOM = ("the same living room at night, a wooden table and a chair, "
        "a wall clock on the wall, a door, dim lamplight, dark "
        "blue-grey night tones")
CLOCK = ("a wall clock with NO readable numbers, only plain short "
         "lines and dots for the hour marks, clock hands visible, "
         "no brand, no logo, no digits")
TABLESET = ("scattered papers, ONE single book and ONE single plain "
            "cold cup on the table, the papers and the book cover with "
            "no readable text and no writing, the cup with no writing "
            "and no logo and no steam, only one cup and only one book "
            "in the whole scene")

PROMPTS = {
    "shot-01": "vertical 9:16, " + ROOM + ", a door on the RIGHT side "
               "of the frame, the table and chair on the LEFT side of "
               "the frame with dim lamplight focused on the table, "
               + CLOCK + " on the wall behind the table, the room "
               "dark and quiet at midnight, clear empty floor space "
               "in the MIDDLE of the frame where a person would enter "
               "from the door and stand facing the table, no second "
               "chair, no readable text",
    "shot-02": "vertical 9:16, " + ROOM + ", close view of the back "
               "of the chair and the dark wall behind it, dim "
               "lamplight coming from the table side on the LEFT, "
               "large clear empty space in the MIDDLE of the frame "
               "where a person would sit leaning back in the chair, "
               "no readable text, no clock with numbers",
    "shot-03a": "vertical 9:16, " + ROOM + ", medium view of the "
                "table in the foreground, " + TABLESET + ", the chair "
                "behind the table, dim lamplight from the LEFT, clear "
                "empty space behind the table where a person would "
                "sit at the table with hands on the table beside the "
                "papers, no readable text, no second cup, no second "
                "book",
    "shot-03b": "vertical 9:16, " + ROOM + ", closer tighter view of "
                "the tabletop, " + TABLESET + ", the papers spread "
                "across the table, the book and the cold cup close to "
                "the camera, the top edge of the chair back barely "
                "visible at the top of the frame, dim lamplight from "
                "the LEFT, no readable text, no second cup, no second "
                "book",
    "shot-04": "vertical 9:16, " + ROOM + ", plain dark empty wall "
               "behind the chair, the table edge at the bottom of the "
               "frame, dim lamplight from the upper LEFT, large clear "
               "empty space in the MIDDLE of the frame where a person "
               "would sit at the table, focus on the torso, no "
               "readable text, no clock, no objects on the wall",
    "shot-05": "vertical 9:16, " + ROOM + ", very dark empty wall, "
               "only a faint dim lamplight wash on one side, large "
               "clear empty space in the MIDDLE of the frame where a "
               "person would sit close to the camera, no readable "
               "text, no numbers, no objects",
    "shot-06": "vertical 9:16, " + ROOM + ", wide view of the whole "
               "living room, a door on the LEFT side of the frame, "
               "the table and chair on the RIGHT side of the frame, "
               "a stack of papers on the table between the two sides, "
               + CLOCK + " on the wall behind the table, dim "
               "lamplight, clear empty floor space on the LEFT where "
               "a person would stand near the door and clear empty "
               "space on the RIGHT where a person would sit at the "
               "table, no readable text",
    "shot-07": "vertical 9:16, " + ROOM + ", dark wall behind the "
               "chair, dim lamplight from the RIGHT side of the frame "
               "falling on the chair, large clear empty space in the "
               "MIDDLE of the frame where a person would sit facing "
               "left, no readable text, no writing on the wall",
    "shot-08": "vertical 9:16, " + ROOM + ", the same living room, "
               "a person standing on the LEFT side and a person "
               "sitting at the table on the RIGHT side, distance "
               "between the two sides kept, the table and chair on "
               "the RIGHT, dim lamplight, clear empty floor space in "
               "the MIDDLE of the frame between the two sides, no "
               "readable text",
    "shot-09": "vertical 9:16, " + ROOM + ", the wall behind the "
               "chair with " + CLOCK + " high on the wall above the "
               "chair, the table in the foreground, dim lamplight, "
               "clear empty space behind the table where a person "
               "would sit at the table with the clock behind his "
               "head, no readable text, no brand on the clock",
    "shot-10": "vertical 9:16, " + ROOM + ", the table and the EMPTY "
               "chair in the foreground, warm lamplight shining on "
               "the empty chair, the chair clearly empty, dim "
               "lamplight in the rest of the room, clear empty floor "
               "space beside the chair where a person would stand "
               "looking at the chair, only one chair in the whole "
               "scene, no readable text",
    "shot-11": "vertical 9:16, " + ROOM + ", the door of the room at "
               "the far end of the frame on the LEFT side, a hallway "
               "wall beside the door, dim lamplight, clear empty "
               "floor space in the MIDDLE of the frame where a person "
               "would walk toward the door on the left, no readable "
               "text, no second door",
    "shot-12": "vertical 9:16, " + ROOM + ", the same table and "
               "chair, warm lamplight shining on the chair, the room "
               "empty and calm and quiet, dim warm light, clear empty "
               "space on the chair where a person would sit, only one "
               "chair in the whole scene, no readable text",
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
