#!/usr/bin/env python3
"""Episode 19 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (12 shots = 12 sentences).
Output: ep19_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.

Scene: one fixed home entryway, closed front door on the right,
one pair of waiting shoes by the door, cold dim hallway light from
the left (shots 01-06), warm bright light streaming in from behind
the door once it opens (shots 07-12). Lessons from ep16/ep17: the
word "silhouette"/"shadow" makes FLUX render a human figure — no
shadow language at all here; the shoes are the character's own and
he is sock-footed, so the prompt says ONE single pair only, plain
with no logo, and never a person wearing shoes. No readable text /
numbers / logos anywhere; no number or writing on the door.
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
    "shot-01": "vertical 9:16, dim home entryway hallway at dusk, cold "
               "faint light from the LEFT, a heavy CLOSED front door on "
               "the RIGHT side of the frame with ONE single round doorknob "
               "at shoulder height, ONE single pair of plain shoes waiting "
               "on the floor in front of the door at the bottom of the "
               "frame, the shoes plain with no readable logo and no text, "
               "dark grey-blue hallway walls, clear empty floor space in "
               "the MIDDLE of the frame where a person would stand facing "
               "the door, no second pair of shoes, no person, no readable "
               "text, no numbers",
    "shot-02": "vertical 9:16, closer view of the same dim home entryway, "
               "ONE single pair of plain shoes waiting on the floor in "
               "front of ONE single CLOSED front door at the bottom RIGHT "
               "of the frame, the shoes plain with no readable logo and no "
               "text, the closed door behind them is the ONLY door in the "
               "whole scene, no second door, no side door, no other doorway, "
               "no opening in any wall, cold faint hallway light from the "
               "LEFT, a person standing behind the shoes would be visible "
               "in the empty floor space in the MIDDLE of the frame, no "
               "second pair of shoes, no single extra shoe, no person "
               "wearing shoes, no readable text, no numbers",
    "shot-03": "vertical 9:16, wider view of the same dim home entryway "
               "hallway, a heavy CLOSED front door on the RIGHT side of "
               "the frame, the door FULLY CLOSED and flush inside its "
               "frame with no gap and not open at all, ONE single round "
               "doorknob on the door and only one knob in the whole image, "
               "no second knob, no knob on the other side of the door, a plain empty dark wall on the LEFT "
               "side of the frame, cold faint light from the LEFT, clear "
               "empty floor space in the MIDDLE of the frame where a person "
               "would stand facing the door, ONE single pair of plain shoes "
               "barely visible at the bottom edge in front of the door, "
               "no second pair of shoes, no person, no readable text, "
               "no numbers, no map, no drawn path",
    "shot-04": "vertical 9:16, the same dim home entryway, a person "
               "standing close to a heavy CLOSED front door on the RIGHT "
               "side of the frame, the door closed and still, cold faint "
               "hallway light from the LEFT, dark grey-blue walls, clear "
               "empty floor space in the MIDDLE of the frame where a "
               "person would stand facing the door, ONE single pair of "
               "plain shoes at the bottom edge in front of the door, no "
               "second pair of shoes, no person, no readable text, "
               "no numbers",
    "shot-05": "vertical 9:16, the same dim home entryway, a heavy CLOSED "
               "front door in the CENTER-RIGHT of the frame, the door "
               "closed and heavy, a person standing facing the door in the "
               "empty floor space in the MIDDLE of the frame, cold faint "
               "hallway light from the LEFT, plain dark wall on the LEFT, "
               "nothing new in the scene, ONE single pair of plain shoes "
               "at the bottom edge, no second pair of shoes, no person, "
               "no readable text, no numbers",
    "shot-06": "vertical 9:16, lower closer view of the same dim home "
               "entryway floor, the floor line clearly visible across the "
               "bottom of the frame, ONE single pair of plain shoes waiting "
               "at the bottom edge in front of a CLOSED front door on the "
               "RIGHT, the door closed, cold faint hallway light from the "
               "LEFT, clear empty floor space in the MIDDLE where a "
               "person's feet would stand planted on the floor, no second "
               "pair of shoes, no person, no readable text, no numbers",
    "shot-07": "vertical 9:16, the same home entryway, ONE single front "
               "door on the RIGHT side of the frame standing AJAR, opening "
               "inward, ONE single door panel only, ONE single round "
               "doorknob on it, warm bright golden light streaming in "
               "gently from behind the open door on the RIGHT, the hallway "
               "on the LEFT still dim and cold with a plain empty wall and "
               "no other door and no other doorway and no opening, the "
               "light spilling across the floor but not harsh, ONE single "
               "pair of plain shoes still waiting on the floor in front of "
               "the door, exactly two shoes and no third shoe and no single "
               "extra shoe anywhere, clear empty floor space in the MIDDLE "
               "where a person would stand facing the door, no second pair "
               "of shoes, no person, no readable text, no numbers",
    "shot-08": "vertical 9:16, the threshold of a front door, warm bright "
               "light coming from the RIGHT, from outside the open door, "
               "the hallway behind on the LEFT darker and dim, the open "
               "door edge visible on the RIGHT, clear empty floor space in "
               "the MIDDLE of the frame at the threshold where a person "
               "would take one step toward the light, ONE single pair of "
               "plain shoes left behind at the bottom LEFT edge, no second "
               "pair of shoes, no person, no readable text, no numbers",
    "shot-09": "vertical 9:16, just outside the threshold of an open front "
               "door, brighter warm daylight, the open door and the dim "
               "hallway behind on the LEFT side of the frame, open bright "
               "space on the RIGHT, clear empty ground in the MIDDLE of "
               "the frame where a person would walk toward the right, "
               "no shoes in the foreground, no person, no readable text, "
               "no numbers",
    "shot-10": "vertical 9:16, outside a front door in bright open "
               "daylight, the open door and the dim hallway far behind on "
               "the LEFT side of the frame, wide bright open space on the "
               "RIGHT, clear empty ground in the MIDDLE of the frame where "
               "a person would walk toward the right, no shoes in the "
               "foreground, no person, no readable text, no numbers",
    "shot-11": "vertical 9:16, outside a front door in bright daylight, "
               "the open front door with its doorknob on the LEFT side of "
               "the frame behind, bright open path stretching to the RIGHT, "
               "a person standing in the MIDDLE of the frame would face "
               "the bright path to the right, clear empty ground in the "
               "MIDDLE, no shoes in the foreground, no person, no readable "
               "text, no numbers",
    "shot-12": "vertical 9:16, wide bright open space outside a front "
               "door, the open door and the hallway very far behind on the "
               "LEFT side of the frame, small and distant, bright daylight "
               "and open sky feeling, clear empty ground in the MIDDLE of "
               "the frame where a person would walk toward the right, "
               "sense of walking away, no shoes in the foreground, no "
               "person, no readable text, no numbers",
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
                path = os.path.join("ep19_bgs", f"{key}.png")
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
    os.makedirs("ep19_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
