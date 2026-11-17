"""Step 9. Review: cut labelled frame sheets from the draft for a fresh reviewer subagent.

Usage: python s09_review_frames.py <workdir>
Input : <workdir>/draft.mp4, shots.json, graphics.json
Output: <workdir>/review/sheet_01.png ... and <workdir>/review/BRIEF.md
The BRIEF tells the reviewer what to read (style guide, style.json, rules.md) and what to judge.
It does NOT include the plan, shots.json or graphics.json: the reviewer must judge from the frames alone.
Check : at least one frame per cut, per graphic, per plate, the title and the end logo; every frame file is non-empty.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from common import FFMPEG, SKILL, fail, fmt_t, load, ok, run

COLS, ROWS = 6, 3  # fluid mode samples every 1 s, so expect 3 to 4 sheets
TW, TH = 270, 480


def main(work):
    work = Path(work)
    fluid = (work / "fluid.json").exists() and load(work / "props.json").get("mode") == "fluid"
    if fluid:
        FL = load(work / "fluid.json")
        T = FL["duration"]
    else:
        S, G = load(work / "shots.json"), load(work / "graphics.json")
        T = S["duration"]
    want = {}

    def add(t, why):
        t = max(0.0, min(T - 0.05, t))
        key = round(t * 30)
        want.setdefault(key, why)

    if fluid:
        for c in FL["cards"]:
            add(c["start"] + 0.12, f"{c['id']} entering")
            add(c["start"] + 0.8, f"{c['id']} settled")
            add(c["end"] - 0.15, f"{c['id']} leaving")
        for k in FL["camera"]:
            add(k["t"], "camera key")
        if FL.get("reveal"):
            add(FL["reveal"]["start"] + 0.45, "reveal mid pull-back")
        add(FL["end_logo"]["start"] + 0.5, "end logo")
        add(T - 0.1, "last frame")
        t = 0.0
        while t < T:
            add(t, "every 1 s")
            t += 1.0
    else:
        for s in S["shots"]:
            add(s["start"] + 0.15, f"shot {s['id']} start ({s['layout']})")
            add((s["start"] + s["end"]) / 2, f"shot {s['id']} middle")
        for g in G["graphics"]:
            add(g["start"] + 0.07, f"graphic {g['id']} entering")
            add(g["start"] + 0.35, f"graphic {g['id']} settled")
        add(G["title"]["start"] + 0.5, "title")
        add(G["end_logo"]["start"] + 0.5, "end logo")
        add(T - 0.1, "last frame")
        t = 0.0
        while t < T:
            add(t, "every 2 s")
            t += 2.0
    keys = sorted(want)
    rd = work / "review"
    rd.mkdir(exist_ok=True)
    for old in rd.glob("*"):
        old.unlink()
    tiles = []
    for k in keys:
        p = rd / f"f_{k:05d}.jpg"
        r = run([FFMPEG, "-v", "error", "-y", "-ss", f"{k / 30:.3f}", "-i", work / "draft.mp4", "-frames:v", "1", "-vf", f"scale={TW}:{TH}", p])
        if r.returncode != 0 or not p.exists() or p.stat().st_size < 500:
            fail(f"could not extract frame at {k / 30:.2f} s")
        tiles.append((k, p))
    sheets = []
    per = COLS * ROWS
    for n in range(0, len(tiles), per):
        sheet = Image.new("RGB", (COLS * TW, ROWS * TH), (20, 20, 20))
        d = ImageDraw.Draw(sheet)
        for j, (k, p) in enumerate(tiles[n:n + per]):
            x, y = (j % COLS) * TW, (j // COLS) * TH
            sheet.paste(Image.open(p), (x, y))
            d.rectangle([x, y, x + 96, y + 16], fill=(0, 0, 0))
            d.text((x + 3, y + 2), f"{fmt_t(k / 30)} #{k}", fill=(255, 255, 255))
        sp = rd / f"sheet_{n // per + 1:02d}.png"
        sheet.save(sp)
        sheets.append(sp)
    for _, p in tiles:
        p.unlink()
    brief = f"""# Review brief (fresh reviewer, you have not seen the plan)

You are reviewing a draft vertical video edit. Judge only from the frame sheets.

Read first:
- {SKILL / 'rules.md'}  (hard rules, especially the brand rule)
- {SKILL / 'taste-checklist.md'}  (the user's numbered preferences: check EVERY rule)
- {SKILL / 'style.json'}  (the numbers)

Frame sheets (each tile is labelled with time and frame number, 1080x1920 scaled to 270x480):
{chr(10).join('- ' + str(p) for p in sheets)}

Judge against those files and report findings as a table with columns: Frame | Problem | Rule it breaks | Fix.
Check each of these:
1. Brand rule: only the colors and the font of this video's brand profile (brands/). No logo except the brand's own end logo in the last 2 s. Nothing copied from another creator's branding: no landing pages, calls to action, colors or fonts of theirs.
2. The face is never covered, cropped or touched by a graphic. Graphics sit only in the top band (6% to 33% of height).
3. Captions: one short caption at a time, same row (about 77% down) in every layout, readable, never over the face.
4. Layouts follow the style: head full frame; plates are light with one rounded card; inset is a rounded card on a plate; title is two lines in the top band at the start only.
5. Graphics look real (real screens, real photos, real logos), not generic or clip-art. Flag anything that looks invented.
6. Pacing from the sheets: do cuts and graphics land often enough (about every 2 to 3 s something changes) without clutter?
7. Anything generic, cheap or off-brand that a marketing manager would not ship.
After the table, add a second table "Checklist" with one row per numbered rule in taste-checklist.md: Rule number | PASS, FAIL or N/A | frame or evidence. A rule you cannot judge from frames is N/A with the reason.
Say "no findings" for any check that passes. Be specific: frame number and what you see.
"""
    if fluid:
        brief = brief.replace("""2. The face is never covered, cropped or touched by a graphic. Graphics sit only in the top band (6% to 33% of height).
3. Captions: one short caption at a time, same row (about 77% down) in every layout, readable, never over the face.
4. Layouts follow the style: head full frame; plates are light with one rounded card; inset is a rounded card on a plate; title is two lines in the top band at the start only.""",
"""2. FLUID MODE: one continuous take. There must be NO cuts and NO sudden scale jumps on the speaker (Rule 25).
   The camera only glides: a slow push-in, a glide into a corner inset while a screen recording plays, and a pull-back at the end.
   Compare neighbouring frames: any jump in his position or size that is not one of those glides is a finding.
3. The face is never covered, cropped or touched by a card. Cards sit by the hand or on the side he looks to (Rule 26).
4. Captions: a short phrase low in the frame, words light up as they are spoken (unspoken words are dimmer on purpose).
   Readable, never over the face. Flag dim words only if a spoken word stays dim.
5b. The ending (Rule 28): the picture pulls back onto the real storyboard and real check lines tick in, then the brand's end logo.
   Does it feel designed and land as a "wow"? Is anything on it unreadable or cluttered?
5c. Rule 30: numbers on screen. A real screenshot may show its own figures: list where, so the editor can tell the user.""")
        need = len(FL["cards"]) + 2
    else:
        need = len(S["shots"]) + len(G["graphics"]) + 2
    (rd / "BRIEF.md").write_text(brief, encoding="utf-8")
    if len(keys) < need:
        fail(f"only {len(keys)} frames for {need} required events")
    ok(f"{len(keys)} frames on {len(sheets)} sheet(s), brief written to review/BRIEF.md. Now spawn the reviewer subagent with that brief only.")


if __name__ == "__main__":
    main(sys.argv[1])
