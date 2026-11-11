#!/usr/bin/env python3
"""Episode 3 backgrounds: FLUX.2 Klein 4B via Cloudflare (account rotation).
Empty cinematic painted scenes (character is composited later, locally).
Prompts are taken verbatim from ~/workspace/episode3/sequence-plan.md.
Output: ep3_bgs/<key>.png for each prompt below.
Env: CF account/token pairs 1..3 (repo secrets). ONLY = comma keys.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

STYLE = ("cinematic painted illustration, film-still lighting, "
         "no letters, no words, no numbers, no watermark")

PROMPTS = {
    "s01": "cinematic digital painting, vertical 9:16, small dim bedroom "
           "before dawn, unmade bed with rumpled blanket, wooden chair, "
           "window with closed blinds leaking cold grey light, heavy still "
           "air, muted grey-blue palette, oppressive quiet mood, empty "
           "scene, no people, no text",
    "s02": "cinematic digital painting, vertical 9:16, tall window taking "
           "most of the frame, endless flat overcast grey sky outside, no "
           "sun, no clouds movement, faint condensation on glass, cold "
           "desaturated light, sense of a day that will never change, empty "
           "scene, no people, no text",
    "s03": "cinematic digital painting, vertical 9:16, corner of the same "
           "grey bedroom in flat morning light, simple wooden chair beside "
           "a plain wall, round wall clock with a completely blank white "
           "face, only two simple black hands and short plain tick marks, "
           "absolutely no numerals, no digits, no letters, no brand marks "
           "anywhere in the image, still and lifeless air, muted grey "
           "palette, everyday repetitive mood, empty scene, no people, "
           "no text",
    "s04": "cinematic digital painting, vertical 9:16, worn armchair in a "
           "dark corner of a room, deep shadows, a folded blanket over one "
           "armrest, single weak grey light from the side, heavy exhausting "
           "atmosphere, empty scene, no people, no text",
    "s05a": "cinematic digital painting, vertical 9:16, window with fogged "
            "glass looking onto a grey street, blurred rooftops in mist, "
            "waiting and longing mood, cold grey tones, empty scene, no "
            "people, no text",
    "s05b": "cinematic digital painting, vertical 9:16, the same room "
            "transformed in a dream, soft pale golden sunlight flooding "
            "in, dust motes floating in light beams, airy and weightless "
            "feeling, washed-out dreamy brightness, gentle and unreal, "
            "empty scene, no people, no text",
    "s06": "cinematic digital painting, vertical 9:16, the same fogged "
           "window as before but darker, rain streaks running down the "
           "glass, grey street beyond, light drained away, quiet "
           "disappointment, cold palette, empty scene, no people, no text",
    "s07a": "cinematic digital painting, vertical 9:16, long plain interior "
            "wall with a row of identical windows repeating into the "
            "distance, exaggerated repetition, flat grey light in every "
            "window, monotonous loop feeling, empty scene, no people, "
            "no text",
    "s07b": "cinematic digital painting, vertical 9:16, bed in a dim grey "
            "room seen from a low side angle, flat ceiling light, boredom "
            "and stale air, muted palette, empty scene, no people, no text",
    "s08": "cinematic digital painting, vertical 9:16, entryway of a small "
           "home, closed front door, a single pair of sport sneakers on "
           "the floor beside the door covered in an exaggerated thick "
           "layer of dust with a small cobweb between them, grey neglected "
           "light, stillness of something untouched for weeks, plain blank "
           "wall light switches with absolutely no markings, no digits and "
           "no symbols on any surface, empty scene, no people, no text",
    "s09": "cinematic digital painting, vertical 9:16, small desk buried "
           "under exaggerated towering stacks of papers, notebooks and "
           "boxes leaning like a paper mountain, dim grey-brown light, "
           "overwhelming backlog feeling, empty scene, no people, no text, "
           "no readable writing on the papers",
    "s10a": "cinematic digital painting, vertical 9:16, the towering paper "
            "mountain on the desk seen from a low angle looming overhead, "
            "dark grey tones, intimidating scale, a task that feels "
            "impossible to begin, empty scene, no people, no text, "
            "no readable writing",
    "s10b": "cinematic digital painting, vertical 9:16, the same looming "
            "paper stacks but a warm golden glow beginning to build behind "
            "them like stored energy about to ignite, first hint of warm "
            "light in a grey world, cinematic contrast of cold shadow and "
            "warm rim light, empty scene, no people, no text",
    "s11a": "cinematic digital painting, vertical 9:16, entryway with the "
            "front door slightly ajar, a shaft of warm morning light "
            "cutting through the doorway across the floor, dust particles "
            "in the light beam, grey room behind, the moment of finally "
            "moving, empty scene, no people, no shoes, no text",
    "s11b": "cinematic digital painting, vertical 9:16, desk in warm "
            "morning light, the paper stacks now half cleared, an open "
            "clear workspace in the middle of the desk, soft golden light "
            "from a side window, feeling of flow and quiet momentum, empty "
            "scene, no people, no text, no readable writing on the papers",
    "s12": "cinematic digital painting, vertical 9:16, early morning park "
           "path with warm sunrise light breaking through trees, long "
           "soft shadows, fresh golden air, sense of release and quiet "
           "achievement, empty scene, no people, no text",
    # Style-hardening pass (manager): same scenes as s02/s05a/s06/s08 but
    # with a multi-layer painterly push, keys end in "p".
    "s02p": "hand-painted cinematic matte painting, vertical 9:16, a tall "
            "window taking most of the frame, endless flat overcast grey "
            "sky outside merging into one flat grey horizon, no sun, "
            "faint painted condensation smears on the glass, cold "
            "desaturated grey light, sense of a day that will never "
            "change, heavy still mood, painterly illustration with "
            "clearly visible broad brushstrokes and dry-brush texture, "
            "stylized simplified shapes, soft painted edges, flat washes "
            "of color, gouache painting look, 2D animation background "
            "art, absolutely NOT photorealistic, not a photograph, no "
            "photographic detail, no camera look, empty scene, no "
            "people, no text",
    "s05ap": "hand-painted cinematic matte painting, vertical 9:16, "
             "window with fogged glass looking onto a grey street, "
             "softly painted rooftops fading into mist, simplified "
             "building shapes, waiting and longing mood, cold grey "
             "tones, painterly illustration with clearly visible broad "
             "brushstrokes and dry-brush texture, stylized simplified "
             "shapes, soft painted edges, flat washes of color, gouache "
             "painting look, 2D animation background art, absolutely "
             "NOT photorealistic, not a photograph, no photographic "
             "detail, no camera bokeh, empty scene, no people, no text",
    "s06p": "hand-painted cinematic matte painting, vertical 9:16, the "
            "same fogged window as before but darker, painted rain "
            "streaks running down the glass, grey street beyond in "
            "simplified shapes, light drained away, quiet "
            "disappointment, cold palette, painterly illustration with "
            "clearly visible broad brushstrokes and dry-brush texture, "
            "stylized simplified shapes, soft painted edges, flat "
            "washes of color, gouache painting look, 2D animation "
            "background art, absolutely NOT photorealistic, not a "
            "photograph, no photographic detail, no camera bokeh, "
            "empty scene, no people, no text",
    "s08p": "hand-painted cinematic matte painting, vertical 9:16, "
            "entryway of a small home, closed front door, a single pair "
            "of sport sneakers on the floor beside the door covered in "
            "an exaggerated thick layer of dust with a small cobweb "
            "between them, grey neglected light, stillness of something "
            "untouched for weeks, plain blank wall light switches and "
            "outlet plates, completely blank with absolutely no "
            "markings, no symbols, no digits and no letters on any "
            "surface, painterly illustration with clearly visible broad "
            "brushstrokes and dry-brush texture, stylized simplified "
            "shapes, soft painted edges, flat washes of color, gouache "
            "painting look, 2D animation background art, absolutely "
            "NOT photorealistic, not a photograph, no photographic "
            "detail, empty scene, no people, no text",
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
                path = os.path.join("ep3_bgs", f"{key}.png")
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
    os.makedirs("ep3_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
