#!/usr/bin/env python3
"""Episode 16 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (13 shots = 13 sentences).
Output: ep16_bgs/<key>.png. Env: CF account/token pairs 1..3.
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
    "shot-01": "vertical 9:16, dark room at night, a wooden desk on the "
               "RIGHT side of the frame with one single open laptop, the "
               "laptop screen glowing cold blue light with only vague "
               "blurry lines and no readable text, one single small "
               "glowing dot on the screen meaning unread, no digit, a "
               "small window on the LEFT leaking faint cold moonlight, "
               "dark blue-grey room, clear empty floor space behind the "
               "desk where a person would stand, no laptop anywhere "
               "else, no second laptop",
    "shot-02": "vertical 9:16, medium close view of the same dark room "
               "at night, one single open laptop on a wooden desk with "
               "its screen glowing cold blue light, only vague blurry "
               "lines on the screen and no readable text, one single "
               "small glowing dot on the screen clearly visible, no "
               "digit, darkness of the room all around the desk, clear "
               "empty space on the LEFT side of the frame where a person "
               "would stand, no second laptop, no biscuit",
    "shot-03": "vertical 9:16, wider view of a dark room at night, one "
               "single open laptop on a desk in the background with its "
               "cold blue screen light, a plain empty wall and a dark "
               "floor, feeling of walking past the desk, large clear "
               "empty space in the middle of the room where a person "
               "would walk, no second laptop, no readable text",
    "shot-04": "vertical 9:16, dark room at night, one single open "
               "laptop on a wooden desk on the LEFT side of the frame "
               "with cold blue screen light, in the CENTER of the frame "
               "a tall formless black smudge rising from the floor in "
               "front of the laptop screen, like a blot of black ink or "
               "a column of dark smoke, ragged uneven top edge, wider at "
               "the bottom, cold screen light shining from behind the "
               "dark mass, the dark mass has no face, no head, no arms, "
               "no legs, no feet, no human outline, no body shape, never "
               "a person, never a human figure, not a silhouette of a "
               "person, clear empty space on the RIGHT side of the frame "
               "where a person would stand, no readable text, no second "
               "laptop",
    "shot-05": "vertical 9:16, closer view of a dark room at night, a "
               "wooden desk with one single open laptop with dim cold "
               "blue screen light, plain blank blue glow on the screen "
               "with no lines and no browser bars, and only one single "
               "biscuit on the desk, only one biscuit in the whole "
               "scene, a faint small dark smudge on the far back wall "
               "off-center, flat on the wall like a stain, no head, no "
               "body, no limbs, no human outline, clear empty space "
               "beside the desk where a person would stand, no second "
               "biscuit, no readable text, no second laptop",
    "shot-06": "vertical 9:16, wide view of a dark room at night, a "
               "wooden desk with one single small open laptop on it, the "
               "laptop screen giving a small dim cold blue light, half "
               "of the back wall covered by a huge flat black stain like "
               "spilled ink spreading across the wall, ragged edges, the "
               "black stain has no face, no head, no body, no arms, no "
               "legs, no human outline, never a person, never a human "
               "figure, not a silhouette of a person, clear empty space "
               "in the foreground on the RIGHT side where a person would "
               "stand, no readable text, no second laptop",
    "shot-07": "vertical 9:16, the same dark room at night, darker than "
               "before, a wooden desk with one single open laptop on it, "
               "the laptop screen giving a dim cold blue light that is "
               "still present and glowing, never fully off, dark washes "
               "and flat black stains spreading across the walls of the "
               "room, the stains have no face, no head, no body, no "
               "human outline, never a person, clear empty space in the "
               "middle of the room where a person would stand, no "
               "readable text, no second laptop",
    "shot-08": "vertical 9:16, dim blue-grey room at night, a wooden "
               "desk with one single open laptop on it, the laptop "
               "screen glowing cold blue light, in the CENTER of the "
               "frame a tall formless black smudge standing on the floor "
               "in front of the laptop, like a column of dark smoke or a "
               "blot of black ink, ragged edges, the black smudge has no "
               "face, no head, no arms, no legs, no feet, no human "
               "outline, no body shape, never a person, never a human "
               "figure, not a silhouette of a person, clear empty space "
               "on the RIGHT side of the frame where a person would "
               "stand facing the darkness, no readable text, no second "
               "laptop",
    "shot-09": "vertical 9:16, the same dim blue-grey room at night as "
               "the previous shot, a wooden desk with one single open "
               "laptop on it, the laptop screen glowing cold blue light, "
               "a small formless black smudge still present in the frame "
               "but further back and smaller, flat on the back wall like "
               "an ink stain, distant from the laptop, the black smudge "
               "has no face, no head, no body, no limbs, no human "
               "outline, never a person, never a human figure, clear "
               "empty space in the foreground where a person would stand "
               "facing it, no readable text, no second laptop",
    "shot-10": "vertical 9:16, wide view of a dark room at night, a "
               "wooden desk with one single open laptop on it, the "
               "laptop screen glowing cold blue light, a small low black "
               "smudge on the floor near the far corner on the RIGHT "
               "side of the frame, flat on the floor like spilled ink, "
               "small and low, the black smudge has no head, no limbs, "
               "no claws, no creature shape, no human outline, never a "
               "person, never an animal, clear empty space on the LEFT "
               "side of the frame where a person would stand, no "
               "readable text, no second laptop",
    "shot-11": "vertical 9:16, medium shot beside a wooden desk in a "
               "dark room at night, a chair behind the desk with clear "
               "empty space on the seat where a seated person would sit, "
               "one single open laptop on the desk with a vague blue "
               "screen glow and no readable text, one small dark spot in "
               "the far corner of the room, no biscuit anywhere, no "
               "second laptop, no readable text",
    "shot-12": "vertical 9:16, wide view of a room at night, cold clean "
               "WHITE screen light from one single open laptop flooding "
               "the whole room with bright white light, the room bright "
               "and clean, the shadow completely gone except one small "
               "dark spot in the far corner of the room, large clear "
               "empty space in front of the laptop where a person would "
               "sit, no darkness in the corners except the one small "
               "spot, no readable text, no second laptop, night scene, "
               "not daylight",
    "shot-13": "vertical 9:16, the same room at night, the whole room "
               "BRIGHT WHITE, pale white walls and pale floor washed in "
               "bright white light from the laptop screen, a bright "
               "white room, no dark areas, no door, no doorway, no dark "
               "opening anywhere, one single open laptop on a wooden "
               "desk with a plain white screen, the laptop never "
               "closed, the white screen glowing, one small dark spot "
               "still in the far corner of the room, the same night, "
               "NOT daylight, no window daylight, no sun, clear empty "
               "space beside the desk where a seated person would sit, "
               "no readable text, no second laptop",
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
                path = os.path.join("ep16_bgs", f"{key}.png")
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
    os.makedirs("ep16_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
