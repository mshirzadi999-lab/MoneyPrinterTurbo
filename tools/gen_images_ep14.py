#!/usr/bin/env python3
"""Episode 14 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (12 shots = 12 sentences).
Output: ep14_bgs/<key>.png. Env: CF account/token pairs 1..3.
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
    "shot-01": "vertical 9:16, very dark bedroom at night, a low bed "
               "with a rumpled dark blanket in the center of the frame, "
               "mattress top low near knee height, a plain wooden "
               "nightstand and a bare empty wall behind the bed, a small "
               "window on the left leaking very faint cold moonlight, "
               "deep blue-grey darkness, quiet sudden-waking mood, clear "
               "empty floor space in front of the bed, no phone, no "
               "clock, no readable numbers",
    "shot-02": "vertical 9:16, dark hallway of a house at night, bare "
               "empty wall and dark wooden floor, one long stretched "
               "human-shaped shadow cast across the wall behind, shadow "
               "only, no face and no second body, no lit door, no wall "
               "writing, cold dim light, tense feeling of being followed",
    "shot-03": "vertical 9:16, exterior of a small house at night seen "
               "from the yard at eye level, every window glowing warm "
               "amber light, dark foggy night sky, small empty yard in "
               "the foreground with bare ground, exaggerated scale of the "
               "glowing house against the dark night, quiet ominous mood, "
               "no car, no logo",
    "shot-04": "vertical 9:16, interior of a warmly lit room at night, "
               "a wooden desk with crumpled blank papers with no writing "
               "and a cold cup of tea, harsh ceiling lamp light from "
               "above, in the corner a bed with messy rumpled sheets, "
               "warm amber and shadow palette, exhausted trapped mood, "
               "no phone, no clock with hands",
    "shot-05": "vertical 9:16, dark bedroom at night, an unmade bed "
               "with a dark blanket, a wooden nightstand beside the bed "
               "holding one single smartphone with a softly glowing "
               "blank blue screen showing no readable text and no chat, "
               "warm amber light spilling through a half-open door on "
               "the right side of the frame, the door light falling on "
               "the floor, not on the bed, dark blue-grey palette, only "
               "one phone in the whole scene",
    "shot-06": "vertical 9:16, hallway of a house at midnight, a second "
               "wooden door on the right with cold blue light spilling "
               "through its gap, bare empty wall and dark floor, the blue "
               "light clearly different from warm light, only the light "
               "is visible, the room interior behind the door is not "
               "visible, quiet tense mood, no phone",
    "shot-07": "vertical 9:16, living room at midnight, dark wooden "
               "floor, two tall standing floor lamps in the background, "
               "one lamp glowing warm amber and the other lamp unlit and "
               "dark, a plain wall light switch on the wall between the "
               "two lamps, dim moody light, calm analytical mood, no "
               "phone",
    "shot-08": "vertical 9:16, the same dim living room at night, focus "
               "on long tall shadows cast by one warm lamp across a plain "
               "matte grey wall, sparse empty frame, dark wooden floor at "
               "the bottom, quiet oppressive stillness, no decorative "
               "objects, no smoke, no mist",
    "shot-09": "vertical 9:16, corner of a study desk in darkness at "
               "night, a few books with completely blank covers and no "
               "titles blurred in the background, absolute darkness "
               "around the desk, one small pool of soft light on the desk "
               "surface, feeling of stopping and stillness, no phone, no "
               "notebook",
    "shot-10": "vertical 9:16, study desk seen from the side at night, "
               "the wooden desk occupies the right two-thirds of the "
               "frame with one single open notebook with blank pages "
               "showing only faint blank lines and no readable writing "
               "and one single plain pen lying on the notebook, one "
               "single small study lamp with a green glass shade casting "
               "a focused pool of warm light on the notebook, the left "
               "third of the frame is empty dark space for a seated "
               "person, darkness around the desk, only one pen and only "
               "one lamp in the whole scene, no phone, no second lamp",
    "shot-11": "vertical 9:16, wider view of a living room at night, the "
               "main warm light fading away into darkness, colors sinking "
               "toward black and grey, a plain wall light switch visible "
               "on the wall, quiet ending mood, dim and empty, no new "
               "light source",
    "shot-12": "vertical 9:16, dark bedroom at night, a bed in the "
               "center of the frame with a pillow and dark blanket, a "
               "window showing the night sky and a faint dim moon, "
               "absolutely no light coming from inside the house, deep "
               "dark blue-grey palette, peaceful sleep mood, no phone, "
               "no notebook, no bright stars",
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
                path = os.path.join("ep14_bgs", f"{key}.png")
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
    os.makedirs("ep14_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
