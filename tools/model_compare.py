#!/usr/bin/env python3
"""Side-by-side comparison: FLUX.1 Schnell vs FLUX.2 Klein 4B.

Sends ONE identical prompt to both Cloudflare models (same account,
1024x1024) and saves the PNGs next to each other for visual comparison.

Env: COMPARE_PROMPT (optional), CF account/token pairs 1..3.
Output: compare/flux1-schnell.png, compare/flux2-klein-4b.png
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_PROMPT = (
    "Flat vector illustration of a busy old Persian bazaar alley at "
    "golden hour, in a minimal educational style: a tea seller pouring "
    "tea from a brass samovar into small glass cups at a wooden stall, "
    "three merchants talking beside him, colorful carpets and copper "
    "pots hanging on the walls, a cat sitting on stacked wooden crates, "
    "open sacks of orange, red and turquoise spices in front of a shop, "
    "soft beige background, muted teal and orange color palette, clean "
    "simple shapes, detailed but tidy composition, no text, no letters, "
    "no words, no watermark"
)
PROMPT = (os.environ.get("COMPARE_PROMPT") or "").strip() or DEFAULT_PROMPT

PAIRS = (("CF_ACCOUNT_ID", "CF_API_TOKEN"),
         ("CF_ACCOUNT_ID_2", "CF_API_TOKEN_2"),
         ("CF_ACCOUNT_ID_3", "CF_API_TOKEN_3"))
ACCOUNTS = []
for _a, _t in PAIRS:
    _av = (os.environ.get(_a) or "").strip()
    _tv = (os.environ.get(_t) or "").strip()
    if _av and _tv:
        ACCOUNTS.append((_av, _tv))

SCHNELL = "@cf/black-forest-labs/flux-1-schnell"
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


def gen_schnell(acc, tok, prompt):
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    ctype, body = _post(acc, tok, SCHNELL, payload, "application/json")
    return _extract(ctype, body)


def _multipart(fields):
    boundary = "----cfform" + uuid.uuid4().hex
    out = []
    for name, value in fields:
        out.append(f"--{boundary}\r\n".encode())
        out.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            .encode())
        out.append(str(value).encode("utf-8"))
        out.append(b"\r\n")
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def gen_klein(acc, tok, prompt):
    body, ctype = _multipart(
        [("prompt", prompt), ("width", "1024"), ("height", "1024")])
    rtype, rbody = _post(acc, tok, KLEIN, body, ctype)
    return _extract(rtype, rbody)


def run_one(label, fn, out_path):
    last = None
    for i, (acc, tok) in enumerate(ACCOUNTS):
        try:
            img = fn(acc, tok, PROMPT)
            with open(out_path, "wb") as f:
                f.write(img)
            print(f"{label}: OK via account {i + 1} "
                  f"({len(img)} bytes) -> {out_path}", flush=True)
            return True
        except Exception as e:  # noqa: BLE001 - try next account
            last = e
            print(f"{label}: account {i + 1} failed: {e}", flush=True)
    print(f"{label}: ALL ACCOUNTS FAILED: {last}", flush=True)
    return False


def main():
    if not ACCOUNTS:
        print("no Cloudflare accounts configured")
        return 2
    os.makedirs("compare", exist_ok=True)
    print(f"prompt: {PROMPT[:120]}...", flush=True)
    ok1 = run_one("flux1-schnell", gen_schnell, "compare/flux1-schnell.png")
    ok2 = run_one("flux2-klein-4b", gen_klein, "compare/flux2-klein-4b.png")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())
