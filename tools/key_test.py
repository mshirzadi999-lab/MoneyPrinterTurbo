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


def test_cf():
    acc = (os.environ.get(A1) or "").strip()
    tok = (os.environ.get(T1) or "").strip()
    if not acc or not tok:
        verdict("cf", False, "FAIL - account id or token empty/not set")
    url = ("https://api.cloudflare.com/client/v4/accounts/"
           f"{acc}/ai/run/@cf/black-forest-labs/flux-1-schnell")
    req = urllib.request.Request(
        url, data=json.dumps({"prompt": "a red apple on a table"}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read()
            ctype = resp.headers.get("Content-Type", "")
        if ctype.startswith("image/") and len(body) > 1000:
            verdict("cf", True, f"PASS - image returned ({len(body)} bytes)")
        data = json.loads(body.decode("utf-8"))
        if data.get("success"):
            verdict("cf", True, "PASS - success response")
        verdict("cf", False, f"FAIL - errors: {data.get('errors')}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        low = detail.lower()
        if e.code == 429 or "4006" in detail or "quota" in low \
                or "allocation" in low or "neurons" in low:
            verdict("cf", True,
                    "VALID_QUOTA - account accepted, daily quota exhausted")
        verdict("cf", False, f"FAIL - HTTP {e.code}: {detail}")
    except Exception as e:  # noqa: BLE001
        verdict("cf", False, f"FAIL - {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "gemini":
        test_gemini()
    elif mode == "cf":
        test_cf()
    else:
        print("usage: key_test.py gemini|cf")
        sys.exit(2)
