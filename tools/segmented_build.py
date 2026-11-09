#!/usr/bin/env python3
"""Per-sentence segmented builder.

For each segment (one narration sentence + one image prompt):
  1. Generate the sentence audio with Gemini TTS (single call per sentence).
  2. Measure the audio duration exactly.
  3. Generate the sentence's image via the local Cloudflare shim.
  4. Hold the image for exactly the audio duration (+ small pad).
Then concatenate all segments and (if songs exist in resource/songs) mix BGM.

Env:
  SEGMENTS        multiline, each line: "<sentence text> ||| <image prompt>"
  VOICE           e.g. "gemini:Cruz-Narration" (MPT format) or a bare voice name
  STYLE_PROMPT    instruction prepended to every TTS call ("" to disable)
  IMAGE_STYLE     template containing {term} ("" for raw prompt)
  GEMINI_API_KEY  API key
  GEMINI_TTS_MODEL  default gemini-3.8-flash-tts
  IMAGE_API_BASE  default http://127.0.0.1:8123/v1
Output: storage/tasks/segmented/final-1.mp4
"""
import base64
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import wave

W, H = 1080, 1920
PAD = 0.15  # seconds of breathing room after each sentence
OUT_DIR = os.path.join("storage", "tasks", "segmented")
MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
SHIM = os.environ.get("IMAGE_API_BASE", "http://127.0.0.1:8123/v1")


def run(cmd):
    print("+", " ".join(cmd[:3]), "...", flush=True)
    subprocess.run(cmd, check=True)


def parse_voice(v):
    v = (v or "").strip()
    if v.startswith("gemini:"):
        return v.split(":", 1)[1].split("-", 1)[0].strip()
    return v


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


STYLE_MODE = {"mode": "system"}


def tts(text, voice, style, out_wav):
    from google import genai
    from google.genai import types

    if ("GEMINI" + "_API_KEY") not in os.environ:
        raise RuntimeError("Gemini key secret is not set")
    last = None
    for attempt in range(4):
        use_system = bool(style) and STYLE_MODE["mode"] == "system"
        contents = text if use_system else (
            (style.rstrip() + " " + text) if style else text)
        try:
            client = genai.Client()
            cfg = {
                "response_modalities": ["AUDIO"],
                "speech_config": types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice))),
            }
            if use_system:
                cfg["system_instruction"] = style
            resp = client.models.generate_content(
                model=MODEL, contents=contents,
                config=types.GenerateContentConfig(**cfg))
            cand = resp.candidates[0] if resp.candidates else None
            data, rate = None, 24000
            for part in (getattr(getattr(cand, "content", None), "parts", None) or []):
                if getattr(part, "inline_data", None):
                    data = part.inline_data.data
                    m = re.search(r"rate=(\d+)", part.inline_data.mime_type or "")
                    if m:
                        rate = int(m.group(1))
                    break
            if not data:
                raise RuntimeError("Gemini returned no audio")
            if isinstance(data, str):
                data = base64.b64decode(data)
            with wave.open(out_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(rate)
                wf.writeframes(data)
            return
        except Exception as e:  # noqa: BLE001 - retry / fall back, then surface
            last = e
            if use_system:
                STYLE_MODE["mode"] = "prepend"
                print(f"system_instruction mode failed ({e}); "
                      "switching to prepend mode", flush=True)
                continue
            print(f"TTS attempt {attempt + 1} failed: {e}", flush=True)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"TTS failed after retries: {last}")


def gen_image(prompt, out_png):
    body = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(
        SHIM + "/images/generations", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer shim-local"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read())
    b64 = resp["data"][0]["b64_json"]
    with open(out_png, "wb") as f:
        f.write(base64.b64decode(b64))


def make_segment(img, wav, dur, out_mp4):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},fps=30,format=yuv420p")
    af = (f"apad,afade=t=in:st=0:d=0.03,"
          f"afade=t=out:st={max(dur - 0.06, 0):.3f}:d=0.06")
    run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-i", wav,
         "-filter_complex", f"[0:v]{vf}[v];[1:a]{af}[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-c:a", "aac",
         "-ar", "48000", out_mp4])


def concat(parts, out_mp4):
    lst = os.path.join(OUT_DIR, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", out_mp4])


def add_bgm(video, out_mp4):
    songs = sorted(glob.glob(os.path.join("resource", "songs", "*.mp3")))
    if not songs:
        print("No BGM songs found, keeping narration only.", flush=True)
        os.replace(video, out_mp4)
        return
    song = songs[0]
    print(f"Mixing BGM: {song}", flush=True)
    run(["ffmpeg", "-y", "-i", video, "-stream_loop", "-1", "-i", song,
         "-filter_complex",
         "[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first:"
         "dropout_transition=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
         out_mp4])


def main():
    raw = os.environ.get("SEGMENTS", "")
    voice = parse_voice(os.environ.get("VOICE", "gemini:Cruz-Narration"))
    style = os.environ.get("STYLE_PROMPT", "")
    image_style = os.environ.get("IMAGE_STYLE", "")
    segments = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or "|||" not in line:
            continue
        text, prompt = line.split("|||", 1)
        segments.append((text.strip(), prompt.strip()))
    if not segments:
        print("No segments parsed from SEGMENTS", file=sys.stderr)
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Building {len(segments)} segments with voice {voice}", flush=True)
    speed = float(os.environ.get("SPEED", "1.0") or "1.0")
    parts = []
    for i, (text, prompt) in enumerate(segments, 1):
        wav = os.path.join(OUT_DIR, f"seg{i:02d}.wav")
        img = os.path.join(OUT_DIR, f"seg{i:02d}.png")
        mp4 = os.path.join(OUT_DIR, f"seg{i:02d}.mp4")
        print(f"[{i}/{len(segments)}] TTS: {text[:40]}...", flush=True)
        tts(text, voice, style, wav)
        if abs(speed - 1.0) > 0.001:
            sped = wav.replace(".wav", "-s.wav")
            run(["ffmpeg", "-y", "-i", wav, "-filter:a",
                 f"atempo={speed}", sped])
            wav = sped
        dur = probe_duration(wav)
        print(f"[{i}/{len(segments)}] audio {dur:.2f}s -> image: {prompt[:50]}",
              flush=True)
        full_prompt = (image_style.replace("{term}", prompt)
                       if "{term}" in image_style else prompt)
        gen_image(full_prompt, img)
        make_segment(img, wav, dur + PAD, mp4)
        parts.append(mp4)
    joined = os.path.join(OUT_DIR, "joined.mp4")
    concat(parts, joined)
    final = os.path.join(OUT_DIR, "final-1.mp4")
    add_bgm(joined, final)
    print(f"DONE {final} duration={probe_duration(final):.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
