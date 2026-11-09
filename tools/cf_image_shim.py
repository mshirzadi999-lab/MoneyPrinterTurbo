#!/usr/bin/env python3
"""OpenAI-compatible image shim backed by Cloudflare Workers AI.

MoneyPrinterTurbo's ``openai_image`` source POSTs to
``{base_url}/images/generations`` and expects ``{"data": [{"b64_json": ...}]}``.
Cloudflare's image API is not OpenAI-shaped, so this tiny local server
translates between the two inside the GitHub Actions job.

Env:
  CF_ACCOUNT_ID   Cloudflare account id
  CF_API_TOKEN    Cloudflare API token (Workers AI permission)
  CF_IMAGE_MODEL  default @cf/black-forest-labs/flux-1-schnell
  SHIM_PORT       default 8123
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CF_API_TOKEN", "").strip()
ACCOUNTS = []
for _a, _t in (("CF_ACCOUNT_ID", "CF_API_TOKEN"),
               ("CF_ACCOUNT_ID_2", "CF_API_TOKEN_2")):
    _av = os.environ.get(_a, "").strip()
    _tv = os.environ.get(_t, "").strip()
    if _av and _tv:
        ACCOUNTS.append((_av, _tv))
QUOTA_WORDS = ("quota", "limit", "exceeded", "allocation",
               "neurons", "daily", "429")


def is_quota_failure(msg):
    s = str(msg).lower()
    return ("4006" in s or "429" in s
            or ("error" in s and any(w in s for w in QUOTA_WORDS[0:6]))
            or any(w in s for w in ("quota", "allocation", "neurons")))


MODEL = os.environ.get(
    "CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell"
).strip()
PORT = int(os.environ.get("SHIM_PORT", "8123"))


def generate_image(prompt: str) -> bytes:
    last = None
    for i, (acc, tok) in enumerate(ACCOUNTS):
        try:
            return _generate_with(acc, tok, prompt)
        except Exception as e:  # noqa: BLE001 - try next account on quota
            last = e
            if i + 1 < len(ACCOUNTS) and is_quota_failure(e):
                sys.stderr.write(
                    f"[shim] account {i + 1} quota/limit hit ({e}); "
                    f"switching to account {i + 2}\n")
                continue
            raise
    raise RuntimeError(f"all Cloudflare accounts failed: {last}")


def _generate_with(ACCOUNT, TOKEN, prompt: str) -> bytes:
    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{ACCOUNT}/ai/run/{MODEL}"
    )
    # NOTE: flux-1-schnell's REST schema rejects extra properties such as
    # num_steps (AiError 5006). Send the prompt only; defaults apply.
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(
            f"cloudflare HTTP {exc.code}: {detail}"
        ) from exc
    if ctype.startswith("image/"):
        return body
    data = json.loads(body.decode("utf-8"))
    if not data.get("success", False):
        raise RuntimeError(f"cloudflare error: {data.get('errors')}")
    b64 = (data.get("result") or {}).get("image")
    if not b64:
        raise RuntimeError("cloudflare response has no result.image")
    return base64.b64decode(b64)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: A003 - stdlib name
        sys.stderr.write("[shim] " + (fmt % args) + "\n")

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/health"):
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/images/generations"):
            self._json(404, {"error": {"message": "not found"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:  # bad client payload
            self._json(400, {"error": {"message": f"bad request: {exc}"}})
            return
        prompt = str(req.get("prompt") or "").strip()
        if not prompt:
            self._json(400, {"error": {"message": "prompt is required"}})
            return
        try:
            img = generate_image(prompt)
        except Exception as exc:  # upstream failure -> let MPT log/skip
            self._json(
                502,
                {"error": {"message": f"cloudflare generation failed: {exc}"}},
            )
            return
        self._json(
            200,
            {
                "created": 0,
                "data": [{"b64_json": base64.b64encode(img).decode("ascii")}],
            },
        )


if __name__ == "__main__":
    if not ACCOUNTS:
        sys.exit("CF_ACCOUNT_ID and CF_API_TOKEN must be set")
    print(f"cf_image_shim listening on 127.0.0.1:{PORT}, model={MODEL}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
