"""Shared paths and helpers for the edit-like-a-pro scripts."""
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
# where ffmpeg, Whisper, OpenCV, MediaPipe and the renderer live. A colleague sets VIDEO_TOOLS instead of editing code (Rule 36).
import os  # noqa: E402
IS_WIN = os.name == "nt"
# The tools folder: ~/video-tools unless VIDEO_TOOLS points somewhere else.
_DEFAULT_TOOLS = str(Path.home() / "video-tools")
TOOLS = Path(os.environ.get("VIDEO_TOOLS", _DEFAULT_TOOLS))
_EXE = ".exe" if IS_WIN else ""
FFMPEG = TOOLS / "bin" / f"ffmpeg{_EXE}"
FFPROBE = TOOLS / "bin" / f"ffprobe{_EXE}"
# Optional icon font (not used by the standard edit).
ICON_FONT = Path(r"C:\Windows\Fonts\SegoeIcons.ttf") if IS_WIN else TOOLS / "fonts" / "SegoeIcons.ttf"


def headless_browser():
    """Edge on Windows, Edge or Chrome on a Mac. Used for storyboard screenshots. None if neither is found."""
    import shutil as _sh
    cands = [_sh.which("msedge"),
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             _sh.which("google-chrome"), _sh.which("chromium")]
    return next((c for c in cands if c and Path(c).exists()), None)
REMOTION = TOOLS / "remotion"
MODELS = TOOLS / "models"

# the OpenCV and faster-whisper libraries live in video-tools/py
sys.path.insert(0, str(TOOLS / "py"))

STYLE = json.loads((SKILL / "style.json").read_text(encoding="utf-8"))


def load_brand(work=None):
    """Taste Rule 45: every video uses its own brand profile from brands/.
    $WD/brand.json: {"profile": "<file name in brands/ without .json>", ...any token to override}.
    No brand.json: the default profile."""
    cfg = {}
    if work and (Path(work) / "brand.json").exists():
        cfg = json.loads((Path(work) / "brand.json").read_text(encoding="utf-8"))
    name = cfg.get("profile") or "default"
    brand = json.loads((SKILL / "brands" / f"{name}.json").read_text(encoding="utf-8"))
    brand.update({k: v for k, v in cfg.items() if k != "profile"})
    return brand


# every script takes $WD as its first argument, so the brand for this video is set once here
_WD = sys.argv[1] if len(sys.argv) > 1 and Path(sys.argv[1]).is_dir() else None
STYLE["brand"] = load_brand(_WD)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, obj):
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    return subprocess.run([str(c) for c in cmd], **kw)


def probe(path):
    out = run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout
    return json.loads(out)


def fail(msg):
    print("CHECK FAILED: " + msg)
    sys.exit(1)


def ok(msg):
    print("CHECK PASSED: " + msg)


def banned_words():
    """Lines starting with '- ' under the 'Banned words' heading in rules.md."""
    txt = (SKILL / "rules.md").read_text(encoding="utf-8")
    m = re.search(r"## Banned words.*?\n(.*?)(\n## |\Z)", txt, re.S)
    return [ln[2:].strip().lower() for ln in (m.group(1).splitlines() if m else []) if ln.startswith("- ") and ln[2:].strip()]


def fmt_t(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def audio_db(path, sr=16000):
    """Loudness of the audio in 10 ms frames, in dB, plus the room-noise floor (10th percentile).
    Used to put every cut in real silence (Rule 25)."""
    import numpy as np
    raw = run([FFMPEG, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], text=False).stdout
    a = np.frombuffer(raw, np.float32)
    hop = sr // 100
    n = len(a) // hop
    db = 20 * np.log10(np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9)
    return db, float(np.percentile(db, 10))


def quietest(db, t0, t1):
    """Time (s) of the quietest 10 ms frame between t0 and t1, and its dB."""
    import numpy as np
    i0, i1 = max(0, int(round(t0 * 100))), min(len(db) - 1, int(round(t1 * 100)))
    if i1 <= i0:
        i = max(0, min(len(db) - 1, i0))
        return i / 100.0, float(db[i])
    # smooth over 30 ms so one quiet frame inside a word does not win
    seg = np.convolve(db[i0:i1 + 1], np.ones(3) / 3, mode="same")
    k = int(np.argmin(seg))
    return (i0 + k) / 100.0, float(seg[k])


def silent_edge(db, floor, t, limit, direction, quiet_db=5.0, run_frames=4):
    """Walk from time t toward limit (direction -1 = back, +1 = forward) and return the first moment where the sound
    has been at room level (floor + quiet_db) for run_frames x 10 ms. That is where a cut is inaudible.
    Returns None if there is no such moment before the limit."""
    import numpy as np
    sm = np.convolve(db, np.ones(3) / 3, mode="same") - floor
    i, stop, run_ = int(round(t * 100)), int(round(limit * 100)), 0
    i = max(0, min(len(sm) - 1, i))
    stop = max(0, min(len(sm) - 1, stop))
    while (i >= stop) if direction < 0 else (i <= stop):
        run_ = run_ + 1 if sm[i] <= quiet_db else 0
        if run_ >= run_frames:
            # centre of the quiet run
            return (i + direction * -(run_frames // 2)) / 100.0
        i += direction
    return None
