"""Step 2s (optional). Filmed in sections: pick the best take of every script section and join them (Rule 34).

Usage: python s02s_sections.py <workdir> --script <script.txt> <clip1> [<clip2> ...]
       One line of script.txt = one section. Clips can each hold one section, several sections, or several tries of one.
Input : the raw clips (any order), the script
Output: <workdir>/takes/tNN/  intake and words for each clip
        <workdir>/source_norm.mp4  the chosen sections joined in script order, each cut in a pause
        <workdir>/words.json       their words, with "hard_breaks": the word index where each new section starts
        <workdir>/sections.json    which clip and time each section came from, coverage, and what he said differently
Then  : continue with s02b_tightcut.py (normal mode, removes dead air, every section join becomes a picture cut)
        Both read "hard_breaks".
How   : for each section, every place in every clip where its words were spoken is a candidate; the best coverage wins,
        and on a tie the later try wins (people get it right on the last go).
Check : every section found with 80% or more of its words; each cut sits in a pause (noise floor + 9 dB at most).
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

from common import FFMPEG, audio_db, fail, load, ok, probe, quietest, run, save, silent_edge
from s02b_tightcut import refine_edges

HERE = Path(__file__).resolve().parent


def norm(w):
    return re.sub(r"[^\w']", "", w.lower().replace("’", "'"))


def best_span(stoks, toks):
    """Best (coverage, first, last) of the section tokens in this clip, latest wins on a tie."""
    best, key = (0.0, None, None), None
    starts = [i for i in range(len(toks)) if toks[i] == stoks[0]] or [i for i in range(len(toks)) if toks[i] in stoks[:3]] or [0]
    for s in starts:
        seg = toks[s:s + len(stoks) + 8]
        sm = difflib.SequenceMatcher(None, stoks, seg, autojunk=False)
        pairs = [(b.a + k, s + b.b + k) for b in sm.get_matching_blocks() for k in range(b.size)]
        if not pairs:
            continue
        cov = len(pairs) / len(stoks)
        # most words first, then a match that starts at the section's first word, then the latest try
        k_ = (round(cov, 6), -pairs[0][0], -pairs[-1][0] + len(stoks), s)
        if key is None or k_ > key:
            key, best = k_, (cov, pairs[0][1], pairs[-1][1])
    return best


def main(work, script, clips):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    sections = [ln.strip() for ln in Path(script).read_text(encoding="utf-8").splitlines() if ln.strip()]
    takes = []
    for k, c in enumerate(clips, 1):
        td = work / "takes" / f"t{k:02d}"
        td.mkdir(parents=True, exist_ok=True)
        for step in (["s01_intake.py", str(c), str(td)], ["s02_transcribe.py", str(td)]):
            if step[0] == "s01_intake.py" and (td / "source_norm.mp4").exists():
                continue
            if step[0] == "s02_transcribe.py" and (td / "words.json").exists():
                continue
            r = subprocess.run([sys.executable, str(HERE / step[0])] + step[1:], capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"{step[0]} failed on {c}:\n{(r.stdout + r.stderr)[-400:]}")
        words = refine_edges(load(td / "words.json")["words"], td / "source_norm.mp4")
        db, floor = audio_db(td / "source_norm.mp4")
        takes.append({"clip": str(c), "dir": td, "words": words, "toks": [norm(w["w"]) for w in words], "db": db, "floor": floor})

    chosen, problems = [], []
    for si, line in enumerate(sections):
        stoks = [t for t in (norm(x) for x in re.findall(r"[\w'’]+", line)) if t]
        best = None
        for ti, tk in enumerate(takes):
            cov, a, b = best_span(stoks, tk["toks"])
            if a is None:
                continue
            if best is None or cov > best[0] + 1e-9 or (abs(cov - best[0]) < 1e-9 and (ti, a) > (best[1], best[2])):
                best = (cov, ti, a, b)
        if best is None or best[0] < 0.8:
            problems.append(f"section {si + 1} \"{line[:40]}\" not found with 80% of its words (best {0 if best is None else best[0]:.0%})")
            continue
        cov, ti, a, b = best
        tk = takes[ti]
        w = tk["words"]
        lo = max(0.0, w[a]["start"] - 0.6, (w[a - 1]["end"] + 0.03) if a > 0 else 0.0)
        # cut in the first real silence before the line (Whisper and soft onsets like "h" can start late)
        t0 = silent_edge(tk["db"], tk["floor"], w[a]["start"] - 0.04, max(0.0, w[a]["start"] - 1.0, lo - 0.4 if a else 0.0), -1)
        if t0 is None:
            t0, _ = quietest(tk["db"], lo, w[a]["start"] - 0.04)
        hi = min(len(tk["db"]) / 100.0, w[b]["end"] + 0.6, (w[b + 1]["start"] - 0.03) if b + 1 < len(w) else 1e9)
        t1 = silent_edge(tk["db"], tk["floor"], w[b]["end"] + 0.06, min(hi + 0.4, w[b]["end"] + 1.0), +1)
        if t1 is None:
            t1, _ = quietest(tk["db"], w[b]["end"] + 0.06, hi)
        for edge in (t0, t1):
            i = int(round(edge * 100))
            lvl = float(tk["db"][max(0, i - 1):i + 2].max() - tk["floor"])
            if lvl > 9.0:
                problems.append(f"section {si + 1}: the cut at {edge:.2f} s in {Path(tk['clip']).name} is on voiced sound ({lvl:.1f} dB over the room)")
        said = [w[i]["w"] for i in range(a, b + 1)]
        extra = [x for x in said if norm(x) not in stoks]
        chosen.append({"section": si + 1, "line": line, "clip": tk["clip"], "src": str(tk["dir"] / "source_norm.mp4"), "start": round(t0, 3), "end": round(t1, 3),
                       "coverage": round(cov, 3), "first": a, "last": b, "said_not_in_script": extra, "ti": ti})
    if problems:
        print("\n".join("  - " + p for p in problems))
        fail(f"{len(problems)} section problem(s)")

    # join the chosen spans in script order into one source, and carry their words over with new times
    parts, labels, out_words, breaks, t = [], [], [], [], 0.0
    srcs = sorted({c["src"] for c in chosen})
    for k, c in enumerate(chosen):
        n = srcs.index(c["src"])
        parts.append(f"[{n}:v]trim=start={c['start']}:end={c['end']},setpts=PTS-STARTPTS[v{k}];"
                     f"[{n}:a]atrim=start={c['start']}:end={c['end']},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={c['end'] - c['start'] - 0.012:.3f}:d=0.012[a{k}]")
        labels.append(f"[v{k}][a{k}]")
        breaks.append(len(out_words))
        for w in takes[c["ti"]]["words"][c["first"]:c["last"] + 1]:
            out_words.append({"i": len(out_words), "w": w["w"], "start": round(t + w["start"] - c["start"], 3), "end": round(t + w["end"] - c["start"], 3),
                              "p": w.get("p", 1.0), "section": c["section"]})
        c["tight_start"] = round(t, 3)
        t += c["end"] - c["start"]
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(chosen)}:v=1:a=1[v][a]"
    (work / "sections_filter.txt").write_text(fc, encoding="utf-8")
    cmd = [FFMPEG, "-v", "error", "-y"]
    for s in srcs:
        cmd += ["-i", s]
    cmd += ["-/filter_complex", work / "sections_filter.txt", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "fast",
            "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", work / "source_norm.mp4"]
    r = run(cmd)
    if r.returncode != 0:
        fail("joining sections failed: " + r.stderr[-400:])
    dur = float(probe(work / "source_norm.mp4")["format"]["duration"])
    if abs(dur - t) > 0.15:
        fail(f"joined video is {dur:.2f} s, plan says {t:.2f} s")
    save(work / "words.json", {"language": "en", "duration": round(dur, 2), "words": out_words, "hard_breaks": breaks[1:]})
    (work / "transcript.txt").write_text(" ".join(w["w"] for w in out_words), encoding="utf-8")
    save(work / "sections.json", {"sections": [{k: v for k, v in c.items() if k != "ti"} for c in chosen]})
    intake0 = takes[chosen[0]["ti"]]["dir"] / "intake.json"
    if intake0.exists():
        save(work / "intake.json", load(intake0))
    for c in chosen:
        print(f"  section {c['section']}: {Path(c['clip']).name} {c['start']:.2f}-{c['end']:.2f} s, {c['coverage']:.0%} of the words"
              + (f", also said {c['said_not_in_script']}" if c["said_not_in_script"] else ""))
    ok(f"{len(chosen)} sections joined in script order, {dur:.1f} s, every cut in a pause")


if __name__ == "__main__":
    a = sys.argv
    k = a.index("--script")
    sc = a[k + 1]
    rest = [x for i, x in enumerate(a[2:], 2) if i not in (k, k + 1)]
    main(a[1], sc, rest)
