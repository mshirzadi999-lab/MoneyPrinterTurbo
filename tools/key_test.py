#!/usr/bin/env python3
"""Classify one Gemini key or one Cloudflare account for the key-test job.

Usage: key_test.py gemini|cf   (credentials come from the environment)
Verdicts: PASS (works), VALID_QUOTA (key accepted, quota exhausted),
FAIL (key rejected / other error).
"""
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

K1 = "GEMINI" + "_API" + "_KEY"
A1, T1 = "CF_ACCOUNT_ID", "CF_API_TOKEN"


def verdict(kind, ok, detail):
    print(f"VERDICT {kind}: {detail}", flush=True)
    sys.exit(0 if ok else 1)


def test_gemini():
    from google import genai
    from google.genai import types
    if not (os.environ.get(K1) or "").strip():
        verdict("gemini", False, "FAIL - secret is empty or not set")
    try:
        client = genai.Client()
        resp = client.models.generate_content(
            model=os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
            contents="سلام",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Cruz")))))
        data = None
        cand = resp.candidates[0] if resp.candidates else None
        for part in (getattr(getattr(cand, "content", None), "parts", None) or []):
            if getattr(part, "inline_data", None):
                data = part.inline_data.data
                break
        if data:
            verdict("gemini", True,
                    f"PASS - TTS audio returned ({len(data)} bytes)")
        verdict("gemini", False, "FAIL - response had no audio")
    except Exception as e:  # noqa: BLE001
        s = str(e)
        if "429" in s or "RESOURCE_EXHAUSTED" in s:
            verdict("gemini", True,
                    "VALID_QUOTA - key accepted, daily quota exhausted")
        verdict("gemini", False, f"FAIL - {type(e).__name__}: {s[:200]}")


def _multipart(fields):
    boundary = "----cfkt" + uuid.uuid4().hex
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


def _cf_call(acc, tok, model, data, ctype):
    """Returns (status, detail): PASS / VALID_QUOTA / FAIL."""
    url = ("https://api.cloudflare.com/client/v4/accounts/"
           f"{acc}/ai/run/{model}")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read()
            rtype = resp.headers.get("Content-Type", "")
        if rtype.startswith("image/") and len(body) > 1000:
            return "PASS", f"image returned ({len(body)} bytes)"
        payload = json.loads(body.decode("utf-8"))
        if payload.get("success"):
            return "PASS", "success response"
        return "FAIL", f"errors: {payload.get('errors')}"
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        low = detail.lower()
        if e.code == 429 or "4006" in detail or "quota" in low \
                or "allocation" in low or "neurons" in low:
            return ("VALID_QUOTA",
                    "account accepted, daily quota exhausted")
        return "FAIL", f"HTTP {e.code}: {detail}"
    except Exception as e:  # noqa: BLE001
        return "FAIL", f"{type(e).__name__}: {str(e)[:200]}"


def test_cf():
    acc = (os.environ.get(A1) or "").strip()
    tok = (os.environ.get(T1) or "").strip()
    if not acc or not tok:
        verdict("cf", False, "FAIL - account id or token empty/not set")
    prompt = "a red apple on a table"
    klein_body, klein_ctype = _multipart(
        [("prompt", prompt), ("width", "512"), ("height", "512")])
    cases = (
        ("cf-schnell", "@cf/black-forest-labs/flux-1-schnell",
         json.dumps({"prompt": prompt}).encode(), "application/json"),
        ("cf-klein-4b", "@cf/black-forest-labs/flux-2-klein-4b",
         klein_body, klein_ctype),
    )
    ok = True
    for label, model, data, ctype in cases:
        status, detail = _cf_call(acc, tok, model, data, ctype)
        print(f"VERDICT {label}: {status} - {detail}", flush=True)
        if status == "FAIL":
            ok = False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "gemini":
        test_gemini()
    elif mode == "cf":
        test_cf()
    else:
        print("usage: key_test.py gemini|cf")
        sys.exit(2)
