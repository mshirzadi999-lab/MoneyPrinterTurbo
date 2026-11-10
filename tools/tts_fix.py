#!/usr/bin/env python3
"""Re-synthesize specific narration lines with NO style prompt (plain Cruz).
Fix for prepend-mode instruction leaks/repeats in tts_narration.py output.
Env: FIX_INDICES e.g. "4,5,6"; GEMINI_API_KEY, GEMINI_API_KEY_2.
"""
import json
import os
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segmented_build as sb  # noqa: E402
from tts_narration import LINES  # noqa: E402


def wav_duration(path):
    with wave.open(path, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def main():
    indices = [int(x) for x in os.environ["FIX_INDICES"].split(",")]
    out_dir = "narration_fix"
    os.makedirs(out_dir, exist_ok=True)
    voice = sb.parse_voice("gemini:Cruz-Narration")
    durations = {}
    for i in indices:
        path = os.path.join(out_dir, f"n{i}.wav")
        sb.tts(LINES[i - 1], voice, "", path)
        durations[f"n{i}"] = round(wav_duration(path), 3)
        print(f"n{i}: {durations[f'n{i}']}s  {LINES[i - 1]}", flush=True)
    with open(os.path.join(out_dir, "durations.json"), "w") as f:
        json.dump(durations, f, ensure_ascii=False, indent=1)
    print("FIX DONE", flush=True)


if __name__ == "__main__":
    main()
