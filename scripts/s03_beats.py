"""Step 3. Story: split the tight transcript into beats and note the trigger words.

Usage: python s03_beats.py <workdir> --show      print the indexed transcript to write beats from
       python s03_beats.py <workdir>             validate <workdir>/beats.json
Input : <workdir>/tight_words.json, <workdir>/beats.json (written by Claude)
Output: <workdir>/beats.json (validated) and <workdir>/beats.md (readable summary)

beats.json format:
{"beats": [{"id": "hook", "type": "hook", "words": [0, 14],
            "triggers": [{"word": 6, "label": "names the thing to show"}],
            "summary": "one line"}]}
Types, in order: hook, setup, proof (one or more), turn, cta. Not every video needs every type, but hook comes first.
Check : beats cover every word once, in order, no gaps; hook starts at word 0 and ends within 8 s;
        types are in allowed order; every beat has at least one trigger word inside its own range;
        a cta beat, if present, is last and its words are the speaker's (nothing is added).
"""
import sys
from pathlib import Path

from common import fail, load, ok, fmt_t

ORDER = ["hook", "setup", "proof", "turn", "cta"]


def show(work):
    tw = load(work / "tight_words.json")
    line, out = [], []
    for w in tw["words"]:
        line.append(f"[{w['i']}]{w['w']}")
        if w["w"].endswith((".", "?", "!")) or len(line) >= 14:
            out.append(f"{fmt_t(tw['words'][int(line[0].split(']')[0][1:])]['start'])}  " + " ".join(line))
            line = []
    if line:
        out.append(f"{fmt_t(tw['words'][int(line[0].split(']')[0][1:])]['start'])}  " + " ".join(line))
    print("\n".join(out))
    print(f"\n{len(tw['words'])} words, {tw['duration']:.1f} s")


def main(work, show_only=False):
    work = Path(work)
    if show_only:
        return show(work)
    tw = load(work / "tight_words.json")
    words = tw["words"]
    b = load(work / "beats.json")["beats"]
    if not b:
        fail("beats.json has no beats")
    last_rank = -1
    expect = 0
    for k, beat in enumerate(b):
        t = beat.get("type")
        if t not in ORDER:
            fail(f"beat {beat.get('id')}: type '{t}' is not one of {ORDER}")
        rank = ORDER.index(t)
        if rank < last_rank:
            fail(f"beat {beat['id']}: type '{t}' is out of order (hook, setup, proof, turn, cta)")
        last_rank = rank
        w0, w1 = beat["words"]
        if w0 != expect:
            fail(f"beat {beat['id']} starts at word {w0} but the previous beat ended at {expect - 1}. Beats must cover every word once.")
        if w1 < w0:
            fail(f"beat {beat['id']}: end before start")
        expect = w1 + 1
        trig = beat.get("triggers", [])
        if not trig:
            fail(f"beat {beat['id']} has no trigger words")
        for tr in trig:
            if not w0 <= tr["word"] <= w1:
                fail(f"beat {beat['id']}: trigger word {tr['word']} is outside its range {w0}-{w1}")
        if t == "cta" and k != len(b) - 1:
            fail("a cta beat must be last")
    if b[0]["type"] != "hook" or b[0]["words"][0] != 0:
        fail("the first beat must be the hook and start at word 0")
    if expect != len(words):
        fail(f"beats end at word {expect - 1} but the transcript has {len(words)} words")
    hook_end = words[b[0]["words"][1]]["end"]
    if hook_end > 8.0:
        fail(f"hook ends at {hook_end:.1f} s. The style opens fast: the hook must end within 8 s (first cut median 7.0 s).")
    lines = ["# Beats", ""]
    for beat in b:
        w0, w1 = beat["words"]
        lines.append(f"## {beat['id']} ({beat['type']}) {fmt_t(words[w0]['start'])} to {fmt_t(words[w1]['end'])}")
        lines.append(" ".join(w["w"] for w in words[w0:w1 + 1]))
        lines.append("triggers: " + "; ".join(f"[{t['word']}] {words[t['word']]['w']} ({t.get('label', '')})" for t in beat["triggers"]))
        lines.append("")
    (work / "beats.md").write_text("\n".join(lines), encoding="utf-8")
    ok(f"{len(b)} beats cover all {len(words)} words; hook ends at {hook_end:.1f} s; every beat has triggers")


if __name__ == "__main__":
    main(sys.argv[1], "--show" in sys.argv)
