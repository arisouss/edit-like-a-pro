"""Step 6b. Check the effects layer (Rule 42): icons popping, words behind his head, background swaps,
full-screen takeovers and counters. Write $WD/fx.json by hand from the beats, then run this.

Usage : python3.12 s06b_fx.py "$WD"
fx.json: {"fx": [
  {"kind": "icon_pop", "start": 4.2, "end": 7.0, "icons": [{"name": "brain", "label": "Brain", "word": 41}, ...]},
  {"kind": "behind_words", "start": 1.0, "end": 3.2, "text": "AI EDITED", "word": 3},
  {"kind": "bg_swap", "start": 9.0, "end": 11.5, "word": 60, "bg": {"pattern": "<png>"} | {"image": "<png>", "scroll": true, "travel": 900} | {"scene": "IconSwarm", "props": {...}}},
  {"kind": "takeover", "start": 14.0, "end": 17.0, "word": 88, "scene": "Compare", "props": {...}},
  {"kind": "stat", "start": 20.0, "end": 22.5, "word": 120, "value": 51, "suffix": "%", "label": "less build time"}]}
  "word" = index in tight_words.json the effect lands on. Icons in icon_pop each name their own word.
  Icon names: files in assets/icons (Lucide). Scenes: IconSwarm, Kinetic, IconList, Compare, StatSlam, DocFly, CTA, PhotoPunch.
Check : kinds and scenes exist; every effect starts within 0.05 s of its word (each icon on its word); 1.2 to 6 s long;
        effects do not overlap each other, the title window or a full plate; behind_words and bg_swap need
        subject.webm (run cutout.py, fails if missing); behind_words and stat labels use only words he said
        (Rule 11); no em dashes; at most 40% of the video is takeover (he stays the host).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SKILL, STYLE, load, fail, ok, banned_words  # noqa: E402

KINDS = {"icon_pop", "behind_words", "bg_swap", "takeover", "stat"}
SCENES = {"IconSwarm", "Kinetic", "IconList", "Compare", "StatSlam", "DocFly", "CTA", "PhotoPunch", "ReadingWindow"}


def main():
    if len(sys.argv) < 2:
        fail('usage: s06b_fx.py "$WD"')
    wd = Path(sys.argv[1])
    if not (wd / "fx.json").exists():
        ok("no fx.json: no effects layer for this video")
        return
    fx = load(wd / "fx.json")["fx"]
    words = load(wd / "tight_words.json")["words"]
    spoken = {re.sub(r"[^\w%]", "", w["w"].lower()) for w in words}
    shots = load(wd / "shots.json")
    gr = load(wd / "graphics.json")
    icons = {p.stem for p in (SKILL / "assets" / "icons").iterdir() if p.suffix in (".svg", ".png")}
    dur = shots["duration"]
    bad = banned_words()
    problems = []
    tk_total = 0.0
    for i, x in enumerate(fx, 1):
        tag = f"fx {i} ({x.get('kind')})"
        k = x.get("kind")
        if k not in KINDS:
            problems.append(f"{tag}: kind must be one of {sorted(KINDS)}")
            continue
        s, e = x.get("start", -1), x.get("end", -1)
        if not (0 <= s < e <= dur):
            problems.append(f"{tag}: start/end {s}..{e} outside 0..{dur:.1f}")
            continue
        if not 1.2 <= e - s <= 6.0:
            problems.append(f"{tag}: {e - s:.1f} s long; keep effects 1.2 to 6 s")
        if "word" in x and abs(words[x["word"]]["start"] - s) > 0.05:
            problems.append(f"{tag}: starts {s} but its word '{words[x["word"]]["w"]}' starts {words[x['word']]['start']:.2f}")
        if k == "icon_pop" and STYLE["brand"].get("icon_prefix"):
            # Rule 47: a brand profile with an icon_prefix allows only its own official icons
            for ic in x.get("icons", []):
                if not str(ic.get("name", "")).startswith(STYLE["brand"]["icon_prefix"]):
                    problems.append(f"{tag}: '{ic.get('name')}' is not one of this brand's own icons (Rule 47)")
        if k == "icon_pop":
            for ic in x.get("icons", []):
                if ic.get("name") not in icons:
                    problems.append(f"{tag}: icon '{ic.get('name')}' not in assets/icons")
                if "word" not in ic:
                    problems.append(f"{tag}: icon '{ic.get('name')}' needs the word it lands on")
                else:
                    ic["at"] = words[ic["word"]]["start"]
                    if not s - 0.01 <= ic["at"] < e:
                        problems.append(f"{tag}: icon '{ic.get('name')}' word is outside the effect window")
        if k in ("behind_words", "bg_swap") and not (wd / "subject.webm").exists():
            problems.append(f"{tag}: needs subject.webm. Run: python3.12 cutout.py \"{wd}\"")
        if k in ("takeover",) or (k == "bg_swap" and (x.get("bg") or {}).get("scene")):
            sc = x.get("scene") or x["bg"]["scene"]
            if sc not in SCENES:
                problems.append(f"{tag}: scene '{sc}' unknown")
        if k == "takeover":
            tk_total += e - s
        text = " ".join(str(v) for v in (x.get("text", ""), x.get("label", "")) if v)
        if "—" in text:
            problems.append(f"{tag}: em dash")
        for w in re.findall(r"[\w%']+", text.lower()):
            if k in ("behind_words", "stat") and re.sub(r"[^\w%]", "", w) not in spoken:
                problems.append(f"{tag}: '{w}' is not a word he said (Rule 11)")
            if w in bad:
                problems.append(f"{tag}: banned word '{w}'")
        if s < gr["title"]["end"] and k != "behind_words":
            problems.append(f"{tag}: starts inside the title window (0 to {gr['title']['end']:.1f} s)")
        for g in gr["graphics"]:
            if s < g["end"] - 0.01 and e > g["start"] + 0.01:
                problems.append(f"{tag}: overlaps graphic {g['id']} ({g['kind']}, {g['start']:.1f} to {g['end']:.1f} s). Drop one of them from the inventory.")
        for sh in shots["shots"]:
            if sh["layout"] in ("D", "E") and s < sh["end"] and e > sh["start"]:
                problems.append(f"{tag}: overlaps full plate shot {sh['id']} ({sh['start']:.1f} to {sh['end']:.1f} s)")
    srt = sorted(fx, key=lambda z: z.get("start", 0))
    for a, b in zip(srt, srt[1:]):
        if b.get("start", 0) < a.get("end", 0) - 0.01:
            problems.append(f"{a['kind']} at {a['start']} overlaps {b['kind']} at {b['start']}")
    if tk_total > 0.4 * dur:
        problems.append(f"takeovers fill {tk_total:.1f} s of {dur:.1f} s; keep him on screen at least 60% of the time")
    if problems:
        fail(f"{len(problems)} effect problems:\n- " + "\n- ".join(problems))
    from common import save
    save(wd / "fx.json", {"fx": fx})
    ok(f"{len(fx)} effects, takeovers {tk_total:.1f} s, all on their words")


if __name__ == "__main__":
    main()
