#!/usr/bin/env python3
"""Timed builder (Mehdi's method, 2026-11-09).

  1. ONE Gemini TTS call for the whole script (natural flow, 1 request/day).
  2. Optional speed-up (atempo, pitch preserved) applied to the narration.
  3. Sentence boundaries measured from the actual audio (faster-whisper
     word timestamps -> largest inter-word gaps are the sentence pauses).
  4. Mehdi's 5-second rule: a sentence of length L gets
     ceil(L / SPLIT_THRESHOLD) image slots, split at its largest
     internal pauses, so no image sits much longer than the threshold.
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
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segmented_build as sb  # noqa: E402  (reuse tts/image/ffmpeg helpers)

OUT_DIR = os.path.join("storage", "tasks", "timed")
SPLIT_THRESHOLD = float(os.environ.get("SPLIT_THRESHOLD", "5.0"))


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
                  n_sentences, threshold=SPLIT_THRESHOLD, sent_words=None):
    """Sentence spans anchored on the word stream.

    Expected boundary positions come from each sentence's share of the
    script's words (speech rate is roughly uniform); each boundary then
    snaps to the largest pause (inter-word gap) near its expected spot.
    Whisper's own segments are deliberately NOT trusted for boundaries:
    on one take they swallowed the first three sentences into a single
    segment and every image drifted ~10s behind the voice. Slots: a
    sentence of length L gets ceil(L / threshold) images, split at its
    largest internal pauses, so no image sits much longer than the
    threshold. (audio_path/segments kept for signature stability.)
    """
    if sent_words and len(sent_words) == n_sentences and sum(sent_words) > 0:
        total_w = float(sum(sent_words))
        expected = [0.0]
        acc = 0
        for c in sent_words[:-1]:
            acc += c
            expected.append(total_dur * acc / total_w)
        expected.append(total_dur)
    else:
        step = total_dur / max(n_sentences, 1)
        expected = [i * step for i in range(n_sentences + 1)]

    gaps = []  # (size, start, end) of pauses between consecutive words
    for i in range(len(words) - 1):
        g = words[i + 1][0] - words[i][1]
        if g > 0.05:
            gaps.append((g, words[i][1], words[i + 1][0]))

    bounds = [0.0]
    for k in range(1, n_sentences):
        exp = expected[k]
        lo = max(bounds[-1] + 0.8, exp - 2.5)
        hi = min(total_dur - 0.8 * (n_sentences - k), exp + 2.5)
        cand = [g for g in gaps if lo <= (g[1] + g[2]) / 2.0 <= hi]
        if cand:
            g = max(cand, key=lambda t: t[0])
            bounds.append((g[1] + g[2]) / 2.0)
        else:
            bounds.append(min(max(exp, lo), hi))
    bounds.append(total_dur)
    spans = [(bounds[i], bounds[i + 1]) for i in range(n_sentences)]

    def split_span(s, e):
        n = max(1, math.ceil((e - s) / threshold - 1e-9))
        if n == 1:
            return [(s, e)]
        inside = sorted(
            (g for g in gaps if s + 1.6 <= (g[1] + g[2]) / 2.0 <= e - 1.6),
            key=lambda t: -t[0])
        cuts = []
        for g in inside:
            mid = (g[1] + g[2]) / 2.0
            if all(abs(mid - c) >= 1.6 for c in cuts):
                cuts.append(mid)
            if len(cuts) == n - 1:
                break
        while len(cuts) < n - 1:
            edges = [s] + sorted(cuts) + [e]
            k = max(range(len(edges) - 1),
                    key=lambda i: edges[i + 1] - edges[i])
            cuts.append((edges[k] + edges[k + 1]) / 2.0)
        pts = [s] + sorted(cuts) + [e]
        return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]

    slots = []
    for si, (s, e) in enumerate(spans):
        for (a, b) in split_span(s, e):
            slots.append((a, b, si))
    # Hard guarantee: no image ever sits longer than threshold + 1s.
    fixed = []
    for (a, b, si) in slots:
        while b - a > threshold + 1.0:
            mid = (a + b) / 2.0
            fixed.append((a, mid, si))
            a = mid
        fixed.append((a, b, si))
    return spans, fixed


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
    sent_words = [len(normalize_fa(it["text"])) for it in items]
    spans, slots = compute_slots(narration, words, wsegs, total,
                                 len(items), sent_words=sent_words)
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
    sb.run(["ffmpeg", "-y", "-i", mixed,
            "-filter_complex",
            f"[0:a]afade=t=out:st={fade_st:.3f}:d=0.6[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-ar", "48000", final])
    print(f"DONE {final} duration={sb.probe_duration(final):.2f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
