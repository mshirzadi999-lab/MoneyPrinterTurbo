#!/usr/bin/env python3
"""Character-consistency test with FLUX.2 Klein 4B (Arsln-style line man).

Step 1: generate ONE reference image of the stick-figure character.
Step 2: generate two Law 1 scenes, each time passing the reference
        image as a multipart input (input_image_0, <512px) so the model
        reuses the same character. Falls back to text-only (identical
        character description) if the reference call fails.

Output: char/ref.png, char/scene1-party.png, char/scene2-prison.png
Env: CF account/token pairs 1..3.
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid

MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
PAIRS = (("CF_ACCOUNT_ID", "CF_API_TOKEN"),
         ("CF_ACCOUNT_ID_2", "CF_API_TOKEN_2"),
         ("CF_ACCOUNT_ID_3", "CF_API_TOKEN_3"))
ACCOUNTS = []
for _a, _t in PAIRS:
    _av = (os.environ.get(_a) or "").strip()
    _tv = (os.environ.get(_t) or "").strip()
    if _av and _tv:
        ACCOUNTS.append((_av, _tv))

STYLE = ("minimalist black line drawing, simple hand-drawn explainer "
         "style, thin clean black outlines, warm beige paper background, "
         "flat, no shading, no colors, no text, no letters, no words, "
         "no watermark")
CHAR = ("a simple stick-figure man with a round head, round eyeglasses, "
        "three short strands of hair on top, a small nose, wearing a "
        "plain long-sleeve shirt and long trousers")
REF_PROMPT = (f"{CHAR}, standing full-body facing the viewer with a "
              f"neutral friendly expression, {STYLE}")
SCENE1_PROMPT = (
    f"the exact same character from the reference image: {CHAR}, now "
    f"proudly hosting a lavish party inside a grand palace hall, arms "
    f"spread wide with a proud smile, a long banquet table with dishes "
    f"beside him and fireworks visible through a tall window, {STYLE}")
SCENE2_PROMPT = (
    f"the exact same character from the reference image: {CHAR}, now "
    f"sitting sadly on the floor inside a dark prison cell, head bowed, "
    f"behind thick vertical prison bars, a small barred window above, "
    f"{STYLE}")


def _multipart(fields, files=None):
    boundary = "----cfchar" + uuid.uuid4().hex
    out = []
    for name, value in fields:
        out.append(f"--{boundary}\r\n".encode())
        out.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            .encode())
        out.append(str(value).encode("utf-8"))
        out.append(b"\r\n")
    for name, blob in (files or {}).items():
        out.append(f"--{boundary}\r\n".encode())
        out.append(
            (f'Content-Disposition: form-data; name="{name}"; '
             f'filename="ref.png"\r\n').encode())
        out.append(b"Content-Type: image/png\r\n\r\n")
        out.append(blob)
        out.append(b"\r\n")
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def _call(acc, tok, data, ctype):
    url = ("https://api.cloudflare.com/client/v4/accounts/"
           f"{acc}/ai/run/{MODEL}")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            rtype = resp.headers.get("Content-Type", "")
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    if rtype.startswith("image/"):
        return body
    payload = json.loads(body.decode("utf-8"))
    if not payload.get("success", False):
        raise RuntimeError(f"cloudflare error: {payload.get('errors')}")
    b64 = (payload.get("result") or {}).get("image")
    if not b64:
        raise RuntimeError("response has no result.image")
    return base64.b64decode(b64)


def generate(prompt, ref_blob=None):
    fields = [("prompt", prompt), ("width", "1024"), ("height", "1024")]
    files = {"input_image_0": ref_blob} if ref_blob else None
    data, ctype = _multipart(fields, files)
    last = None
    for i, (acc, tok) in enumerate(ACCOUNTS):
        try:
            img = _call(acc, tok, data, ctype)
            print(f"  ok via account {i + 1} ({len(img)} bytes)",
                  flush=True)
            return img
        except Exception as e:  # noqa: BLE001 - try next account
            last = e
            print(f"  account {i + 1} failed: {e}", flush=True)
    raise RuntimeError(f"all accounts failed: {last}")


def shrink(png_bytes, out_png):
    with open("_ref_full.png", "wb") as f:
        f.write(png_bytes)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", "_ref_full.png",
         "-vf", "scale=448:448", out_png], check=True)
    with open(out_png, "rb") as f:
        return f.read()


def main():
    if not ACCOUNTS:
        print("no Cloudflare accounts configured")
        return 2
    os.makedirs("char", exist_ok=True)
    print("step 1: reference character", flush=True)
    ref = generate(REF_PROMPT)
    with open("char/ref.png", "wb") as f:
        f.write(ref)
    ref_small = shrink(ref, "_ref_small.png")
    print(f"  reference shrunk to {len(ref_small)} bytes", flush=True)

    scenes = (("scene1-party", SCENE1_PROMPT),
              ("scene2-prison", SCENE2_PROMPT))
    ok = True
    for name, prompt in scenes:
        print(f"step: {name} (with reference image)", flush=True)
        try:
            img = generate(prompt, ref_blob=ref_small)
            mode = "reference"
        except Exception as e:  # noqa: BLE001 - fall back to text only
            print(f"  reference mode failed ({e}); text-only fallback",
                  flush=True)
            try:
                img = generate(prompt)
                mode = "text-only-fallback"
            except Exception as e2:  # noqa: BLE001
                print(f"  {name} FAILED completely: {e2}", flush=True)
                ok = False
                continue
        with open(f"char/{name}.png", "wb") as f:
            f.write(img)
        print(f"  {name}: saved, mode={mode}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
