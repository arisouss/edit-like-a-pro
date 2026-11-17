"""Step 10. Render and check: final export, loudness, captions vs audio, face not covered, brand.

Usage: python s10_final_check.py <workdir> [--skip-asr]
Input : <workdir>/draft.mp4 (after step 9 fixes), props.json, tight_words.json, tight.mp4
Output: <workdir>/final.mp4 (1080x1920, 30 fps, about -14 LUFS) and <workdir>/final_check.json
Checks (all must pass):
  1 format      1080x1920, 30 fps, H.264, AAC stereo
  2 loudness    integrated -14 LUFS within 1 LU, true peak at or under -1.0 dBTP
  3 captions    caption words are exactly the speaker's words (tight_words), and a fresh Whisper pass over final.mp4
                matches them with word error rate at or under 10%
  4 face        in head shots, the face seen in tight.mp4 is still visible in final.mp4, and no top graphic reaches below the face top
  5 brand       props use only this video's brand tokens, no banned words, no study-creator strings, logo only in the last 2.1 s
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

from common import FFMPEG, STYLE, banned_words, fail, load, ok, probe, run, save

import cv2  # noqa: E402


def toks(s):
    return re.findall(r"[a-z0-9\u05d0-\u05ea']+", s.lower())  # Latin, digits and Hebrew letters (no niqqud)


def wer(ref, hyp):
    d = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=int)
    d[:, 0] = np.arange(len(ref) + 1)
    d[0, :] = np.arange(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    return d[-1, -1] / max(1, len(ref))


def main(work, skip_asr=False):
    work = Path(work)
    res, problems = {}, []
    draft = work / "draft.mp4"
    if not draft.exists():
        fail("draft.mp4 missing. Run step 8.")
    # loudness: two-pass loudnorm to -14 LUFS, -1.5 dBTP
    r = run([FFMPEG, "-hide_banner", "-nostats", "-i", draft, "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr)
    if not m:
        fail("could not measure loudness: " + r.stderr[-300:])
    L = json.loads(m.group(0))
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={L['input_i']}:measured_TP={L['input_tp']}:measured_LRA={L['input_lra']}"
          f":measured_thresh={L['input_thresh']}:offset={L['target_offset']}:linear=true")
    final = work / "final.mp4"
    mus = load(work / "music.json") if (work / "music.json").exists() else None
    if mus:
        # soft music bed (Rule 32): looped to length, fades in and out, and ducks under the voice so every word stays clear
        if mus.get("generate"):
            # Rule 46: generated with Lyria once and cached in $WD/music (lyria.py); the licence note comes with it
            import lyria
            mus["file"] = str(lyria.ensure(work, mus))
            mus.setdefault("licence", lyria.LICENCE)
        mf = Path(mus["file"])
        if not mf.exists():
            fail(f"music file missing: {mf}")
        T_ = float(probe(draft)["format"]["duration"])
        g = float(mus.get("gain_db", -20))
        fc = (f"[0:a]{af},asplit=2[v][key];"
              f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{T_:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
              f"volume={g}dB,afade=t=in:d=1.2,afade=t=out:st={max(0, T_ - 2.2):.3f}:d=2.2[m];"
              f"[m][key]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350[duck];"
              f"[v]aformat=sample_rates=48000:channel_layouts=stereo[v2];[v2][duck]amix=inputs=2:duration=first:normalize=0[mix]")
        mixed = work / "draft_music.wav"
        r = run([FFMPEG, "-v", "error", "-y", "-i", draft, "-i", mf, "-filter_complex", fc, "-map", "[mix]", "-ar", "48000", mixed])
        if r.returncode != 0:
            fail("music mix failed: " + r.stderr[-300:])
        r = run([FFMPEG, "-hide_banner", "-nostats", "-i", mixed, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
        L = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr).group(0))
        af2 = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={L['input_i']}:measured_TP={L['input_tp']}:measured_LRA={L['input_lra']}"
               f":measured_thresh={L['input_thresh']}:offset={L['target_offset']}:linear=true")
        r = run([FFMPEG, "-v", "error", "-y", "-i", draft, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", af2, "-ar", "48000", "-ac", "2",
                 "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
        res["music"] = {"file": mf.name, "licence": mus.get("licence", "NOT RECORDED"), "gain_db": g}
        if not mus.get("licence"):
            problems.append("music.json has no licence: only use a track you are allowed to use (Rule 32)")
    else:
        r = run([FFMPEG, "-v", "error", "-y", "-i", draft, "-c:v", "copy", "-af", af, "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
    if r.returncode != 0:
        fail("final export failed: " + r.stderr[-300:])

    # 1 format
    info = probe(final)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    num, den = v["r_frame_rate"].split("/")
    fmt_ok = (v["width"], v["height"]) == (1080, 1920) and abs(float(num) / float(den) - 30) < 0.01 and v["codec_name"] == "h264" and a and a["codec_name"] == "aac"
    res["format"] = {"ok": bool(fmt_ok), "w": v["width"], "h": v["height"], "fps": float(num) / float(den), "vcodec": v["codec_name"], "acodec": a["codec_name"] if a else None}
    if not fmt_ok:
        problems.append(f"format is {res['format']}")

    # 2 loudness
    r = run([FFMPEG, "-hide_banner", "-nostats", "-i", final, "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    L2 = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr).group(0))
    lufs, tp = float(L2["input_i"]), float(L2["input_tp"])
    res["loudness"] = {"lufs": lufs, "true_peak": tp}
    if abs(lufs + 14) > 1.0:
        problems.append(f"loudness {lufs:.1f} LUFS is not within 1 LU of -14")
    if tp > -1.0:
        problems.append(f"true peak {tp:.1f} dBTP is above -1.0")

    # 3 captions
    props = load(work / "props.json")
    fluid = props.get("mode") == "fluid"
    tw = load(work / "tight_words.json")["words"]
    if fluid:
        cap_tokens = toks(" ".join(w["w"] for p in props["phrases"] for w in p["words"]))
    else:
        cap_tokens = toks(" ".join(p["text"] for p in props["pages"]))
    src_tokens = toks(" ".join(w["w"] for w in tw))
    exact = cap_tokens == src_tokens
    res["captions"] = {"identical_to_speaker_words": exact, "caption_words": len(cap_tokens)}
    if not exact:
        problems.append("caption words differ from the speaker's words (tight_words.json)")
    if not skip_asr:
        raw = run([FFMPEG, "-v", "error", "-i", final, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], text=False).stdout
        from faster_whisper import WhisperModel
        from common import MODELS
        mdl = WhisperModel("small", device="cpu", compute_type="int8", download_root=str(MODELS))
        _wj = work / "words.json"
        _lang = (load(_wj).get("language") if _wj.exists() else None) or None
        segs, _ = mdl.transcribe(np.frombuffer(raw, np.float32), word_timestamps=False, beam_size=5, condition_on_previous_text=False, language=_lang)
        heard = toks(" ".join(s.text for s in segs))
        w = float(wer(cap_tokens, heard))
        res["captions"]["wer_vs_final_audio"] = round(w, 3)
        if w > 0.10:
            problems.append(f"captions vs final audio word error rate {w:.0%} (limit 10%)")

    # 4 face not covered
    G = STYLE["geometry"]
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    capf, capt = cv2.VideoCapture(str(final)), cv2.VideoCapture(str(work / "tight.mp4"))

    def face(cap, t):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok_, fr = cap.read()
        if not ok_:
            return None
        g = cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY)
        fs = casc.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        return None if len(fs) == 0 else max(fs, key=lambda q: q[2] * q[3])

    checked = lost = low = 0
    gfx = props.get("graphics", [])
    if fluid:
        # fluid: no shots. Wherever the camera is full frame, the face seen in tight.mp4 must be visible in the final,
        # and no card may touch the face found in the final frame.
        def cam_s(t):
            k = props["camera"]
            for a, b in zip(k, k[1:]):
                if a["t"] <= t <= b["t"]:
                    return min(a["s"], b["s"])
            return k[-1]["s"]
        t = 0.25
        while t < props["duration"] - 0.1:
            if cam_s(t) >= 0.99:
                tt = face(capt, t)
                if tt is not None:
                    checked += 1
                    ff = face(capf, t)
                    if ff is None:
                        lost += 1
                    else:
                        fx, fy, fw, fh = ff[0] / 270, ff[1] / 480, ff[2] / 270, ff[3] / 480
                        for c in props["cards"]:
                            if c["kind"] == "badge" or not (c["start"] + 0.6 <= t < c["end"] - 0.4):
                                continue
                            r = c.get("move", {}).get("rect") if c.get("move") and t >= c["move"]["at"] + 0.6 else c["rect"]
                            if not (r[0] + r[2] <= fx or fx + fw <= r[0] or r[1] + r[3] <= fy or fy + fh <= r[1]):
                                low += 1
            t += 0.5
    for s in ([] if fluid else props["shots"]):
        if s["layout"] not in ("A", "B", "C"):
            continue
        t = s["start"]
        while t < s["end"] - 0.1:
            tt = face(capt, t)
            if tt is not None:
                checked += 1
                ff = face(capf, t)
                if ff is None:
                    lost += 1
                active = [g for g in gfx if g["start"] <= t < g["end"]]
                if active:
                    top = tt[1] / 480
                    sc = s["scale"]
                    top_scaled = G["face_centre"]["y"] + (top - G["face_centre"]["y"]) * sc
                    if top_scaled < max(g["zone"][1] for g in active) + 0.01:
                        low += 1
            t += 0.5
    res["face"] = {"frames_checked": checked, "face_lost_in_final": lost, "graphic_zone_touches_face": low}
    if checked == 0:
        problems.append("no face found in tight.mp4 to compare")
    elif lost / checked > 0.08:
        problems.append(f"the face is lost in {lost} of {checked} checked head frames. Something covers it.")
    if low:
        problems.append(f"a graphic zone reaches the face top in {low} checked frame(s)")

    # 5 brand
    blob = json.dumps({"g": props.get("graphics") or props.get("cards"), "t": props["title"], "p": props.get("pages") or props.get("phrases"),
                       "r": (props.get("reveal") or {}).get("checks")}).lower()
    for b in banned_words():
        if b in blob:
            problems.append(f"banned word '{b}' appears on screen")
    for bad in ("mariah", "brunner", "buildai", "comment \\\"", "comment '"):
        if bad in blob:
            problems.append(f"study-creator branding string '{bad}' appears in the plan")
    if props["brand"] != STYLE["brand"]:
        problems.append(f"props brand tokens differ from this video's brand profile ({STYLE['brand']['name']})")
    T = props["duration"]
    if props["end_logo"].get("asset") and props["end_logo"]["start"] < T - 2.1:
        problems.append("the logo starts earlier than the last 2 seconds")
    if STYLE["brand"].get("end_logo") and any(Path(str(STYLE["brand"]["end_logo"])).stem.lower() in str(g.get("asset", "")).lower() for g in (props.get("graphics") or props.get("cards"))):
        problems.append("the brand's end logo is used as a graphic before the end card")
    res["brand"] = {"tokens_match": props["brand"] == STYLE["brand"], "logo_start": props["end_logo"]["start"], "duration": T}

    res["problems"] = problems
    save(work / "final_check.json", res)
    print(json.dumps({k: v for k, v in res.items() if k != "problems"}, indent=1))
    if problems:
        print("\n".join("  - " + p for p in problems))
        fail(f"{len(problems)} check(s) failed")
    ok("format, loudness, caption match, face visible and brand all pass. final.mp4 is ready.")


if __name__ == "__main__":
    main(sys.argv[1], "--skip-asr" in sys.argv)
