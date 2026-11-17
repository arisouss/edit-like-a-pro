"""Step 4. Visual inventory: for each beat, the real thing worth showing, or nothing.

Usage: python s04_inventory.py <workdir>
Input : <workdir>/beats.json, <workdir>/tight_words.json, <workdir>/inventory.json (written by Claude)
Output: <workdir>/inventory.json (validated)

inventory.json format:
{"title": {"line1": "text", "line2": "text"},
 "items": [{"beat": "proof", "kind": "plate_card", "trigger_word": 57,
            "asset": "C:/path/screenshot.png", "source": "user-supplied",
            "text": "the exact words or numbers shown", "why": "what is real about it"},
           {"beat": "setup", "kind": "nothing", "why": "no real thing to show"}]}
kinds: plate_card, product_card, photo_insert, logo, numbered_list, keyword_text, plate_inset, nothing
numbered_list also takes "lines": [{"text": "Contrarian", "word": 31}, ...]
sources: user-supplied, official-site, screen-capture (never generated, never invented)

Check : every beat has at least one item (nothing is allowed, with a reason); kinds and sources are allowed;
        image kinds point to a file that exists (optional "crop": [x0, y0, x1, y1] fractions; the cropped copy is saved as "asset_used"); trigger_word lies inside the beat;
        keyword_text and list lines use only words the speaker said; no banned words on screen;
        no branding of the study creator (rules.md hard rule); the brand's end logo is never an inventory item
        (it appears only on the end card, added by step 6).
"""
import re
import sys
from pathlib import Path

from common import STYLE, banned_words, fail, load, ok

IMAGE_KINDS = {"plate_card", "product_card", "photo_insert", "logo", "plate_inset"}
TEXT_KINDS = {"keyword_text", "numbered_list"}
SOURCES = {"user-supplied", "official-site", "screen-capture"}
THEIR_BRAND = ("mariah", "brunner", "buildai", "build-ai", "learnaiwithmariah", "learn-ai-with")


def toks(s):
    return re.findall(r"[a-z0-9\u05d0-\u05ea']+", s.lower())  # Latin, digits, Hebrew letters


def main(work):
    work = Path(work)
    words = load(work / "tight_words.json")["words"]
    beats = load(work / "beats.json")["beats"]
    inv = load(work / "inventory.json")
    items = inv.get("items", [])
    kinds = set(STYLE["graphics"]["kinds"]) | {"nothing"}
    spoken = set(toks(" ".join(w["w"] for w in words)))
    bad = banned_words()
    problems = []
    title = inv.get("title")
    if not title or not title.get("line1"):
        problems.append("inventory.json needs a title: {line1, line2}. The style opens with a two-line title in the top band.")
    else:
        for line in (title.get("line1", ""), title.get("line2", "")):
            for b in bad:
                if b in line.lower():
                    problems.append(f"title contains banned word '{b}'")
    by_beat = {b["id"]: b for b in beats}
    seen = set()
    for k, it in enumerate(items):
        tag = f"item {k} ({it.get('kind')}, beat {it.get('beat')})"
        if it.get("beat") not in by_beat:
            problems.append(f"{tag}: unknown beat")
            continue
        seen.add(it["beat"])
        kind = it.get("kind")
        if kind not in kinds:
            problems.append(f"{tag}: kind must be one of {sorted(kinds)}")
            continue
        if kind == "nothing":
            if not it.get("why"):
                problems.append(f"{tag}: 'nothing' needs a reason")
            continue
        if it.get("source") not in SOURCES:
            problems.append(f"{tag}: source must be one of {sorted(SOURCES)}. Never generated or invented.")
        w0, w1 = by_beat[it["beat"]]["words"]
        tw = it.get("trigger_word")
        if tw is None or not w0 <= tw <= w1:
            problems.append(f"{tag}: trigger_word {tw} is not inside the beat ({w0}-{w1})")
        if kind in IMAGE_KINDS:
            a = it.get("asset")
            if not a or not Path(a).exists():
                problems.append(f"{tag}: asset file not found: {a}. Get the real file or use 'nothing'.")
            elif any(x in str(a).lower() for x in THEIR_BRAND):
                problems.append(f"{tag}: asset looks like the study creator's branding. Hard rule: never.")
            elif kind == "logo" and STYLE["brand"].get("end_logo") and Path(str(a)).name == Path(str(STYLE["brand"]["end_logo"])).name:
                problems.append(f"{tag}: the brand's end logo is end card only. Remove it from the inventory.")
        if kind == "keyword_text":
            t = toks(it.get("text", ""))
            miss = [x for x in t if x not in spoken]
            if not t:
                problems.append(f"{tag}: keyword_text needs text")
            elif miss and not it.get("editor_placeholder"):
                problems.append(f"{tag}: words {miss} were not spoken. On-screen words must be the speaker's own words.")
        if kind == "numbered_list":
            lines = it.get("lines", [])
            if len(lines) < 2:
                problems.append(f"{tag}: numbered_list needs at least 2 lines")
            for ln in lines:
                miss = [x for x in toks(ln["text"]) if x not in spoken]
                if miss:
                    problems.append(f"{tag}: list line '{ln['text']}' has words never spoken: {miss}")
                if not w0 <= ln.get("word", -1) <= w1:
                    problems.append(f"{tag}: list line '{ln['text']}' trigger word is outside the beat")
        for b in bad:
            blob = (it.get("text", "") + " " + " ".join(l["text"] for l in it.get("lines", []))).lower()
            if b in blob:
                problems.append(f"{tag}: banned word '{b}'")
        blob = (it.get("text", "") + str(it.get("why", ""))).lower()
        if "comment " in blob and "\"" in blob:
            problems.append(f"{tag}: looks like a 'Comment X' call to action. That is the study creator's branding. Hard rule: never.")
    for b in beats:
        if b["id"] not in seen:
            problems.append(f"beat {b['id']} has no inventory item. Add a real thing or kind 'nothing' with a reason.")
    if problems:
        print("\n".join("  - " + p for p in problems))
        fail(f"{len(problems)} problem(s) in inventory.json")
    # prepare each image: optional "crop": [x0, y0, x1, y1] as fractions, so a graphic shows one readable panel
    from PIL import Image
    out_dir = work / "assets_crop"
    out_dir.mkdir(exist_ok=True)
    for k, it in enumerate(items):
        if it.get("kind") in IMAGE_KINDS and it.get("asset"):
            im = Image.open(it["asset"]).convert("RGB")
            c = it.get("crop")
            if c:
                if not (len(c) == 4 and 0 <= c[0] < c[2] <= 1 and 0 <= c[1] < c[3] <= 1):
                    fail(f"item {k}: crop must be [x0, y0, x1, y1] as fractions with x0<x1 and y0<y1")
                W, H = im.size
                im = im.crop((round(c[0] * W), round(c[1] * H), round(c[2] * W), round(c[3] * H)))
            if it.get("kind") in ("plate_card", "plate_inset"):
                # Edit.jsx only shrinks images (maxWidth/maxHeight), never grows them, so a small crop renders tiny (G52).
                # Scale it up to fill the plate box: 0.86 x 0.56 of the 1080x1920 frame.
                f = min(1080 * 0.86 / im.size[0], 1920 * 0.56 / im.size[1])
                if f > 1:
                    im = im.resize((round(im.size[0] * f), round(im.size[1] * f)), Image.LANCZOS)
            dst = out_dir / f"item{k}.png"
            im.save(dst)
            it["asset_used"] = str(dst)
    from common import save
    save(work / "inventory.json", inv)
    shown = [i for i in items if i["kind"] != "nothing"]
    ok(f"{len(shown)} real graphic(s) across {len(beats)} beats, {len(items) - len(shown)} 'nothing' decision(s), title set")


if __name__ == "__main__":
    main(sys.argv[1])
