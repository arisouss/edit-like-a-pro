"""Generated music with Google Lyria (taste Rule 46 here, the reels skill taste Rule 13). Shared by edit-like-a-pro and the reels skill.

A music spec in a plan or music.json:
  {"generate": "<prompt: genre, BPM, instruments, mood>", "full": false, "gain": 0.3}
  full false: lyria-3-clip-preview, 30 s, about $0.04. Fine for videos up to about 30 s (longer ones loop it).
  full true : lyria-3.5, a couple of minutes, about $0.08. Use it for videos over 30 s so the music never loops.
ensure(work, spec) makes the track ONCE and caches it in <work>/music/lyria-<hash>.mp3 with a manifest entry
(prompt, model, cost, date, licence note). Re-renders reuse the file: changing the prompt is the only thing that
spends money again. Never call this in a loop or for many variants without asking the user (every call is paid).
"""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "Desktop" / "Claude" / ".claude" / "scripts" / "generate-music.js"
LICENCE = "Generated with Google Lyria through your own Gemini API account (paid tier); carries Google's SynthID watermark."


def ensure(work, spec):
    """Return the path of the music file for this spec, generating it only if it does not exist yet."""
    work = Path(work)
    if spec.get("file") and not spec.get("generate"):
        return Path(spec["file"]) if Path(spec["file"]).is_absolute() else work / spec["file"]
    prompt = spec["generate"].strip()
    full = bool(spec.get("full"))
    key = hashlib.sha1(f"{prompt}|{full}".encode()).hexdigest()[:10]
    out = work / "music" / f"lyria-{key}.mp3"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["node", str(SCRIPT), prompt, str(out)] + (["--full"] if full else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not out.exists():
        raise RuntimeError("Lyria generation failed: " + (r.stderr or r.stdout)[-600:])
    man = work / "music" / "manifest.json"
    entries = json.loads(man.read_text()) if man.exists() else []
    entries.append({"file": out.name, "prompt": prompt, "model": "lyria-3.5" if full else "lyria-3-clip-preview",
                    "cost_usd": 0.08 if full else 0.04, "date": datetime.date.today().isoformat(), "licence": LICENCE})
    man.write_text(json.dumps(entries, indent=1))
    print(f"music generated: {out.name} ({'full track' if full else '30 s clip'}, about ${0.08 if full else 0.04})", flush=True)
    return out
