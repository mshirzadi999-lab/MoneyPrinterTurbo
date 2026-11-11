#!/usr/bin/env python3
"""TTS-only narration: synthesize each line with Gemini Cruz (via
segmented_build.tts) and save per-line WAVs + durations.json as an artifact.
Used for the discipline pilot (50s 5-AM story) — video is built locally,
this job only produces the voice lines.

Env: GEMINI_API_KEY, GEMINI_API_KEY_2 (repo secrets)
"""
import json
import os
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segmented_build as sb  # noqa: E402

LINES = [
    "سه ساعته اسکرول می‌کنی، هیچی یادت نیست.",
    "چشماتو باز نکرده، گوشی دستته.",
    "یه ویدیوی دیگه، بعدش شروع می‌کنم.",
    "یه شب، وسط اسکرول، یهو از دست خودت خسته میشی.",
    "اینستا رو از گوشیت پاک می‌کنی.",
    "روز اول، دستت هی میره سمت جیبت؛ گوشی رو درمیاری، ولی دیگه چیزی توش نیست.",
    "روز سوم، به‌جای گوشی، یه صفحه کتاب می‌خونی.",
    "شب سوم، سایه برمی‌گرده: امشب حوصلت سر رفته؛ نصبش کن. فردا دوباره پاکش می‌کنی.",
    "گوشی رو می‌ذاری کنار؛ کتاب رو باز می‌کنی.",
    "روز دوازدهم، کتاب میرسه وسطاش و خودت حواست نیست.",
    "روز بیست و یکم، یه عصر کامل می‌گذره و یادت هم نمیاد گوشی رو برداری.",
    "روز سی‌ام، کتاب رو می‌بندی. صفحه گوشیت هنوز خالیه، ولی تو دیگه خالی نیستی.",
]

STYLE = ("Read the following Persian text aloud in a commanding narration "
         "style, with rich vocal modulation and dramatic pauses. "
         "Read only the Persian text, not this instruction:")


def wav_duration(path):
    with wave.open(path, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def main():
    out_dir = "narration_out"
    os.makedirs(out_dir, exist_ok=True)
    voice = sb.parse_voice("gemini:Cruz-Narration")
    durations = {}
    for i, line in enumerate(LINES, start=1):
        path = os.path.join(out_dir, f"n{i}.wav")
        sb.tts(line, voice, STYLE, path)
        durations[f"n{i}"] = round(wav_duration(path), 3)
        print(f"n{i}: {durations[f'n{i}']}s  {line}", flush=True)
    with open(os.path.join(out_dir, "durations.json"), "w") as f:
        json.dump(durations, f, ensure_ascii=False, indent=1)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
