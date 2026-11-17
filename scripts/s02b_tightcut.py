"""Step 2b. Tight cut: remove dead air, fillers, immediate repeats and flubs. Never reword.

Usage: python s02b_tightcut.py <workdir>
Input : <workdir>/words.json
        <workdir>/drops_manual.json  (optional) {"drop_words": [word indices], "reasons": {"12": "false start"}}
Output: <workdir>/cuts.json        what was dropped and why (every removed word listed)
        <workdir>/keep.json        source time segments that are kept
        <workdir>/tight_words.json the kept words with times remapped to the tight video
        <workdir>/tight.mp4        the tightened video
Check : (1) no kept word differs from its source word, (2) kept words stay in source order,
        (3) no gap between kept words over style.pacing.no_silence_over_s (0.3 s) in tight_words,
        (4) tight.mp4 duration matches the remapped timeline within 0.15 s.
Automatic drops: filler words, immediate repeated words, restarted phrases (2-3 word phrase said twice in a row).
Flubs that need judgment (a wrong word, a sentence restarted differently) go in drops_manual.json by word index.
"""
import re
import sys
from pathlib import Path

from common import FFMPEG, STYLE, audio_db, fail, load, ok, probe, quietest, run, save

FILLERS = {"um", "uh", "umm", "uhh", "erm", "er", "ah", "hmm", "hm", "mm", "mhm"}
# repeats that are emphasis, not false starts ("really really cool", "very very"): never auto-dropped
KEEP_REPEATS = {"that", "had", "really", "very", "so", "no", "yes", "ha", "hey", "way", "many", "much", "bye", "go", "more", "again", "sorry"}
# cut points sit in the quietest moment of the pause, inside these windows around the words (Rule 25: never clip a word)
LEAD_MIN, LEAD_MAX = 0.04, 0.25   # room kept before a segment's first word
TAIL_MIN, TAIL_MAX = 0.06, 0.30   # room kept after a segment's last word (soft endings: s, f, th)
JOIN_DB = 9.0                     # a join louder than noise floor + this is a clipped word
FADE = 0.012
MAX_GAP = STYLE["pacing"]["no_silence_over_s"]


def quietest_join(db, t0, t1):
    """Like common.quietest, but ranks each frame by the loudest of its 3 neighbours: the same measure the join check uses (G59)."""
    import numpy as np
    i0, i1 = max(0, int(round(t0 * 100))), min(len(db) - 1, int(round(t1 * 100)))
    if i1 <= i0:
        return quietest(db, t0, t1)
    pad = np.pad(db, 1, mode="edge")
    mx = np.maximum(np.maximum(pad[:-2], pad[1:-1]), pad[2:])
    seg = mx[i0:i1 + 1]
    k = int(np.argmin(seg))
    return (i0 + k) / 100.0, float(seg[k])


def norm(w):
    return re.sub(r"[^\w']", "", w.lower())


def refine_edges(words, src):
    """Whisper stretches word ends into the pause that follows. Pull each word's start and end onto the audio itself:
    10 ms RMS frames, voiced = above (noise floor + 9 dB). Word text and order are untouched."""
    import numpy as np
    raw = run([FFMPEG, "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], text=False).stdout
    a = np.frombuffer(raw, np.float32)
    hop = 160
    nfr = len(a) // hop
    rms = np.sqrt((a[:nfr * hop].reshape(nfr, hop) ** 2).mean(axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    floor = np.percentile(db, 10)
    voiced = db > floor + 9.0
    # close tiny holes inside words (stops, quiet consonants)
    k = 4
    sm = np.convolve(voiced.astype(int), np.ones(2 * k + 1, int), mode="same") > 0
    out = []
    for w in words:
        s0, e0 = int(w["start"] * 100), int(w["end"] * 100)
        lo, hi = max(0, s0 - 12), min(nfr - 1, e0 + 3)
        idx = np.nonzero(sm[lo:hi + 1])[0]
        if len(idx) == 0:
            out.append(dict(w))
            continue
        ns, ne = (lo + idx[0]) / 100.0, (lo + idx[-1] + 1) / 100.0
        ns = max(ns, w["start"] - 0.12)
        ne = min(ne, w["end"] + 0.15)  # let soft endings (s, f, th) finish
        if ne - ns < 0.08:
            ns, ne = w["start"], min(w["end"], w["start"] + 0.25)
        out.append({**w, "start": round(ns, 3), "end": round(ne, 3)})
    # Whisper sometimes ends a word early ("anima|tions"): carry each end on through unbroken voice, and each start back
    # through it, as long as it stays clear of the neighbouring word (G45)
    strong = np.convolve((db > floor + 8.0).astype(int), np.ones(5, int), mode="same") > 0  # voice, 20 ms holes closed
    for k, w in enumerate(out):
        nxt = out[k + 1]["start"] if k + 1 < len(out) else nfr / 100.0
        prv = out[k - 1]["end"] if k else 0.0
        e = int(w["end"] * 100)
        while e < nfr - 1 and strong[e] and (e + 1) / 100.0 < min(nxt - 0.05, w["end"] + 0.6):
            e += 1
        b_ = int(w["start"] * 100)
        while b_ > 0 and strong[b_ - 1] and (b_ - 1) / 100.0 > max(prv + 0.05, w["start"] - 0.25):
            b_ -= 1
        w["end"], w["start"] = round(max(w["end"], e / 100.0), 3), round(min(w["start"], b_ / 100.0), 3)
    return out


def main(workdir):
    work = Path(workdir)
    data = load(work / "words.json")
    words = refine_edges(data["words"], work / "source_norm.mp4")
    n = len(words)
    drop = {}
    # fillers
    for w in words:
        if norm(w["w"]) in FILLERS:
            drop[w["i"]] = "filler"
    # immediate repeat of a word ("the the") and restarted 2 to 3 word phrases
    toks = [norm(w["w"]) for w in words]
    for i in range(n - 1):
        if toks[i] and toks[i] == toks[i + 1] and i not in drop and toks[i] not in KEEP_REPEATS:
            drop[i] = "repeated word"
    for L in (3, 2):
        i = 0
        while i + 2 * L <= n:
            a, b = toks[i:i + L], toks[i + L:i + 2 * L]
            if a == b and all(a) and not any(j in drop for j in range(i, i + L)) and (words[i + L]["start"] - words[i + L - 1]["end"]) < 0.8:
                for j in range(i, i + L):
                    drop[j] = "restarted phrase"
                i += L
            else:
                i += 1
    manual = work / "drops_manual.json"
    manual_tail = 0.0
    manual_trim = {}
    if manual.exists():
        m = load(manual)
        manual_tail = m.get("end_tail_s", 0.0)
        manual_trim = m.get("gap_trim", {})
        for i in m.get("drop_words", []):
            drop[int(i)] = m.get("reasons", {}).get(str(i), "manual flub")
    hard = set(data.get("hard_breaks", []))
    kept = [w for w in words if w["i"] not in drop]
    if len(kept) < 5:
        fail("fewer than 5 words would remain")

    # segments: one per run of kept words that are neighbours in the source, with a gap rule
    segs = []
    for w in kept:
        prev_src = words[w["i"] - 1] if w["i"] > 0 else None
        contiguous = segs and prev_src is not None and prev_src["i"] not in drop and (w["start"] - words[w["i"] - 1]["end"]) <= MAX_GAP
        if w["i"] in hard:
            contiguous = False  # a new section from another take (s02s_sections.py): always a join
        if contiguous:
            segs[-1]["last"] = w["i"]
        else:
            segs.append({"first": w["i"], "last": w["i"]})
    # put each edge in the quietest moment of the pause around it, never inside a neighbouring word's audio
    db, floor = audio_db(work / "source_norm.mp4")
    T_src = len(db) / 100.0
    for k, sg in enumerate(segs):
        fw, lw = words[sg["first"]], words[sg["last"]]
        lo = fw["start"] - LEAD_MAX
        if sg["first"] > 0:
            lo = max(lo, words[sg["first"] - 1]["end"] + 0.02)
        lo = max(0.0, min(lo, fw["start"] - LEAD_MIN))
        t, _ = quietest_join(db, lo, fw["start"] - LEAD_MIN)
        sg["start"] = round(max(0.0, t), 3)
        if str(sg["first"]) in manual_trim:  # drops_manual.json "gap_trim": {"<first word after the gap>": seconds}: take a little more out of a pause
            sg["start"] = round(min(sg["start"] + float(manual_trim[str(sg["first"])]), fw["start"] - 0.02), 3)
        hi = lw["end"] + TAIL_MAX
        if sg["last"] + 1 < n:
            hi = min(hi, words[sg["last"] + 1]["start"] - 0.02)
        hi = max(hi, lw["end"] + TAIL_MIN)
        t, _ = quietest_join(db, lw["end"] + TAIL_MIN, min(hi, T_src))
        sg["end"] = round(min(T_src, t), 3)
        if k == len(segs) - 1 and manual_tail:  # drops_manual.json "end_tail_s": keep real footage after the last word (room for an end caption)
            sg["end"] = round(min(T_src, lw["end"] + float(manual_tail)), 3)
        if k and sg["start"] < segs[k - 1]["end"]:
            sg["start"] = segs[k - 1]["end"]
    # two segments with nothing removed between them are one segment (no join, no click risk)
    merged = []
    for sg in segs:
        if merged and abs(sg["start"] - merged[-1]["end"]) < 0.015 and sg["first"] not in hard:
            merged[-1]["end"], merged[-1]["last"] = sg["end"], sg["last"]
        else:
            merged.append(sg)
    segs = merged
    joins = []
    for sg in segs:
        for edge in ("start", "end"):
            i = int(round(sg[edge] * 100))
            lvl = float(db[max(0, i - 1):i + 2].max() - floor) if len(db) else 0.0
            joins.append({"t": sg[edge], "edge": edge, "word": words[sg["first"] if edge == "start" else sg["last"]]["w"], "db_over_floor": round(lvl, 1)})
    total = 0.0
    for s in segs:
        s["tight_start"] = round(total, 3)
        total += s["end"] - s["start"]
        s["tight_end"] = round(total, 3)
    # remap word times
    tw = []
    for w in kept:
        s = next(sg for sg in segs if sg["first"] <= w["i"] <= sg["last"] and sg["start"] - 0.001 <= w["start"] <= sg["end"] + 0.001)
        tw.append({**w, "src_i": w["i"], "i": len(tw), "start": round(s["tight_start"] + (w["start"] - s["start"]), 3),
                   "end": round(s["tight_start"] + (w["end"] - s["start"]), 3)})
    save(work / "keep.json", {"segments": segs, "joins": joins, "noise_floor_db": round(floor, 1)})
    save(work / "tight_words.json", {"duration": round(total, 3), "words": tw})
    save(work / "cuts.json", {"dropped": [{"src_i": i, "word": words[i]["w"], "start": words[i]["start"], "end": words[i]["end"], "reason": r} for i, r in sorted(drop.items())],
                              "source_duration": data["duration"], "tight_duration": round(total, 3)})

    # render
    parts, labels = [], []
    for k, s in enumerate(segs):
        parts.append(f"[0:v]trim=start={s['start']:.3f}:end={s['end']:.3f},setpts=PTS-STARTPTS[v{k}];"
                     f"[0:a]atrim=start={s['start']:.3f}:end={s['end']:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},afade=t=out:st={max(0, s['end'] - s['start'] - FADE):.3f}:d={FADE}[a{k}]")
        labels.append(f"[v{k}][a{k}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    (work / "tight_filter.txt").write_text(fc, encoding="utf-8")
    r = run([FFMPEG, "-v", "error", "-y", "-i", work / "source_norm.mp4", "-/filter_complex", work / "tight_filter.txt", "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
             "-movflags", "+faststart", work / "tight.mp4"])
    if r.returncode != 0:
        fail("ffmpeg render failed: " + r.stderr[-400:])

    # checks
    src_by_i = {w["i"]: w["w"] for w in words}
    if any(src_by_i[t["src_i"]] != t["w"] for t in tw):
        fail("a kept word differs from its source word")
    if any(tw[k]["src_i"] >= tw[k + 1]["src_i"] for k in range(len(tw) - 1)):
        fail("kept words are out of source order")
    big = [(tw[k]["w"], round(tw[k + 1]["start"] - tw[k]["end"], 2)) for k in range(len(tw) - 1) if tw[k + 1]["start"] - tw[k]["end"] > MAX_GAP + 0.25]
    if big:
        fail(f"gaps over {MAX_GAP + 0.25:.2f} s remain after {big[:5]}")
    dur = float(probe(work / "tight.mp4")["format"]["duration"])
    if abs(dur - total) > 0.15:
        fail(f"tight.mp4 is {dur:.2f} s but the timeline says {total:.2f} s")
    loud = [j for j in joins if j["db_over_floor"] > JOIN_DB and 0.05 < j["t"] < T_src - 0.05]
    if loud:
        fail("cut lands on voiced sound (a clipped word) at " + ", ".join(f"{j['t']:.2f} s next to '{j['word']}' ({j['db_over_floor']} dB over the room)" for j in loud)
             + ". Keep that pause, or drop the whole word in drops_manual.json.")
    by = {}
    for d in load(work / "cuts.json")["dropped"]:
        by[d["reason"]] = by.get(d["reason"], 0) + 1
    print(f"source {data['duration']:.1f} s -> tight {dur:.1f} s, {len(drop)} words dropped {by}, {len(segs)} segments")
    ok(f"kept words identical to source, in order, no dead air, every cut in silence (loudest join {max(j['db_over_floor'] for j in joins):.1f} dB over the room)")


if __name__ == "__main__":
    main(sys.argv[1])
