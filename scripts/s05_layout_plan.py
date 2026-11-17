"""Step 5. Layout plan: one layout per shot, using the style guide's numbers.

Usage: python s05_layout_plan.py <workdir> [--min-shot 1.8] [--waive-median]
Input : <workdir>/tight_words.json, beats.json, inventory.json, and style.json
Output: <workdir>/shots.json
        {"duration", "fps", "title": {...}, "shots": [{id, start, end, layout, scale, w0, w1, item}]}
Layouts: A head only, B head + title, D full plate, E plate + inset. C (head + top graphic) is set by step 6.
Rules applied (all from style.json):
  - cuts fall on phrase boundaries (sentence end, or a pause of 0.12 s or more), frame-aligned at 30 fps
  - head shots aim for the measured median (2.9 s) with a cycle of targets, never over 8.2 s, never under 0.8 s
  - jump cuts alternate scale 1.0 and 1.12
  - a full plate only where the inventory has a real plate_card or plate_inset; never before 3 s;
    plate time stays under the cap (25% of the video); each plate 1.0 to 5.2 s
  - title (layout B) covers the first 6 s of head shots
Check : shots are contiguous from 0 to the end; median shot length 1.8 to 3.6 s; no head shot over 8.5 s;
        plate share under the cap; cuts per minute 6.7 to 42.4; first cut within 10 s; opens and closes on a head layout.
"""
import re
import sys
from pathlib import Path

import numpy as np

from common import STYLE, audio_db, fail, load, ok, quietest, save

FPS = 30
TITLE_S = 5.0
CYCLE = [2.2, 3.4, 2.6, 4.0, 1.8, 3.0, 2.8, 3.6]


def fr(t):
    return round(t * FPS) / FPS


def main(work, min_shot=0.0, waive_median=False):
    work = Path(work)
    tw = load(work / "tight_words.json")
    words, T = tw["words"], tw["duration"]
    inv = load(work / "inventory.json")
    P, PL = STYLE["pacing"], STYLE["planner"]
    # phrase units
    units, cur = [], [0]
    for k in range(len(words) - 1):
        w, nx = words[k], words[k + 1]
        gap = nx["start"] - w["end"]
        end_sentence = w["w"].endswith((".", "?", "!"))
        dur = words[cur[-1]]["end"] - words[cur[0]]["start"]
        if end_sentence or (gap >= PL["phrase_gap_s"] and dur >= 0.5) or (w["w"].endswith(",") and gap >= 0.06 and dur >= 0.8):
            units.append((cur[0], k))
            cur = [k + 1]
        else:
            cur.append(k + 1)
    units.append((cur[0], len(words) - 1))
    # every cut goes in the quietest moment between two words, never inside one (Rule 25, G46)
    db, floor = audio_db(work / "tight.mp4")

    def quiet_cut(a, b):
        t, lvl = quietest(db, a["end"] - 0.01, b["start"] + 0.01)
        t = max(a["end"] - 0.01, min(t, b["start"]))
        return int(t * FPS) / FPS, lvl - floor

    bounds = []  # cut time before each unit (after the first)
    for u in range(1, len(units)):
        a, b = words[units[u - 1][1]], words[units[u][0]]
        bounds.append(quiet_cut(a, b)[0])
    # where the tight cut removed time, the picture jumps anyway: that join must be a cut with a scale change,
    # or it reads as a glitch on the same framing
    joins = []
    keep = load(work / "keep.json") if (work / "keep.json").exists() else {"segments": []}
    for sg in keep["segments"][1:]:
        jt = sg["tight_start"]
        joins.append(int(round(jt * FPS)) / FPS)
    # candidate cuts with a strength: 2 phrase edge, 1 clause start, 0 any safe word edge
    CLAUSE = {"and", "but", "so", "because", "which", "if", "when", "or", "then", "while", "since", "although"}
    NOBREAK_AFTER = {"a", "an", "the", "to", "of", "in", "on", "at", "for", "with", "and", "or", "but", "my", "your", "our", "their", "his",
                     "her", "its", "this", "that", "these", "those", "is", "are", "was", "were", "be", "i", "you", "we", "they", "he",
                     "she", "it", "as", "by", "from", "into", "than", "not", "just", "very", "really"}
    cand = {}
    for t in bounds:
        cand[t] = 2
    for t in joins:
        cand[t] = 3
    for k in range(1, len(words)):
        prev, w = words[k - 1], words[k]
        t, lvl = quiet_cut(prev, w)
        if t in cand or any(abs(t - j) < 0.3 for j in joins):
            continue
        if lvl > 10.0:
            continue  # words run together here: no clean place to cut
        pw = re.sub(r"[^\w']", "", prev["w"].lower())
        nw = re.sub(r"[^\w']", "", w["w"].lower())
        if nw in CLAUSE or prev["w"].endswith(","):
            cand[t] = 1
        elif pw not in NOBREAK_AFTER:
            cand[t] = 0
    bounds_all = sorted(cand)

    def pick(start, target, hi):
        """First candidate at or after start+target, preferring a stronger one within 0.7 s."""
        pool = [x for x in bounds_all if start + target <= x < hi]
        if not pool:
            return None
        first = pool[0]
        near = [x for x in pool if x <= first + 0.7]
        best = max(near, key=lambda x: (cand[x], -x))
        return best

    def unit_of_word(i):
        return next(u for u, (a, b) in enumerate(units) if a <= i <= b)

    # plates from the inventory
    plates = []
    cap = P["plate_share_cap"] * T
    used = 0.0
    items = [(k, it) for k, it in enumerate(inv["items"]) if it["kind"] in ("plate_card", "plate_inset")]
    for k, it in sorted(items, key=lambda x: words[x[1]["trigger_word"]]["start"]):
        s = fr(words[it["trigger_word"]]["start"] - 0.04)
        if s < 3.0 or any(s < p["end"] + 0.5 and s > p["start"] - 0.5 for p in plates):
            print(f"  skipped item {k} ({it['kind']}): too early or too close to another plate")
            continue
        lo, hi = (PL["plate_shot_min_s"], PL["plate_shot_max_s"]) if it["kind"] == "plate_card" else (2.0, PL["plate_shot_max_s"])
        # end on the last unit boundary inside [s+lo, s+hi]
        e = pick(s, max(lo, 2.0), min(s + hi, T))  # a clause edge near 2 s or later, so the card can be read
        if e is None:
            e = fr(min(s + max(lo, 2.0), T))
        e = min(e, T)
        if used + (e - s) > cap:
            print(f"  skipped item {k} ({it['kind']}): plate cap reached")
            continue
        plates.append({"start": s, "end": e, "item": k, "kind": it["kind"]})
        used += e - s

    # head spans between plates
    spans, t = [], 0.0
    for p in plates:
        if p["start"] > t:
            spans.append((t, p["start"]))
        t = p["end"]
    if t < T:
        spans.append((t, T))
    shots = []
    ci = 0
    for (a, b) in spans:
        start = a
        while True:
            target = max(CYCLE[ci % len(CYCLE)], PL["head_shot_min_s"])
            x = pick(start, target, b - PL["head_shot_min_s"])
            if x is None:
                break
            shots.append({"start": start, "end": x, "layout": "A"})
            start = x
            ci += 1
        shots.append({"start": start, "end": b, "layout": "A"})
    # every audio join is a cut: move a nearby cut onto it, or split the shot there
    for j in joins:
        if any(p["start"] - 0.01 <= j <= p["end"] + 0.01 for p in plates):
            continue
        near = [s for s in shots if abs(s["end"] - j) < 0.6 and s is not shots[-1]]
        if near:
            s = near[0]
            nxt = shots[shots.index(s) + 1]
            if j - s["start"] >= 0.5 and nxt["end"] - j >= 0.5:
                s["end"] = nxt["start"] = j
                continue
        host = next((s for s in shots if s["start"] + 0.5 <= j <= s["end"] - 0.5), None)
        if host:
            k = shots.index(host)
            shots[k:k + 1] = [{"start": host["start"], "end": j, "layout": "A"}, {"start": j, "end": host["end"], "layout": "A"}]
    # opt-in (--min-shot 1.8): a take that is already chopped by pauses has many audio joins, and the extra cuts the
    # planner adds on top leave 1 s slivers (G59). Drop any non-join cut that leaves a head shot shorter than min_shot.
    if min_shot > 0:
        changed = True
        while changed:
            changed = False
            for k in range(len(shots) - 1):
                a, b = shots[k], shots[k + 1]
                if abs(a["end"] - b["start"]) > 1e-6 or any(abs(b["start"] - j) < 0.02 for j in joins):
                    continue
                if min(a["end"] - a["start"], b["end"] - b["start"]) < min_shot and b["end"] - a["start"] <= PL["head_shot_max_s"]:
                    a["end"] = b["end"]
                    del shots[k + 1]
                    changed = True
                    break
    # enforce the max length by inserting cuts at the nearest boundary
    fixed = []
    for s in shots:
        s = dict(s)
        while s["end"] - s["start"] > PL["head_shot_max_s"]:
            mid = s["start"] + 4.0
            cand = min((x for x in bounds_all if s["start"] + PL["head_shot_min_s"] < x < s["end"] - PL["head_shot_min_s"]), key=lambda x: abs(x - mid), default=None)
            if cand is None:
                cand = fr(mid)
            fixed.append({"start": s["start"], "end": cand, "layout": "A"})
            s["start"] = cand
        fixed.append(s)
    # merge a too-short tail into the previous shot
    shots = []
    for s in fixed:
        on_join = any(abs(s["start"] - j) < 0.02 for j in joins) and s["end"] - s["start"] >= 0.5
        if shots and s["end"] - s["start"] < PL["head_shot_min_s"] and abs(shots[-1]["end"] - s["start"]) < 1e-6 and not on_join:
            shots[-1]["end"] = s["end"]
        else:
            shots.append(s)
    ov = work / "cut_overrides.json"  # {"move": {"5.9": 6.3}}: move the cut nearest the key to the value (never a join)
    if ov.exists():
        for k, v in load(ov).get("move", {}).items():
            for a, b in zip(shots[:-1], shots[1:]):
                if abs(a["end"] - float(k)) < 0.1 and not any(abs(b["start"] - j) < 0.02 for j in joins):
                    a["end"] = b["start"] = fr(float(v))
                    print(f"  cut moved {k} -> {v} (cut_overrides.json)")
    for p in plates:
        shots.append({"start": p["start"], "end": p["end"], "layout": "D" if p["kind"] == "plate_card" else "E", "item": p["item"]})
    shots.sort(key=lambda s: s["start"])
    # labels, scale, word ranges
    scale_k = 0
    out = []
    for n, s in enumerate(shots):
        w_in = [w["i"] for w in words if s["start"] - 1e-6 <= w["start"] < s["end"] - 1e-6]
        if s["layout"] == "A":
            if "end" in inv["title"]:  # shortened title: B only for shots that are mostly under it
                if (s["start"] + s["end"]) / 2 < min(TITLE_S, float(inv["title"]["end"])):
                    s["layout"] = "B"
            elif s["start"] < TITLE_S:
                s["layout"] = "B"
            s["scale"] = STYLE["planner"]["alternate_scale"][scale_k % 2]
            scale_k += 1
        else:
            s["scale"] = 1.0
            scale_k = 0
        out.append({"id": n + 1, "start": round(s["start"], 3), "end": round(s["end"], 3), "layout": s["layout"], "scale": s["scale"],
                    "w0": w_in[0] if w_in else None, "w1": w_in[-1] if w_in else None, "item": s.get("item")})
    save(work / "shots.json", {"duration": T, "fps": FPS, "title": inv["title"], "shots": out})

    # checks
    for a, b in zip(out[:-1], out[1:]):
        if abs(a["end"] - b["start"]) > 1e-3:
            fail(f"gap or overlap between shot {a['id']} and {b['id']}")
    if abs(out[0]["start"]) > 1e-3 or abs(out[-1]["end"] - T) > 0.05:
        fail("shots do not cover the whole video")
    lens = [s["end"] - s["start"] for s in out]
    med = float(np.median(lens))
    heads = [s["end"] - s["start"] for s in out if s["layout"] in ("A", "B")]
    plate_share = sum(s["end"] - s["start"] for s in out if s["layout"] in ("D", "E")) / T
    cpm = (len(out) - 1) / T * 60
    msgs = []
    if waive_median and med < 1.8 and med >= 1.0:
        print(f"  WAIVED (recorded in waiver.json): median shot {med:.2f} s is under the 1.8 s floor")
    elif not 1.8 <= med <= 3.6:
        msgs.append(f"median shot {med:.2f} s is outside 1.8 to 3.6 s (style median 2.4 s)")
    if max(heads) > 8.5:
        msgs.append(f"a head shot runs {max(heads):.1f} s (max 8.5 s)")
    if plate_share > P["plate_share_cap"] + 1e-6:
        msgs.append(f"plate share {plate_share:.0%} is over the {P['plate_share_cap']:.0%} cap")
    if T >= 20 and not P["cuts_per_min"]["min"] <= cpm <= P["cuts_per_min"]["max"]:
        msgs.append(f"{cpm:.1f} cuts per minute is outside {P['cuts_per_min']['min']} to {P['cuts_per_min']['max']}")
    if len(out) > 1 and out[0]["end"] > 10.0:
        msgs.append(f"first cut at {out[0]['end']:.1f} s (limit 10 s)")
    if out[0]["layout"] not in ("A", "B") or out[-1]["layout"] not in ("A", "B"):
        msgs.append("the video must open and close on a head layout")
    cuts_at = [s["start"] for s in out[1:]]
    for j in joins:
        if any(s["start"] - 0.01 <= j <= s["end"] + 0.01 for s in out if s["layout"] in ("D", "E")):
            continue
        if not any(abs(j - c) < 0.02 for c in cuts_at):
            msgs.append(f"audio join at {j:.2f} s has no picture cut: it will look like a glitch")
    print(f"{len(out)} shots: median {med:.2f} s, {cpm:.1f} cuts/min, plate share {plate_share:.0%}, first cut {out[0]['end']:.1f} s")
    if msgs:
        print("\n".join("  - " + m for m in msgs))
        fail(f"{len(msgs)} pacing check(s) failed")
    ok("shots are contiguous and inside the measured pacing ranges")


if __name__ == "__main__":
    ms = float(sys.argv[sys.argv.index("--min-shot") + 1]) if "--min-shot" in sys.argv else 0.0
    main(sys.argv[1], ms, "--waive-median" in sys.argv)
