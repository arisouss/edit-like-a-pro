"""Cut the user out of his background, frame for frame, so things can sit BEHIND him (words behind the head,
a new or scrolling background, a takeover scene he steps in front of). Rule 42.

Usage : python3.12 cutout.py "$WD" [--video tight.mp4] [--from 0 --to 12.5]
Input : $WD/tight.mp4 (or --video). Model: video-tools/models/mediapipe/selfie_multiclass_256x256.tflite
        (Google MediaPipe, downloaded once from storage.googleapis.com/mediapipe-models).
Output: $WD/subject.webm  VP9 with alpha, same size, fps and frame count as the input (only his body is opaque)
        $WD/cutout.json   frames, mean matte coverage, the window used, the edge-softness setting
Check : frame count equals the input; matte coverage between 5% and 85% on average (0 = nobody found,
        ~100 = the model took the whole frame); no frame with an empty matte for more than 1 s in a row.
Notes : the matte is smoothed over time (no flicker) and feathered 2 px at the edge (G55). Anything held in the
        hand (phone, mic, mug) may be cut away; look at the review frames before using it on such a shot.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import TOOLS, FFMPEG, MODELS, load, save, probe, fail, ok  # noqa: E402

import numpy as np  # noqa: E402
import cv2  # noqa: E402


def main():
    if len(sys.argv) < 2:
        fail('usage: cutout.py "$WD" [--video tight.mp4] [--from s --to s]')
    wd = Path(sys.argv[1])
    a = sys.argv[2:]
    video = wd / (a[a.index("--video") + 1] if "--video" in a else "tight.mp4")
    t_from = float(a[a.index("--from") + 1]) if "--from" in a else 0.0
    t_to = float(a[a.index("--to") + 1]) if "--to" in a else None
    model = MODELS / "mediapipe" / "selfie_multiclass_256x256.tflite"
    if not model.exists():
        fail(f"model missing: {model}. Download selfie_multiclass_256x256.tflite from storage.googleapis.com/mediapipe-models (G55).")
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions

    info = probe(video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=str(model)), running_mode=vision.RunningMode.VIDEO,
        output_confidence_masks=True, output_category_mask=False))

    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_MSEC, t_from * 1000)
    out = wd / "subject.webm"
    enc = subprocess.Popen([str(FFMPEG), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", f"{fps}",
                            "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "4M", "-deadline", "realtime", "-cpu-used", "8",
                            "-auto-alt-ref", "0", str(out)], stdin=subprocess.PIPE)
    prev, n, cover, empty_run, worst_empty = None, 0, [], 0, 0
    while True:
        okf, frame = cap.read()
        if not okf:
            break
        t = t_from + n / fps
        if t_to is not None and t > t_to:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(t * 1000))
        bg = res.confidence_masks[0].numpy_view()  # class 0 = background
        m = 1.0 - cv2.resize(bg, (w, h), interpolation=cv2.INTER_LINEAR)
        # edge-aware refine on the full frame, then temporal smoothing against flicker
        try:
            m = cv2.ximgproc.guidedFilter(guide=frame, src=m.astype(np.float32), radius=8, eps=1e-3)
        except AttributeError:
            m = cv2.GaussianBlur(m, (5, 5), 0)
        m = np.clip((m - 0.35) / 0.35, 0, 1)  # steepen: solid inside, 2 to 3 px soft edge
        if prev is not None:
            m = 0.65 * m + 0.35 * prev
        prev = m
        c = float(m.mean())
        cover.append(c)
        empty_run = empty_run + 1 if c < 0.01 else 0
        worst_empty = max(worst_empty, empty_run)
        rgba = np.dstack([rgb, (m * 255).astype(np.uint8)])
        enc.stdin.write(rgba.tobytes())
        n += 1
    cap.release()
    enc.stdin.close()
    enc.wait()
    if enc.returncode:
        fail("ffmpeg VP9 alpha encode failed")
    expect = n
    got = int(subprocess.run([str(FFMPEG.with_name(FFMPEG.name.replace("ffmpeg", "ffprobe"))), "-v", "error", "-count_frames", "-select_streams", "v:0",
                              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip() or 0)
    mean = sum(cover) / max(1, len(cover))
    save(wd / "cutout.json", {"video": video.name, "from": t_from, "to": t_to, "frames": n, "fps": fps, "mean_cover": round(mean, 3),
                              "longest_empty_frames": worst_empty})
    if got != expect:
        fail(f"subject.webm has {got} frames, expected {expect}: the cutout would drift. Re-run.")
    if not 0.05 <= mean <= 0.85:
        fail(f"matte covers {mean:.0%} of the frame on average: the model did not find him cleanly")
    if worst_empty > fps:
        fail(f"no person found for {worst_empty / fps:.1f} s in a row (he left the frame?). Limit the window with --from/--to.")
    ok(f"subject.webm: {n} frames, matte {mean:.0%} of the frame on average")


if __name__ == "__main__":
    main()
