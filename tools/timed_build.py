#!/usr/bin/env python3
"""Timed builder (Mehdi's method, 2026-11-09).

  1. ONE Gemini TTS call for the whole script (natural flow, 1 request/day).
  2. Optional speed-up (atempo, pitch preserved) applied to the narration.
  3. Sentence boundaries measured from the actual audio (faster-whisper
     word timestamps -> largest inter-word gaps are the sentence pauses).
  4. Mehdi's 6-second rule: a sentence up to SPLIT_THRESHOLD seconds gets
     ONE image; a longer sentence is split into TWO image slots at its
     largest internal pause.
  5. One generated image per slot (Cloudflare shim), held for exactly its
     slot duration; the single narration file is muxed untouched, so the
     audio has no seams at all.

Env:
  SEGMENTS   multiline: "<sentence> ||| <image prompt> ||| <2nd prompt (opt)>"
  VOICE      e.g. "gemini:Cruz-Narration"
  STYLE_PROMPT  style instruction (system channel first, prepend fallback)
  SPEED      e.g. "1.15" (default "1.0")
  IMAGE_STYLE   template containing {term}
  GEMINI_API_KEY / GEMINI_TTS_MODEL / IMAGE_API_BASE: as in segmented_build
Output: storage/tasks/timed/final-1.mp4
"""
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segmented_build as sb  # noqa: E402  (reuse tts/image/ffmpeg helpers)

OUT_DIR = os.path.join("storage", "tasks", "timed")
SPLIT_THRESHOLD = float(os.environ.get("SPLIT_THRESHOLD", "6.0"))


def normalize_fa(text):
    repl = {"ي": "ی", "ك": "ک", "ة": "ه", "ؤ": "و", "إ": "ا", "أ": "ا",
            "ٱ": "ا", "\u200c": " ", "\u0640": ""}
    for k, v in repl.items():
        text = text.replace(k, v)
    for ch in ".,!؟?؛:؛«»()\"\'\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652":
        text = text.replace(ch, " ")
    return [t for t in text.split() if t]


def transcribe_words(wav_path):
    """Return (words, segments) from faster-whisper."""
    from faster_whisper import WhisperModel

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(wav_path, language="fa",
                                       word_timestamps=True)
    segs = list(segments)
    words = []
    for seg in segs:
        for w in (seg.words or []):
            words.append((float(w.start), float(w.end)))
    return words, segs


def compute_slots(audio_path, words, segments, total_dur,
                  n_sentences, threshold=SPLIT_THRESHOLD):
    """Sentence spans from whisper's own sentence-level segments.

    Segments already pause at sentence ends; map them onto the known
    sentence count (merge extras at the smallest gap, split the longest
    if too few), then apply the split rule. (audio_path/words kept for
    signature stability and the split step.)
    """
    times = [(float(s.start), float(s.end)) for s in segments
             if float(s.end) > float(s.start)]
    if not times:
        step = total_dur / max(n_sentences, 1)
        spans = [(i * step, (i + 1) * step) for i in range(n_sentences)]
    else:
        segs = [[s, e] for s, e in times]
        while len(segs) > n_sentences:
            gaps = [segs[i + 1][0] - segs[i][1]
                    for i in range(len(segs) - 1)]
            k = min(range(len(gaps)), key=lambda i: gaps[i])
            segs[k:k + 2] = [[segs[k][0], segs[k + 1][1]]]
        while len(segs) < n_sentences:
            k = max(range(len(segs)),
                    key=lambda i: segs[i][1] - segs[i][0])
            s, e = segs[k]
            segs[k:k + 1] = [[s, (s + e) / 2.0], [(s + e) / 2.0, e]]
        bounds = [0.0]
        for i in range(len(segs) - 1):
            bounds.append((segs[i][1] + segs[i + 1][0]) / 2.0)
        bounds.append(total_dur)
        spans = [(bounds[i], bounds[i + 1]) for i in range(n_sentences)]
    slots = []
    for si, (s, e) in enumerate(spans):
        if e - s > threshold:
            inside = [(words[i + 1][0] - words[i][1], i)
                      for i in range(len(words) - 1)
                      if words[i][1] >= s and words[i + 1][0] <= e]
            mid = (s + e) / 2.0
            if inside:
                gi = max(inside, key=lambda t: t[0])[1]
                cand = (words[gi][1] + words[gi + 1][0]) / 2.0
                if s + 2.2 < cand < e - 2.2:
                    mid = cand
            slots.append((s, mid, si))
            slots.append((mid, e, si))
        else:
            slots.append((s, e, si))
    return spans, slots


def make_image_clip(img, dur, out_mp4):
    vf = (f"scale={sb.W}:{sb.H}:force_original_aspect_ratio=increase,"
          f"crop={sb.W}:{sb.H},fps=30,format=yuv420p")
    sb.run(["ffmpeg", "-y", "-loop", "1", "-i", img,
            "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]",
            "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium",
            out_mp4])


def main():
    raw = os.environ.get("SEGMENTS", "")
    voice = sb.parse_voice(os.environ.get("VOICE", "gemini:Cruz-Narration"))
    style = os.environ.get("STYLE_PROMPT", "")
    image_style = os.environ.get("IMAGE_STYLE", "")
    speed = float(os.environ.get("SPEED", "1.0") or "1.0")
    items = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or "|||" not in line:
            continue
        parts = [p.strip() for p in line.split("|||")]
        items.append({"text": parts[0],
                      "p1": parts[1] if len(parts) > 1 else parts[0],
                      "p2": parts[2] if len(parts) > 2 else None})
    if not items:
        print("No segments parsed from SEGMENTS", file=sys.stderr)
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    full_text = " ".join(it["text"] for it in items)
    print(f"Timed build: {len(items)} sentences, voice {voice}, "
          f"speed {speed}", flush=True)

    narration = os.path.join(OUT_DIR, "narration.wav")
    preset = os.environ.get("NARRATION_FILE", "")
    if preset and os.path.exists(preset):
        import shutil
        print(f"Using preset narration: {preset}", flush=True)
        shutil.copy(preset, narration)
    else:
        sb.tts(full_text, voice, style, narration)
    if abs(speed - 1.0) > 0.001:
        sped = os.path.join(OUT_DIR, "narration-s.wav")
        sb.run(["ffmpeg", "-y", "-i", narration, "-filter:a",
                f"atempo={speed}", sped])
        narration = sped
    total = sb.probe_duration(narration)
    print(f"Narration ready: {total:.2f}s", flush=True)

    words, wsegs = transcribe_words(narration)
    spans, slots = compute_slots(narration, words, wsegs, total,
                                 len(items))
    for i, (s, e) in enumerate(spans, 1):
        print(f"sentence {i}: {s:.2f} -> {e:.2f} ({e - s:.2f}s)", flush=True)
    print(f"{len(slots)} image slots (threshold {SPLIT_THRESHOLD}s)",
          flush=True)

    clips = []
    seen_split = {}
    for j, (s, e, si) in enumerate(slots, 1):
        it = items[si]
        is_second = seen_split.get(si, False)
        seen_split[si] = True
        if is_second:
            prompt = it["p2"] or (it["p1"] + ", closer view, different angle")
        else:
            prompt = it["p1"]
        full_prompt = (image_style.replace("{term}", prompt)
                       if "{term}" in image_style else prompt)
        img = os.path.join(OUT_DIR, f"slot{j:02d}.png")
        clip = os.path.join(OUT_DIR, f"slot{j:02d}.mp4")
        print(f"slot {j}: {s:.2f} -> {e:.2f} image: {prompt[:50]}",
              flush=True)
        sb.gen_image(full_prompt, img)
        make_image_clip(img, e - s, clip)
        clips.append(clip)

    video_only = os.path.join(OUT_DIR, "video.mp4")
    lst = os.path.join(OUT_DIR, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    sb.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
            "-c", "copy", video_only])
    muxed = os.path.join(OUT_DIR, "muxed.mp4")
    sb.run(["ffmpeg", "-y", "-i", video_only, "-i", narration,
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
            "-ar", "48000", muxed])
    mixed = os.path.join(OUT_DIR, "mixed.mp4")
    sb.add_bgm(muxed, mixed)
    # Final polish: fade the audio out so the file never ends mid-waveform
    # (an abrupt cut at full volume is heard as a click/crackle).
    final = os.path.join(OUT_DIR, "final-1.mp4")
    dur = sb.probe_duration(mixed)
    fade_st = max(dur - 0.6, 0)
    sb.run(["ffmpeg", "-y", "-i", mixed, "-map", "0:v", "-map", "0:a",
            "-filter_complex",
            f"[1:a]afade=t=out:st={fade_st:.3f}:d=0.6[a]",
            "-c:v", "copy", "-c:a", "aac", "-ar", "48000", final])
    print(f"DONE {final} duration={sb.probe_duration(final):.2f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
