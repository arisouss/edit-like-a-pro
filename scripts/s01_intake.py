"""Step 1. Intake: check the raw video and flag problems, then normalise it.

Usage: python s01_intake.py <raw video> <workdir>
Input : raw iPhone video (.mov or .mp4)
Output: <workdir>/intake.json and <workdir>/source_norm.mp4 (1080x1920, 30 fps constant, H.264, SDR if possible)
Check : exit 0 only if there is no blocker flag. Warnings are listed and do not stop the run.
"""
import re
import sys
from pathlib import Path

import numpy as np

from common import FFMPEG, STYLE, fail, load, ok, probe, run, save

import cv2  # noqa: E402  (path set up in common)


def main(raw, workdir):
    raw, work = Path(raw), Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    if not raw.exists():
        fail(f"raw video not found: {raw}")
    info = probe(raw)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        fail("no video stream")
    flags = []  # (severity, text)
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) in (90, 270):
        w, h = h, w
    dur = float(info["format"]["duration"])
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    avg = v.get("avg_frame_rate", "0/1").split("/")
    avg_fps = float(avg[0]) / float(avg[1]) if float(avg[1]) else fps
    vfr = abs(fps - avg_fps) > 0.5
    hdr = v.get("color_transfer") in ("arib-std-b67", "smpte2084")
    if w >= h:
        flags.append(("blocker", f"video is landscape ({w}x{h}). The style is vertical 1080x1920. Re-film vertical."))
    if min(w, h) < STYLE["capture_targets"]["min_width_px"]:
        flags.append(("warn", f"width {min(w, h)} px is under 1080. It will be upscaled."))
    if hdr:
        flags.append(("warn", "HDR video (HLG/PQ). Colors can look washed out. Film in SDR: Settings > Camera > Formats > turn off HDR Video."))
    if vfr:
        flags.append(("warn", f"variable frame rate ({fps:.1f} vs {avg_fps:.1f}). It will be converted to constant 30 fps."))
    if dur < 8:
        flags.append(("warn", f"only {dur:.1f} s long."))
    if dur > 180:
        flags.append(("warn", f"{dur:.0f} s is long for this style (study videos run 43 to 109 s)."))
    if not a:
        flags.append(("blocker", "no audio track."))

    # normalise first, so every later step reads the same file
    norm = work / "source_norm.mp4"
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"
    if hdr:
        vf = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv," + vf
    r = run([FFMPEG, "-v", "error", "-y", "-i", raw, "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "fast",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", norm])
    if r.returncode != 0 and hdr:  # build without zimg: fall back to a plain conversion
        flags.append(("warn", "HDR tonemap unavailable in this ffmpeg build; converted without tonemapping."))
        r = run([FFMPEG, "-v", "error", "-y", "-i", raw, "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
                 "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", norm])
    if r.returncode != 0:
        fail("ffmpeg could not normalise the video: " + r.stderr[-300:])

    # audio level and silence
    loud = {}
    if a:
        r = run([FFMPEG, "-hide_banner", "-nostats", "-i", norm, "-vn", "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json,silencedetect=n=-45dB:d=0.4", "-f", "null", "-"])
        m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr)
        if m:
            import json
            loud = json.loads(m.group(0))
        sil = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]
        lufs = float(loud.get("input_i", "nan"))
        tp = float(loud.get("input_tp", "nan"))
        if lufs < -40:
            flags.append(("blocker", f"audio is almost silent ({lufs:.0f} LUFS)."))
        elif lufs < -30:
            flags.append(("warn", f"quiet audio ({lufs:.0f} LUFS). It will be normalised, noise will rise."))
        if tp > -0.1:
            flags.append(("warn", f"audio peaks at {tp:.1f} dBTP: possible clipping."))
        silence_total = sum(sil)
    else:
        lufs = tp = float("nan")
        silence_total = 0.0

    # framing: sample 24 frames, find the face
    cap = cv2.VideoCapture(str(norm))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    boxes, lum, blur = [], [], []
    for k in range(24):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((k + 0.5) / 24 * n))
        okf, f = cap.read()
        if not okf:
            continue
        s = cv2.resize(f, (270, 480))
        g = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
        lum.append(float(g.mean()))
        blur.append(float(cv2.Laplacian(g, cv2.CV_64F).var()))
        faces = casc.detectMultiScale(g, 1.1, 5, minSize=(40, 40))
        if len(faces):
            x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])
            boxes.append([x / 270, y / 480, fw / 270, fh / 480])
    cap.release()
    ct = STYLE["capture_targets"]
    face_share = len(boxes) / 24
    fb = [float(np.median([b[i] for b in boxes])) for i in range(4)] if boxes else None
    if face_share < ct["face_found_min_share"]:
        flags.append(("blocker", f"face found in only {face_share:.0%} of sampled frames (need {ct['face_found_min_share']:.0%}). Check framing and light."))
    if fb:
        cx, cy = fb[0] + fb[2] / 2, fb[1] + fb[3] / 2
        if not ct["face_width_frac_ok"][0] <= fb[2] <= ct["face_width_frac_ok"][1]:
            flags.append(("warn", f"face is {fb[2]:.2f} of frame width (style {STYLE['geometry']['face_box']['w']}, ok {ct['face_width_frac_ok']}). Move the phone {'closer' if fb[2] < ct['face_width_frac_ok'][0] else 'back'}."))
        if not ct["face_centre_x_ok"][0] <= cx <= ct["face_centre_x_ok"][1]:
            flags.append(("warn", f"face centre is {cx:.2f} across (style {STYLE['geometry']['face_centre']['x']}). Centre yourself."))
        if not ct["face_centre_y_ok"][0] <= cy <= ct["face_centre_y_ok"][1]:
            flags.append(("warn", f"face centre is {cy:.2f} down (style {STYLE['geometry']['face_centre']['y']}). The top third needs room for graphics: tilt or lower the phone."))
    if lum and np.median(lum) < 70:
        flags.append(("warn", f"dark footage (mean luma {np.median(lum):.0f}/255). Add light in front of you."))
    if lum and np.median(lum) > 215:
        flags.append(("warn", "very bright footage, check for blown highlights."))
    if blur and np.median(blur) < 30:
        flags.append(("warn", f"soft or blurry frames (sharpness {np.median(blur):.0f}). Check focus and lens."))

    res = {"raw": str(raw), "source_norm": str(norm), "duration_s": round(dur, 2), "width": w, "height": h, "rotation": rot,
           "fps_reported": round(fps, 2), "fps_avg": round(avg_fps, 2), "vfr": vfr, "hdr": hdr,
           "codec": v.get("codec_name"), "lufs": lufs, "true_peak": tp, "silence_total_s": round(silence_total, 2),
           "face_share": round(face_share, 2), "face_box_median": fb, "luma_median": round(float(np.median(lum)), 1) if lum else None,
           "sharpness_median": round(float(np.median(blur)), 1) if blur else None,
           "flags": [{"severity": s, "text": t} for s, t in flags]}
    save(work / "intake.json", res)
    print(f"{raw.name}: {dur:.1f} s, {w}x{h}, {fps:.0f} fps, face found {face_share:.0%}, {lufs:.1f} LUFS")
    for s, t in flags:
        print(f"  [{s.upper()}] {t}")
    blockers = [t for s, t in flags if s == "blocker"]
    if blockers:
        fail("; ".join(blockers))
    ok(f"intake.json written, {len(flags)} warning(s), no blockers")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
