"""Step 7. Storyboard: one HTML page, one row per shot, with a still, the words, and an approve/change box.

Usage: python s07_storyboard.py <workdir>
Input : <workdir>/shots.json, graphics.json, tight_words.json, tight.mp4
Output: <workdir>/storyboard.html and <workdir>/stills/shot_NN.jpg
Also: <workdir>/storyboard_preview.png and <workdir>/BRIEF_storyboard.md for the pre-show check by a fresh subagent.
Check : one row per shot, every still exists and is not empty. Then run the storyboard check, then STOP and wait for the user's approval.
"""
import html
import sys
from pathlib import Path

import numpy as np

from common import FFMPEG, SKILL, STYLE, fail, load, ok, run, fmt_t

B = STYLE["brand"]
G = STYLE["geometry"]


def copy_asset(work, path):
    """Copy a graphic into <workdir>/assets so the storyboard stays portable. Returns a relative href or None."""
    if not path or not Path(path).exists():
        return None
    d = work / "assets"
    d.mkdir(exist_ok=True)
    dst = d / Path(path).name
    if not dst.exists():
        dst.write_bytes(Path(path).read_bytes())
    return f"assets/{dst.name}"


def main(work):
    work = Path(work)
    inv_items = load(work / "inventory.json")["items"]
    tw = load(work / "tight_words.json")
    words, T = tw["words"], tw["duration"]
    _dm = work / "drops_manual.json"
    _tn = load(_dm).get("tail_note", "") if _dm.exists() else ""
    cuts = load(work / "cuts.json")
    _off = [d for d in cuts.get("dropped", []) if d.get("reason", "").startswith("closing offer")]
    _rep = [d for d in cuts.get("dropped", []) if d.get("reason", "") == "restarted phrase"]
    CUT_NOTE = ""
    _box = '<div style="background:#fdecea;border:1px solid #c0392b;padding:.7rem 1rem;border-radius:8px;margin:.6rem 0">'
    if _off:
        CUT_NOTE += (_box + '<b>Proposed whole-word cut, needs the user OK (no word reworded):</b> removes "' + html.escape(" ".join(d["word"] for d in _off)) + '" ('
                     + str(len(_off)) + f' words). Source {cuts["source_duration"]:.1f} s, new length {T:.1f} s.'
                     + (' <b>Deliberate hold:</b> ' + html.escape(_tn) if _tn else '') + '</div>')
    if _rep:
        CUT_NOTE += (_box + '<b>Automatic repeat drop, tell me if it was on purpose:</b> the first "' + html.escape(" ".join(d["word"] for d in _rep))
                     + '" of his repeated "every time, every time" (source ' + f'{_rep[0]["start"]:.2f} to {_rep[-1]["end"]:.2f} s) is removed by the restarted-phrase rule. The second one stays.</div>')
    S = load(work / "shots.json")
    GR = load(work / "graphics.json")
    shots = S["shots"]
    _t = GR["title"]
    CUT_NOTE += ('<div style="background:#fdecea;border:1px solid #c0392b;padding:.7rem 1rem;border-radius:8px;margin:.6rem 0">'
                 '<b>TITLE (new text, editor wrote it), needs the user OK:</b> "' + html.escape(_t["line1"]) + " / " + html.escape(_t.get("line2", "")) + f'" shown 0 to {_t["end"]:.1f} s.</div>')
    FX = load(work / "fx.json")["fx"] if (work / "fx.json").exists() else []
    INTAKE = load(work / "intake.json") if (work / "intake.json").exists() else {}
    (work / "stills").mkdir(exist_ok=True)
    rows, bad = [], []
    for s in shots:
        mid = (s["start"] + s["end"]) / 2
        p = work / "stills" / f"shot_{s['id']:02d}.jpg"
        r = run([FFMPEG, "-v", "error", "-y", "-ss", f"{mid:.3f}", "-i", work / "tight.mp4", "-frames:v", "1", "-vf", "scale=270:-1", p])
        if r.returncode != 0 or not p.exists() or p.stat().st_size < 500:
            bad.append(s["id"])
        said = " ".join(w["w"] for w in words if s["w0"] is not None and s["w0"] <= w["i"] <= s["w1"])
        gfx = [g for g in GR["graphics"] if g["start"] < s["end"] and g["end"] > s["start"]]
        cap_word = next((w["w"] for w in words if w["start"] <= mid <= w["end"]), "")
        # mock overlay as inline SVG on a 270x480 canvas
        svg = [f'<svg viewBox="0 0 270 480" class="mock">']
        fc = G["face_centre"]
        cx, cy0 = fc["x"] * 270, fc["y"] * 480
        still = f"stills/shot_{s['id']:02d}.jpg"
        if s["layout"] in ("D", "E"):
            svg.append(f'<rect width="270" height="480" fill="{B["plate"]}"/>')
            item = inv_items[s["item"]] if s.get("item") is not None else {}
            asset = copy_asset(work, item.get("asset_used") or item.get("asset"))
            if s["layout"] == "D":
                svg.append(f'<rect x="19" y="110" width="232" height="260" rx="14" fill="#fff" stroke="{B["muted"]}" stroke-opacity=".35"/>')
                if asset:
                    svg.append(f'<image href="{asset}" x="19" y="110" width="232" height="260" preserveAspectRatio="xMidYMid meet"/>')
                else:
                    svg.append(f'<text x="135" y="245" text-anchor="middle" font-size="12" fill="{B["muted"]}">graphic card</text>')
            else:
                svg.append(f'<image href="{still}" x="40" y="150" width="190" height="338" preserveAspectRatio="xMidYMid slice"/>')
                svg.append(f'<rect x="40" y="150" width="190" height="270" rx="14" fill="none" stroke="{B["muted"]}"/>')
        else:
            svg.append(f'<g transform="translate({cx:.1f},{cy0:.1f}) scale({s["scale"]}) translate({-cx:.1f},{-cy0:.1f})"><image href="{still}" width="270" height="480"/></g>')
            if s["layout"] == "B":
                svg.append(f'<text x="135" y="{G["title_block"]["y0"] * 480 + 22}" text-anchor="middle" font-size="19" font-weight="700" fill="#fff" stroke="#000" stroke-width=".5">{html.escape(GR["title"]["line1"])}</text>')
                svg.append(f'<text x="135" y="{G["title_block"]["y0"] * 480 + 44}" text-anchor="middle" font-size="15" fill="{B["accent_soft"]}" stroke="#000" stroke-width=".4">{html.escape(GR["title"].get("line2", ""))}</text>')
            for g in gfx:
                z0, z1 = g["zone"][0] * 480, g["zone"][1] * 480
                gx, gw, gh = 135 - g["width_frac"] * 135, g["width_frac"] * 270, (z1 - z0) * 0.62
                asset = copy_asset(work, g.get("asset"))
                if asset:
                    svg.append(f'<image href="{asset}" x="{gx:.0f}" y="{z0:.0f}" width="{gw:.0f}" height="{gh:.0f}" preserveAspectRatio="xMidYMid meet"/>')
                else:
                    svg.append(f'<rect x="{gx:.0f}" y="{z0:.0f}" width="{gw:.0f}" height="{gh:.0f}" rx="8" fill="{B["accent"]}" fill-opacity=".35" stroke="{B["accent"]}"/>')
                    label = g["text"] or "list"
                    svg.append(f'<text x="135" y="{z0 + 18:.0f}" text-anchor="middle" font-size="14" font-weight="700" fill="#fff" stroke="#000" stroke-width=".4">{html.escape(label)}</text>')
        # effects layer (step 6b): picture what fx.json adds on this shot, so the top zone is not shown empty
        fxs = [x for x in FX if x["start"] < s["end"] and x["end"] > s["start"] and (x["kind"] != "takeover" or s["start"] <= x["start"])] if s["layout"] not in ("D", "E") else []
        fb = INTAKE.get("face_box_median") or [0.39, 0.36, 0.40, 0.23]
        head_y = (fb[1] - 0.45 * fb[3]) * 480
        for x in fxs:
            if x["kind"] == "bg_swap" and (x.get("bg") or {}).get("scene") == "ReadingWindow":
                svg.append(f'<rect width="270" height="480" fill="#0b0b0f" fill-opacity=".72"/><rect x="24" y="22" width="222" height="125" rx="8" fill="#1d1d26" stroke="{B["accent"]}"/><circle cx="36" cy="33" r="3" fill="#ff6b5b"/><circle cx="46" cy="33" r="3" fill="#ffd43b"/><circle cx="56" cy="33" r="3" fill="#7bd88f"/><text x="135" y="36" text-anchor="middle" font-size="9" fill="#fff">Claude</text>')
                for k, wd in enumerate((190, 160, 200, 120, 180, 150)):
                    svg.append(f'<rect x="36" y="{50 + k * 15}" width="{wd * 0.9:.0f}" height="6" rx="3" fill="{B["accent"] if k == 2 else "#8a8a98"}" fill-opacity="{1 if k == 2 else .6}"/>')
                svg.append('<text x="135" y="162" text-anchor="middle" font-size="9" fill="#fff" stroke="#000" stroke-width=".3">Claude reads fake placeholder lines (decorative)</text>')
            elif x["kind"] == "bg_swap":
                svg.append(f'<rect width="270" height="480" fill="{B["accent"]}" fill-opacity=".28"/><text x="135" y="40" text-anchor="middle" font-size="11" fill="#fff" stroke="#000" stroke-width=".3">background swap behind him</text>')
            elif x["kind"] == "icon_pop":
                ics = [ic for ic in x["icons"] if ic["at"] < s["end"]]
                for k, ic in enumerate(ics):
                    ix = 135 + (k - (len(ics) - 1) / 2) * 70
                    svg.append(f'<circle cx="{ix:.0f}" cy="{head_y - 52:.0f}" r="22" fill="{B["accent"]}" stroke="#fff" stroke-width="2"/>')
                    try:  # the real icon glyph (same svg the renderer masks), white on the accent circle
                        import base64
                        raw = (SKILL / "assets" / "icons" / f'{ic["name"]}.svg').read_text(encoding="utf-8").replace("currentColor", "#ffffff")
                        svg.append(f'<image href="data:image/svg+xml;base64,{base64.b64encode(raw.encode()).decode()}" x="{ix - 12:.0f}" y="{head_y - 64:.0f}" width="24" height="24"/>')
                    except Exception:
                        svg.append(f'<text x="{ix:.0f}" y="{head_y - 49:.0f}" text-anchor="middle" font-size="11" fill="#000">{k + 1}</text>')
                    svg.append(f'<text x="{ix:.0f}" y="{head_y - 18:.0f}" text-anchor="middle" font-size="13" font-weight="700" fill="#fff" stroke="#000" stroke-width=".4">{html.escape(ic.get("label", ""))}</text>')
            elif x["kind"] == "behind_words":
                svg.append(f'<text x="135" y="{head_y + 6:.0f}" text-anchor="middle" font-size="64" font-weight="900" fill="#fff" fill-opacity=".85" stroke="#000" stroke-width=".6">{html.escape(x["text"])}</text><text x="135" y="{head_y - 62:.0f}" text-anchor="middle" font-size="9" fill="#fff" stroke="#000" stroke-width=".3">word behind his head (his hair covers the bottom)</text>')
            elif x["kind"] == "stat":
                svg.append(f'<text x="135" y="{head_y - 20:.0f}" text-anchor="middle" font-size="58" font-weight="900" fill="#fff" stroke="#000" stroke-width=".6">{x.get("prefix", "")}{x["value"]}{x.get("suffix", "")}</text><text x="135" y="{head_y + 2:.0f}" text-anchor="middle" font-size="16" font-weight="700" fill="#fff" stroke="#000" stroke-width=".4">{html.escape(x.get("label", ""))}</text>')
            elif x["kind"] in ("takeover",):
                svg.append(f'<text x="135" y="60" text-anchor="middle" font-size="12" fill="#fff" stroke="#000" stroke-width=".3">{x["kind"]}</text>')
        cy = G["caption_band"]["centre"] * 480 + 4
        svg.append(f'<text x="135" y="{cy:.0f}" text-anchor="middle" font-size="20" font-weight="700" fill="{B["white"] if s["layout"] not in ("D", "E") else B["muted"]}" stroke="#000" stroke-width="{.5 if s["layout"] not in ("D", "E") else 0}">{html.escape(cap_word)}</text>')
        svg.append("</svg>")
        gdesc = "<br>".join(
            f'<b>{html.escape(g["kind"])}</b> lands on word "{html.escape(g["trigger_text"])}" at {fmt_t(g["start"])}, {g["anim"]} ({g["enter_frames"]} frames), '
            f'{"<b>EDITOR PLACEHOLDER, not his words, needs his OK</b> " if g.get("editor_placeholder") else ""}shows: {html.escape(g["text"] or ", ".join(l["text"] for l in g["lines"]) or Path(str(g["asset"])).name)}' for g in gfx) or "none"
        for x in fxs:
            gdesc = ("" if gdesc == "none" else gdesc + "<br>") + f'<b>fx {html.escape(x["kind"])}</b> {fmt_t(x["start"])} to {fmt_t(x["end"])}: ' + html.escape(x.get("text") or ", ".join(i.get("label", "") for i in x.get("icons", [])) or (x.get("bg") or {}).get("scene", "")) + (' <span style="color:#c0392b"><b>EDITOR PLACEHOLDER, needs the user OK:</b> ' + html.escape(x["placeholder"]) + '</span>' if x.get("placeholder") else "")
        if s is shots[0]:
            gdesc = ("" if gdesc == "none" else gdesc + "<br>") + '<span style="color:#c0392b"><b>TITLE, needs the user OK:</b> ' + html.escape(_t["line1"]) + " / " + html.escape(_t.get("line2", "")) + "</span>"
        if s["layout"] in ("D", "E"):
            gdesc = f'<b>{"plate card" if s["layout"] == "D" else "plate + inset"}</b> (inventory item {s["item"]})'
        rows.append(f'''<tr id="s{s["id"]}"><td class="n">{s["id"]}<small>{fmt_t(s["start"])}<br>{s["end"] - s["start"]:.1f} s</small></td>
<td><img src="stills/shot_{s["id"]:02d}.jpg" alt="still of shot {s["id"]}"></td><td>{"".join(svg)}</td>
<td><div class="lay">{s["layout"]} &middot; scale {s["scale"]}</div><p class="said">{html.escape(said) or "<i>(no words)</i>"}</p><p class="g">{gdesc}</p></td>
<td class="ctl"><label><input type="radio" name="r{s["id"]}" value="approve" checked> Approve</label><label><input type="radio" name="r{s["id"]}" value="change"> Change</label>
<textarea id="t{s["id"]}" placeholder="What to change"></textarea></td></tr>''')
    if bad:
        fail(f"stills failed for shots {bad}")
    lens = [s["end"] - s["start"] for s in shots]
    plate = sum(s["end"] - s["start"] for s in shots if s["layout"] in ("D", "E")) / T
    P = STYLE["pacing"]
    stats = [("Shots", len(shots), "-"), ("Median shot", f"{np.median(lens):.1f} s", f"{P['shot_len_s']['p50']} s"),
             ("Cuts per minute", f"{(len(shots) - 1) / T * 60:.0f}", f"{P['cuts_per_min']['median']}"),
             ("Plate share", f"{plate * 100:.0f}%", f"{P['time_share']['plate'] * 100:.0f}%"),
             ("Changes per 10 s", f"{GR['changes_per_10s']}", f"{P['changes_per_10s']['median']}"),
             ("First cut", f"{shots[0]['end']:.1f} s", f"{P['first_cut_s_median']} s")]
    srows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in stats)
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Storyboard</title>
<style>:root{{--ink:{B["ink"]};--accent:{B["accent"]};--muted:{B["muted"]};--line:#e2e5e8;--bg:#fbfbfd}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:400 15px/1.5 "Segoe UI",-apple-system,system-ui,sans-serif}}
main{{max-width:1080px;margin:auto;padding:2rem 1.5rem 7rem}}h1{{font-size:2rem;letter-spacing:-.02em;margin:.2rem 0}}
.bar{{position:sticky;top:0;z-index:5;background:rgba(251,251,253,.85);backdrop-filter:blur(16px);padding:.7rem 0;border-bottom:1px solid var(--line);display:flex;gap:.6rem;align-items:center;flex-wrap:wrap}}
button{{font:600 14px "Segoe UI",system-ui;border:0;border-radius:10px;padding:.6rem 1rem;cursor:pointer;background:var(--accent);color:#fff}}button.alt{{background:#eef1f4;color:var(--ink)}}
table{{border-collapse:collapse;width:100%}}td,th{{padding:.7rem .6rem;vertical-align:top;border-bottom:1px solid var(--line);text-align:left}}th{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.n{{font-weight:700;font-size:1.3rem;white-space:nowrap}}.n small{{display:block;font-size:12px;color:var(--muted);font-weight:400}}
img,.mock{{width:135px;border-radius:8px;display:block;background:#222}}.mock{{background:#444}}
.lay{{font-weight:700;color:var(--accent)}}.said{{margin:.3rem 0;max-width:34rem}}.g{{font-size:13px;color:var(--muted);margin:.2rem 0}}
.ctl{{min-width:190px}}.ctl label{{margin-right:.7rem}}textarea{{width:100%;min-height:54px;margin-top:.4rem;font:inherit;border:1px solid var(--line);border-radius:8px;padding:.4rem}}
.stats td:first-child{{font-weight:600}}#toast{{color:var(--muted);font-size:13px}}</style></head><body><main>
<h1>Storyboard</h1>{CUT_NOTE}<p>{len(shots)} shots, {fmt_t(T)} long. Left still is your real footage, right is the planned layout. Mark each row, then copy your notes into the chat.</p>
<table class="stats"><tr><th>Measure</th><th>This edit</th><th>Style median</th></tr>{srows}</table>
<div class="bar"><button id="copy">Copy my notes</button><button class="alt" id="all">Approve all</button><span id="toast"></span></div>
<table><tr><th>#</th><th>Footage</th><th>Plan</th><th>Words and graphics</th><th>Your call</th></tr>{"".join(rows)}</table></main>
<script>
const N={len(shots)};
function notes(){{let out=["STORYBOARD NOTES"],ch=0;for(let i=1;i<=N;i++){{const v=document.querySelector('input[name=r'+i+']:checked').value;const t=document.getElementById('t'+i).value.trim();
if(v==='change'||t){{ch++;out.push('Shot '+i+': CHANGE'+(t?' - '+t:''));}}}}
out.push(ch?ch+' shot(s) to change. All other shots approved.':'All '+N+' shots approved.');return out.join('\\n');}}
document.getElementById('copy').onclick=async()=>{{const s=notes();try{{await navigator.clipboard.writeText(s);}}catch(e){{const a=document.createElement('textarea');a.value=s;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();}}document.getElementById('toast').textContent='Copied. Paste into the chat.';}};
document.getElementById('all').onclick=()=>{{for(let i=1;i<=N;i++){{document.querySelector('input[name=r'+i+'][value=approve]').checked=true;}}document.getElementById('toast').textContent='All marked approved.';}};
</script></body></html>'''
    # self-contained: embed every image so the page can be sent or opened anywhere
    import base64
    import mimetypes

    def embed(m):
        rel = m.group(2)
        p = work / rel
        if not p.exists():
            return m.group(0)
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        return f'{m.group(1)}="data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"'

    import re as _re
    page = _re.sub(r'(src|href)="((?:stills|assets)/[^"]+)"', embed, page)
    (work / "storyboard.html").write_text(page, encoding="utf-8")
    # a picture of the page and a brief, so a fresh subagent can check it against the taste checklist before the user sees it
    import shutil
    import subprocess
    from common import headless_browser
    edge = headless_browser()
    png = work / "storyboard_preview.png"
    if edge:
        try:
            subprocess.run([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size=1100,{800 + 300 * len(shots)}",
                            f"--screenshot={png}", (work / "storyboard.html").as_uri()], capture_output=True, timeout=180)
        except Exception:
            pass
    brief = f"""# Storyboard check (fresh reviewer)

You are checking a storyboard for a short-form video edit before the editor shows it to the user. Read:
- {SKILL / 'rules.md'}  (hard rules, especially the brand rule)
- {SKILL / 'taste-checklist.md'}  (the user's numbered preferences)
- {SKILL / 'style.json'}  (the style numbers)
Then look at:
- {png}  (the storyboard page as an image; if it is missing, read {work / 'storyboard.html'})
- {work / 'shots.json'}, {work / 'graphics.json'}, {work / 'inventory.json'}, {work / 'tight_words.json'}

Brand profile for this video: {B['name']}. Apply only that profile's rules (a video that is not for a client brand has no the brand's end logo and no brand rules, taste Rule 45).

Report two tables.
1. Findings: Shot | Problem | Rule it breaks | Fix.
2. Checklist: one row per numbered rule in taste-checklist.md: Rule number | PASS, FAIL or N/A | evidence. N/A needs a reason (for example "needs the rendered video").
Also check: every graphic lands on the word it is meant for, nothing sits on the face, no graphic overlaps a plate, no banned or invented text, nothing generic where a real thing was available.
"""
    (work / "BRIEF_storyboard.md").write_text(brief, encoding="utf-8")
    n_rows = page.count('<tr id="s')
    if n_rows != len(shots):
        fail(f"{n_rows} rows for {len(shots)} shots")
    ok(f"storyboard.html has {n_rows} rows, one still each. STOP: wait for the user's approval before step 8.")


if __name__ == "__main__":
    main(sys.argv[1])
