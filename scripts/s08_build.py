"""Step 8. Build: make the animated graphics and assemble the edit with Remotion.

Usage: python s08_build.py <workdir> [--frames START END]   (--frames renders a slice for a quick test)
Input : <workdir>/shots.json, graphics.json, tight_words.json, tight.mp4, and the approved storyboard
Output: <workdir>/draft.mp4 (1080x1920, 30 fps, H.264 + AAC) and <workdir>/props.json
Work  : the Remotion project is copied to <video-tools>/remotion/jobs/<workdir name>/ so it finds node_modules.
Check : draft.mp4 exists, is 1080x1920 at 30 fps, has an audio stream, and its length is within 0.1 s of tight.mp4.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

from common import FFPROBE, REMOTION, SKILL, STYLE, fail, load, ok, probe, save

FPS = 30


def caption_pages(words, emph):
    """One word per caption. A word under 0.2 s joins the next one when the pair stays under 0.45 s."""
    pages, i = [], 0
    while i < len(words):
        w = words[i]
        text, last, em = w["w"], w, i in emph
        if (w["end"] - w["start"]) < 0.2 and i + 1 < len(words):
            n = words[i + 1]
            if n["end"] - w["start"] <= 0.45 and (n["start"] - w["end"]) < 0.15:
                text, last, em, i = f'{w["w"]} {n["w"]}', n, em or (i + 1) in emph, i + 1
        pages.append({"text": text, "start": w["start"], "last_end": last["end"], "emph": em})
        i += 1
    for k, p in enumerate(pages):
        nxt = pages[k + 1]["start"] if k + 1 < len(pages) else p["last_end"] + 0.3
        p["end"] = round(min(nxt, p["last_end"] + 0.35), 3)
        p["start"] = round(p["start"], 3)
        del p["last_end"]
    return pages


def main(work, frames=None):
    work = Path(work)
    shots, gr = load(work / "shots.json"), load(work / "graphics.json")
    tw = load(work / "tight_words.json")
    words = tw["words"]
    job = REMOTION / "jobs" / re.sub(r"[^\w-]", "_", work.name)
    if job.exists():
        shutil.rmtree(job)
    (job / "public").mkdir(parents=True)
    shutil.copytree(SKILL / "remotion" / "src", job / "src")
    pub = job / "public"
    shutil.copy2(work / "tight.mp4", pub / "tight.mp4")
    for rel in STYLE["brand"]["font_files"].values():
        src = SKILL / "assets" / rel
        (pub / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, pub / rel)
    inv = load(work / "inventory.json")["items"]
    # plate assets
    for s in shots["shots"]:
        s["asset"] = None
        if s.get("item") is not None and (inv[s["item"]].get("asset_used") or inv[s["item"]].get("asset")):
            a = Path(inv[s["item"]].get("asset_used") or inv[s["item"]]["asset"])
            name = f"plate_{s['id']}{a.suffix}"
            shutil.copy2(a, pub / name)
            s["asset"] = name
    # graphic assets and list timings
    for g in gr["graphics"]:
        if g.get("asset"):
            a = Path(g["asset"])
            name = f"g_{g['id']}{a.suffix}"
            shutil.copy2(a, pub / name)
            g["asset"] = name
        for li, ln in enumerate(g.get("lines", [])):
            if ln.get("icon"):
                a = Path(ln["icon"])
                name = f"g_{g['id']}_icon{li}{a.suffix}"
                shutil.copy2(a, pub / name)
                ln["icon"] = name
            ln["start_rel"] = round(max(0.0, words[ln["word"]]["start"] - g["start"]), 3)
    # Rule 42: effects layer (fx.json, checked by s06b_fx.py), shared motion kit sounds and icons, the cutout
    fx = load(work / "fx.json")["fx"] if (work / "fx.json").exists() else []
    shutil.copytree(SKILL / "assets" / "sfx", pub / "sfx")
    shutil.copytree(SKILL / "assets" / "icons", pub / "icons")
    for x in fx:
        for key in ("image", "pattern"):
            for holder in (x, x.get("bg") or {}):
                if holder.get(key):
                    src = Path(holder[key]) if Path(holder[key]).is_absolute() else work / holder[key]
                    name = f"fx_{abs(hash(str(src))) % 10**8}{src.suffix}"
                    shutil.copy2(src, pub / name)
                    holder[key] = name
    cutout = (work / "subject.webm").exists() and any(x["kind"] in ("behind_words", "bg_swap") for x in fx)
    if cutout:
        shutil.copy2(work / "subject.webm", pub / "subject.webm")
    if gr["end_logo"].get("asset"):
        shutil.copy2(Path(gr["end_logo"]["asset"]), pub / "end_logo.png")
        gr["end_logo"]["asset"] = "end_logo.png"
    props = {"fps": FPS, "duration": shots["duration"], "shots": shots["shots"], "graphics": gr["graphics"], "title": gr["title"],
             "end_logo": gr["end_logo"], "pages": caption_pages(words, set(gr["emphasis"])), "brand": STYLE["brand"], "geom": STYLE["geometry"],
             "fx": fx, "cutout": cutout,
             "rtl": (load(work / "words.json").get("language") in ("he", "ar", "fa", "ur")) if (work / "words.json").exists() else False,
             "face_box": load(work / "intake.json").get("face_box_median") if (work / "intake.json").exists() else None}
    save(job / "src" / "props.json", props)
    save(work / "props.json", props)

    out = work / "draft.mp4"
    cmd = f'npx remotion render "jobs/{job.name}/src/index.jsx" Edit "{out}" --public-dir="jobs/{job.name}/public" --codec=h264 --crf=17 --log=warn'
    if frames:
        cmd += f" --frames={frames[0]}-{frames[1]}"
    print("rendering ... this takes a few minutes")
    r = subprocess.run(cmd, cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    tail = (r.stdout + r.stderr)[-800:]
    if r.returncode != 0 or not out.exists():
        fail("remotion render failed:\n" + tail)
    info = probe(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    num, den = v["r_frame_rate"].split("/")
    if (v["width"], v["height"]) != (1080, 1920):
        fail(f"draft is {v['width']}x{v['height']}")
    if abs(float(num) / float(den) - FPS) > 0.01:
        fail(f"draft is {float(num) / float(den):.2f} fps")
    if not a:
        fail("draft has no audio")
    expect = (frames[1] - frames[0] + 1) / FPS if frames else float(probe(work / "tight.mp4")["format"]["duration"])
    if abs(dur - expect) > 0.1:
        fail(f"draft is {dur:.2f} s, expected {expect:.2f} s")
    ok(f"draft.mp4 {dur:.1f} s, 1080x1920, 30 fps, audio present")


if __name__ == "__main__":
    fr = None
    if "--frames" in sys.argv:
        k = sys.argv.index("--frames")
        fr = (int(sys.argv[k + 1]), int(sys.argv[k + 2]))
    main(sys.argv[1], fr)
