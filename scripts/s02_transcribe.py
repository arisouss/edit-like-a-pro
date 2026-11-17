"""Step 2a. Transcribe with local Whisper, word by word.

Usage: python s02_transcribe.py <workdir> [--model small] [--lang he]
Input : <workdir>/source_norm.mp4
Output: <workdir>/words.json  [{i, w, start, end, p}]  and <workdir>/transcript.txt
Check : at least 5 words, speech covers at least 35% of the duration, every word has start < end.
Audio is decoded with ffmpeg and passed as an array (the bundled PyAV is too old to open files).
"""
import sys
from pathlib import Path

import numpy as np

from common import FFMPEG, MODELS, fail, ok, run, save


def main(workdir, model="small", lang=None):
    work = Path(workdir)
    src = work / "source_norm.mp4"
    if not src.exists():
        fail("source_norm.mp4 missing. Run step 1 first.")
    raw = run([FFMPEG, "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], text=False).stdout
    audio = np.frombuffer(raw, np.float32)
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8", download_root=str(MODELS))
    # English keeps the filler-friendly prompt. Other languages get no English prompt (it pushes Whisper to translate or mangle).
    prompt = "Um, uh, so, I mean, like, you know." if lang in (None, "en") else None
    segs, info = m.transcribe(audio, word_timestamps=True, vad_filter=False, beam_size=5,
                              condition_on_previous_text=False, language=lang, initial_prompt=prompt)
    words = []
    for s in segs:
        for w in s.words:
            if w.end <= w.start:
                continue
            words.append({"i": len(words), "w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3), "p": round(float(w.probability), 3)})
    dur = len(audio) / 16000
    if len(words) < 5:
        fail(f"only {len(words)} words found. Is there speech?")
    speech = sum(w["end"] - w["start"] for w in words)
    if speech < 0.35 * dur:
        fail(f"speech covers {speech / dur:.0%} of the video (need 35%). Check the audio.")
    save(work / "words.json", {"language": info.language, "duration": round(dur, 2), "words": words})
    (work / "transcript.txt").write_text(" ".join(w["w"] for w in words), encoding="utf-8")
    low = sum(1 for w in words if w["p"] < 0.5)
    print(f"{len(words)} words, language {info.language}, {low} low-confidence words")
    ok(f"words.json written, speech {speech / dur:.0%} of {dur:.1f} s")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[a.index("--model") + 1] if "--model" in a else "small", a[a.index("--lang") + 1] if "--lang" in a else None)
