#!/usr/bin/env python3
"""Episode 2 backgrounds: FLUX.2 Klein 4B via Cloudflare (account rotation).
Empty cinematic painted scenes (character is composited later, locally).
Output: ep2_bgs/<key>.png for each prompt below.
Env: CF account/token pairs 1..3 (repo secrets).
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

STYLE = ("cinematic painted illustration, moody film-still lighting, "
         "empty scene, no people, no characters, no text, no letters, "
         "no words, no watermark")

PROMPTS = {
    "s01": "dark bedroom at night, unmade bed with rumpled blanket and pillow, "
           "cold blue smartphone light glowing on the pillow, deep shadows, "
           "tense sleepless mood, vertical composition",
    "s02": "bedroom at grey dawn, unmade bed, pale morning light through a "
           "window with curtains, a smartphone lying on the pillow, quiet "
           "heavy mood, vertical composition",
    "s03": "very dark bedroom at night, bed in shadow, a huge ominous human "
           "shadow cast across the wall, threatening stillness, "
           "vertical composition",
    "s04": "dark bedroom close view of a bedside at night, harsh cold phone "
           "light spilling over the blanket, restless tense atmosphere, "
           "vertical composition",
    "s05": "smartphone on a dark wooden desk at night, colorful app icons "
           "glowing on its screen, one icon highlighted with a red glow, "
           "dramatic decision moment, close view, vertical composition",
    "s06a": "pair of jeans hanging on a chair in morning light, one front "
            "pocket turned inside out and empty, bright window light, "
            "vertical composition",
    "s06b": "smartphone lying on a wooden table showing a blank empty white "
            "home screen with no apps, soft morning light, calm but strange "
            "emptiness, vertical composition",
    "s07": "cozy armchair with an open book on it under a warm table lamp at "
           "night, quiet room, first page of reading, hopeful warmth, "
           "vertical composition",
    "s08a": "dark bedroom wall at night with a giant looming shadow "
            "silhouette leaning over a bed, menacing and still, deep blue "
            "darkness, vertical composition",
    "s08b": "nightstand in a dark bedroom, a closed book waiting under faint "
            "moonlight from a window, the room split between shadow and a "
            "thin line of light, vertical composition",
    "s09": "smartphone pushed to the far edge of a desk in dim light, an "
           "open book in warm lamp light at the center of the desk, clear "
           "choice made, vertical composition",
    "s10": "bright daytime room, an open book with a bookmark in its middle "
           "pages on a table, strong sunlight, sense of progress, "
           "vertical composition",
    "s11": "golden evening light in a calm room, armchair with an open book, "
           "a smartphone forgotten far away on a distant side table, "
           "peaceful warm hour, vertical composition",
    "s12a": "bright hopeful morning, a closed finished book resting on a "
            "table in warm sunlight, quiet satisfaction, vertical composition",
    "s12b": "wide bright morning room, a closed book and a dark switched-off "
            "smartphone side by side on a table, sun rays through the "
            "window, serene new beginning, vertical composition",
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
                path = os.path.join("ep2_bgs", f"{key}.png")
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
    os.makedirs("ep2_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
