#!/usr/bin/env python3
"""Episode 17 backgrounds: FLUX.2 Klein 4B via Cloudflare (account
rotation). Empty cinematic painted scenes (character is composited
later, locally). One background per shot (12 shots = 12 sentences).
Output: ep17_bgs/<key>.png. Env: CF account/token pairs 1..3.
ONLY=keys.

Lessons from ep16 applied from the start: the word "silhouette" /
"shadow" makes FLUX render a human figure — the inner-voice shadow
(shot-04) is described as a formless black ink smudge / the
character's own long cast shadow on the wall, with explicit "no head,
no arms, no legs, no human outline, not a silhouette of a person".
The phone sits ON the nightstand explicitly; its screen is plain
glow only (shot-01) or plain dark and off (shot-12); the coffee cup
(shot-10) has no writing. No readable text / numbers / logos anywhere.
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
    "shot-01": "vertical 9:16, dark bedroom at night, a bed on the LEFT "
               "side of the frame, a wooden nightstand on the RIGHT side "
               "of the frame with ONE single phone lying flat ON the "
               "nightstand, the phone screen glowing cold blue light, "
               "plain glow only with no readable text, no icons, no "
               "numbers, the phone glow is the only bright light in the "
               "room, very faint cold moonlight from a small window on "
               "the LEFT, dark blue-grey bedroom, clear empty floor "
               "space in the MIDDLE of the frame where a person would "
               "stand facing the nightstand, no second phone, no person "
               "holding a phone",
    "shot-02": "vertical 9:16, the same dark bedroom at night, a person "
               "standing beside a tall window, faint cold moonlight "
               "coming through the window, the bedroom empty and quiet "
               "and still, a bed at the edge of the frame, dark "
               "blue-grey walls, clear empty floor space in the MIDDLE "
               "of the frame where a person would stand facing the "
               "window, no phone anywhere in the frame, no second "
               "person, no readable text",
    "shot-03": "vertical 9:16, wider view of a dark bedroom at night, a "
               "bed at the side of the frame, a plain empty wall and a "
               "dark floor, faint cold moonlight, feeling of walking "
               "past the bed in the dark, large clear empty space in "
               "the MIDDLE of the room where a person would walk from "
               "right to left, no phone, no second person, no object "
               "in any hand, no readable text",
    "shot-04": "vertical 9:16, dark bedroom wall at night, on the wall "
               "a long stretched formless black smudge like a blot of "
               "black ink or a column of dark smoke, the character's "
               "own long cast shadow on the wall, one edge of the "
               "smudge smeared forward along the wall as if reaching "
               "and searching, ragged uneven edges, faint cold "
               "moonlight from behind where the shadow falls, the black "
               "smudge has no face, no head, no arms, no legs, no feet, "
               "no human outline, no body shape, never a person, never "
               "a human figure, not a silhouette of a person, clear "
               "empty floor space in the foreground where a person "
               "would stand facing the wall, no phone, no readable text",
    "shot-05": "vertical 9:16, medium close view of a dark bedroom wall "
               "at night, plain dark empty wall in the background, "
               "faint cold moonlight falling on one side, a bed edge "
               "barely visible at the bottom of the frame, large clear "
               "empty space in the MIDDLE of the frame where a person "
               "would stand close to the camera, no phone, no second "
               "person, no readable text, no numbers",
    "shot-06": "vertical 9:16, dark bedroom at night, a bed in the "
               "CENTER of the frame with a pillow at the head of the "
               "bed, a wooden nightstand beside the bed, a plain empty "
               "wall behind the bed, very faint cold moonlight from a "
               "window on the LEFT, dark blue-grey bedroom, clear "
               "empty space on the bed and in front of the bed where a "
               "person would lie down and sit up, no phone anywhere in "
               "the frame, no clock with readable numbers, no readable "
               "text",
    "shot-07": "vertical 9:16, the same dark bedroom at night, a bed in "
               "the CENTER of the frame, a patch of cold moonlight on "
               "the floor in front of the bed, still and cold, darkness "
               "around the bed, a plain empty wall behind, clear empty "
               "space on the edge of the bed where a person would sit, "
               "no phone, no readable text",
    "shot-08": "vertical 9:16, the same dark bedroom at night, a person "
               "standing facing the darkness of the room, a window with "
               "faint cold moonlight in the background, dark blue-grey "
               "walls, clear empty floor space in the MIDDLE of the "
               "frame where a person would stand facing the window and "
               "the dark room, no phone anywhere in the frame, no "
               "readable text",
    "shot-09": "vertical 9:16, the same dark bedroom at night, a bed in "
               "the CENTER of the frame, a person sitting on the edge "
               "of the bed, cold moonlight, darkness around the bed, a "
               "plain empty wall behind, clear empty space on the edge "
               "of the bed where a person would sit with a slightly "
               "bowed posture, no phone, no readable text",
    "shot-10": "vertical 9:16, the same bedroom in the MORNING, warm "
               "golden sunlight coming through a window on the LEFT, a "
               "wooden nightstand with ONE single coffee cup ON it, "
               "only one cup in the whole scene, the cup plain with no "
               "writing and no logo, a bed with neat tidy sheets, warm "
               "golden light on the wall and floor, clear empty floor "
               "space in the MIDDLE of the frame where a person would "
               "stand beside the nightstand facing the cup, no phone "
               "anywhere in the frame, no second cup, no readable text",
    "shot-11": "vertical 9:16, the same bedroom in the MORNING, more "
               "warm golden sunlight than before, a person standing "
               "facing a tall window, warm golden light spreading wide "
               "across the wall and the floor from the window, a bed at "
               "the edge of the frame, clear empty floor space in the "
               "MIDDLE of the frame where a person would stand facing "
               "the window, no phone, no readable text",
    "shot-12": "vertical 9:16, bedroom at night again, darker than the "
               "first night scene, a bed in the CENTER of the frame "
               "with a pillow at the head of the bed, a wooden "
               "nightstand beside the bed with ONE single phone lying "
               "flat ON the nightstand, the phone screen DARK and OFF, "
               "plain black with no glow, no light, no readable text, "
               "very faint cold moonlight from a window, the room quiet "
               "and still, clear empty space on the bed where a person "
               "would lie asleep, no second phone, no readable text",
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
                path = os.path.join("ep17_bgs", f"{key}.png")
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
    os.makedirs("ep17_bgs", exist_ok=True)
    only = [x for x in os.environ.get("ONLY", "").split(",") if x]
    keys = only or list(PROMPTS)
    ok = all(gen_one(k, f"{PROMPTS[k]}, {STYLE}") for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
