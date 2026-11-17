"""Step 6. Graphics plan: for each graphic, the exact words, the animation, and the spoken word it lands on.

Usage: python s06_graphics_plan.py <workdir>
Input : <workdir>/inventory.json, tight_words.json, shots.json
Output: <workdir>/graphics.json and an updated <workdir>/shots.json (head shots that carry a top graphic become layout C)
graphics.json: {"graphics": [{id, kind, layout, zone, start, end, trigger_word, trigger_text, text, lines, asset,
                              anim, enter_frames, exit_frames, width_frac}],
                "title": {line1, line2, start, end}, "end_logo": {start, end, asset},
                "emphasis": [word indices]}
Rules (style.json):
  - a graphic starts on the frame its trigger word starts (within 0.05 s)
  - entrance is snap (2 frames) for keyword text, logos and list lines; pop (5 frames, ease-out) for photos and cards
  - hold 1.2 to 4.0 s, ending at the end of the sentence that holds the trigger word where possible
  - top graphics live in the graphic zone (6% to 33% of height), above the face box, never over the face
  - the brand's end logo appears only as the end card, last 2.0 s
  - emphasised caption words are the beat triggers, capped near 10% of caption time
Check : every start is within 0.05 s of its trigger word; no two top graphics overlap in time;
        everything sits inside the video; zone does not touch the face box; screen changes per 10 s inside 1.3 to 8.6;
        no banned word and no study-creator branding on screen.
"""
import sys
from pathlib import Path

from common import SKILL, STYLE, banned_words, fail, load, ok, save

FPS = 30


def fr(t):
    return round(t * FPS) / FPS


def _aspect(path):
    """height / width of an image asset, so Edit.jsx can scroll a tall capture inside its card (Rule 40)."""
    if not path:
        return None
    from PIL import Image
    with Image.open(path) as im:
        return round(im.size[1] / im.size[0], 4)


def main(work):
    work = Path(work)
    tw = load(work / "tight_words.json")
    words, T = tw["words"], tw["duration"]
    inv = load(work / "inventory.json")
    shots = load(work / "shots.json")
    beats = load(work / "beats.json")["beats"]
    A = STYLE["animation"]
    G = STYLE["geometry"]
    zone = G["graphic_zone"]
    face_top = G["face_box"]["y"]
    kinds = STYLE["graphics"]["kinds"]

    def sentence_end(i):
        j = i
        while j < len(words) - 1 and not words[j]["w"].endswith((".", "?", "!")):
            j += 1
        return words[j]["end"]

    graphics = []
    plate_items = {s["item"] for s in shots["shots"] if s.get("item") is not None}
    for k, it in enumerate(inv["items"]):
        if it["kind"] == "nothing" or it["kind"] in ("plate_card", "plate_inset"):
            continue
        tgt = words[it["trigger_word"]]
        start = fr(tgt["start"])
        anim = "snap" if it["kind"] in ("keyword_text", "logo", "numbered_list") else "pop"
        if it["kind"] == "numbered_list":
            last = words[it["lines"][-1]["word"]]
            end = last["end"] + 1.2
        else:
            hold = A["keyword_hold_s"] if it["kind"] == "keyword_text" else A["graphic_hold_s"]
            end = min(sentence_end(it["trigger_word"]) + 0.3, start + hold["max"])
            end = max(end, start + hold["min"])
            if it.get("scroll"):
                # a scrolling capture needs time to read (G38): hold the full max, overlaps trim it later
                end = max(end, start + hold["max"])
        end = fr(min(end, T))
        wf = kinds[it["kind"]].get("width_frac", 0.8)
        wf = wf[1] if isinstance(wf, list) else wf
        graphics.append({"id": len(graphics) + 1, "item": k, "kind": it["kind"], "layout": "C", "zone": [zone["y0"], zone["y1"]],
                         "start": start, "end": end, "trigger_word": it["trigger_word"], "trigger_text": tgt["w"],
                         "text": it.get("text", ""), "editor_placeholder": bool(it.get("editor_placeholder")), "lines": it.get("lines", []), "asset": it.get("asset_used") or it.get("asset"),
                         "anim": anim, "enter_frames": A["snap"]["frames"] if anim == "snap" else A["pop"]["frames"],
                         "exit_frames": A["exit"]["frames"], "width_frac": wf,
                         "scroll": bool(it.get("scroll")), "aspect": _aspect(it.get("asset_used") or it.get("asset"))})
    # title and end logo
    title_end = fr(min(float(inv["title"].get("end", 5.0)), 5.0, T))  # inventory title may end sooner (never later than 5 s)
    title = {**inv["title"], "start": 0.0, "end": title_end}
    logo = STYLE["brand"].get("end_logo")
    logo_asset = str(SKILL / logo) if logo else None
    end_logo = {"start": fr(max(0.0, T - 2.0)), "end": fr(T), "asset": logo_asset}
    if not logo_asset:
        end_logo = {"start": fr(T), "end": fr(T), "asset": None}  # personal profile: no logo, so no end-card window (graphics may run to the end)

    # emphasis words: beat triggers, trimmed to about 10% of caption time
    trig = [t["word"] for b in beats for t in b["triggers"]]
    total_cap = sum(w["end"] - w["start"] for w in words)
    emph, acc = [], 0.0
    for i in sorted(set(trig)):
        d = words[i]["end"] - words[i]["start"]
        if (acc + d) / total_cap <= 0.12:
            emph.append(i)
            acc += d

    # fit each graphic above the face: sample the face top while the graphic is up, keep 0.03 of clearance
    import cv2
    import numpy as np
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(str(work / "tight.mp4"))
    fcy = G["face_centre"]["y"]

    def face_top_at(t):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        okf, fr_ = cap.read()
        if not okf:
            return None
        gray = cv2.cvtColor(cv2.resize(fr_, (270, 480)), cv2.COLOR_BGR2GRAY)
        fs = casc.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
        return None if len(fs) == 0 else max(fs, key=lambda q: q[2] * q[3])[1] / 480

    fit_notes = []
    for g in graphics:
        tops = [face_top_at(t) for t in np.arange(g["start"], g["end"], 0.25)]
        tops = [x for x in tops if x is not None]
        if not tops:
            continue
        sc = max([s["scale"] for s in shots["shots"] if s["start"] < g["end"] and s["end"] > g["start"]] or [1.0])
        top_scaled = fcy + (min(tops) - fcy) * sc
        allowed = round(top_scaled - 0.04, 3)
        if allowed < g["zone"][1]:
            g["zone"][1] = max(allowed, g["zone"][0])
            fit_notes.append(f"graphic {g['id']} zone shortened to {g['zone'][1]:.2f} of height (face top reaches {top_scaled:.2f})")
    cap.release()

    # a top graphic never runs into a full plate: end it where the plate starts
    for g in graphics:
        for s in shots["shots"]:
            if s["layout"] in ("D", "E") and g["start"] < s["start"] < g["end"]:
                g["end"] = fr(s["start"])
            elif s["layout"] in ("D", "E") and s["start"] <= g["start"] < s["end"]:
                g["end"] = g["start"]  # starts inside a plate: drop it below
    for g in graphics:
        g["end"] = min(g["end"], end_logo["start"])  # the end card owns the last 2 s
    graphics = [g for g in graphics if g["end"] - g["start"] > 0.05]

    # checks
    problems = []
    for g in graphics:
        if g["end"] - g["start"] < 1.0 and g["kind"] != "numbered_list":
            problems.append(f"graphic {g['id']} is only {g['end'] - g['start']:.1f} s long after the plate cut. Move its trigger earlier.")
        if g["zone"][1] - g["zone"][0] < 0.10 and g["kind"] not in ("keyword_text",):
            problems.append(f"graphic {g['id']} has only {g['zone'][1] - g['zone'][0]:.2f} of height above the face. Move its trigger to a moment the head is lower, or film with more headroom.")
    for g in graphics:
        if abs(g["start"] - words[g["trigger_word"]]["start"]) > 0.05:
            problems.append(f"graphic {g['id']} starts {g['start']:.2f} s but its word starts {words[g['trigger_word']]['start']:.2f} s")
        if g["end"] > T + 1e-6 or g["start"] < 0:
            problems.append(f"graphic {g['id']} runs outside the video")
        if g["zone"][1] >= face_top:
            problems.append(f"graphic {g['id']} zone reaches the face box")
    for g in graphics:
        if g["start"] < title["end"] and g["kind"] != "photo_insert":
            problems.append(f"graphic {g['id']} ({g['kind']}) starts at {g['start']:.1f} s, inside the title window (0 to {title['end']:.0f} s). "
                            "Only a corner photo may sit with the title. Move its trigger word later or drop it.")
    top = sorted(graphics, key=lambda g: g["start"])
    for a, b in zip(top[:-1], top[1:]):
        if b["start"] < a["end"] - 1e-6:
            # shorten the earlier one so they never overlap
            a["end"] = fr(b["start"])
            if a["end"] - a["start"] < A["graphic_hold_s"]["min"] - 0.01 and a["kind"] != "numbered_list":
                problems.append(f"graphics {a['id']} and {b['id']} overlap and {a['id']} cannot be shortened below {A['graphic_hold_s']['min']} s. Move one trigger.")
    bad = banned_words()
    for g in graphics:
        blob = (g["text"] + " ".join(l["text"] for l in g["lines"])).lower()
        for b in bad:
            if b in blob:
                problems.append(f"graphic {g['id']} contains banned word '{b}'")
        if g["asset"] and any(x in str(g["asset"]).lower() for x in ("mariah", "brunner", "buildai")):
            problems.append(f"graphic {g['id']} uses study-creator branding")
    n_shots = len(shots["shots"])
    changes = (n_shots - 1 + len(graphics)) / T * 10
    lo, hi = STYLE["pacing"]["changes_per_10s"]["min"], STYLE["pacing"]["changes_per_10s"]["max"]
    if T >= 20 and not lo <= changes <= hi:
        problems.append(f"screen changes per 10 s is {changes:.1f}, outside {lo} to {hi}")

    # Rule 1 "check everywhere": flag any stretch over 5 s where nothing changes on screen (no cut, no graphic in or out)
    events = sorted({0.0, T} | {s["start"] for s in shots["shots"]} | {g["start"] for g in graphics} | {g["end"] for g in graphics})
    dead = [(round(a, 1), round(b - a, 1)) for a, b in zip(events, events[1:]) if b - a > 5.0]
    for a, d in dead:
        fit_notes.append(f"Rule 1: nothing changes for {d} s from {a} s. Add a real graphic on a spoken word there, or say why not.")

    # head shots that carry a top graphic become layout C
    for s in shots["shots"]:
        if s["layout"] in ("A", "B"):
            hit = [g for g in graphics if g["start"] < s["end"] and g["end"] > s["start"] and g["layout"] == "C"]
            if hit and s["layout"] == "A":
                s["layout"] = "C"
    save(work / "shots.json", shots)
    save(work / "graphics.json", {"graphics": graphics, "title": title, "end_logo": end_logo, "emphasis": emph, "changes_per_10s": round(changes, 2)})
    print(f"{len(graphics)} top graphic(s), {len(emph)} emphasised word(s), {changes:.1f} screen changes per 10 s")
    for n_ in fit_notes:
        print("  fit: " + n_)
    if problems:
        print("\n".join("  - " + p for p in problems))
        fail(f"{len(problems)} graphics check(s) failed")
    ok("every graphic lands on its spoken word, nothing touches the face, one logo and only at the end")


if __name__ == "__main__":
    main(sys.argv[1])
