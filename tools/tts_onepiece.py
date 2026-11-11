#!/usr/bin/env python3
"""One-piece narration-only TTS (general tool).

Synthesizes a FULL text in exactly ONE Gemini TTS call via
segmented_build.tts() and saves a single WAV + meta.json as an artifact.
No images, no video — narration only, so nothing downstream is built on
unapproved audio.

Env:
  NARRATION_TEXT  full narration text (required)
  VOICE           e.g. "gemini:Zubenelgenubi" or a bare voice name
                  (default "gemini:Zubenelgenubi")
  STYLE_PROMPT    style instruction ("" to disable). The pipeline first
                  tries it as system_instruction; gemini-3.8-flash-tts
                  rejects that, so it falls back to prepend mode
                  (segmented_build handles both and logs the switch).
  GEMINI_API_KEY / GEMINI_API_KEY_2  repo secrets (failover inside tts())
Output: narration_out/narration_raw.wav, narration_out/meta.json
"""
import json
import os
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segmented_build as sb  # noqa: E402


def wav_duration(path):
    with wave.open(path, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def main():
    text = (os.environ.get("NARRATION_TEXT") or "").strip()
    if not text:
        print("NARRATION_TEXT is empty", file=sys.stderr)
        return 1
    voice = sb.parse_voice(os.environ.get("VOICE", "gemini:Zubenelgenubi"))
    style = os.environ.get("STYLE_PROMPT", "")
    out_dir = "narration_out"
    os.makedirs(out_dir, exist_ok=True)
    out_wav = os.path.join(out_dir, "narration_raw.wav")
    print(f"One-piece TTS: voice={voice} chars={len(text)} "
          f"style={'yes' if style else 'no'}", flush=True)
    sb.tts(text, voice, style, out_wav)  # exactly ONE call for the full text
    dur = wav_duration(out_wav)
    meta = {
        "voice": voice,
        "duration_s": round(dur, 3),
        "style_mode_final": sb.STYLE_MODE.get("mode"),
        "style_used": bool(style),
        "chars": len(text),
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"STYLE_MODE_FINAL={meta['style_mode_final']}", flush=True)
    print(f"DONE narration_raw.wav {dur:.2f}s voice={voice}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
