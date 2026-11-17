"""Step 12: safe cleanup. Dry run by default; --apply MOVES listed files into _cleanup_archive.
Only files named in cleanup.json "safe_to_recreate" move. The protected list always wins.
Usage: python s12_cleanup.py "<WD>" [--apply]
"""
import json, shutil, sys
from pathlib import Path

PROTECT_NAMES = {"approved.json", "final.mp4", "inventory.json", "beats.json", "shots.json",
                 "graphics.json", "fx.json", "props.json", "brand.json", "music.json",
                 "cleanup.json", "notes.md", "words.json", "tight_words.json"}

def main():
    if len(sys.argv) < 2:
        print("CHECK FAILED: usage s12_cleanup.py <WD> [--apply]"); sys.exit(1)
    wd = Path(sys.argv[1]).resolve(); apply = "--apply" in sys.argv
    if not (wd / "approved.json").exists():
        print("CHECK FAILED: no approved.json, cleanup runs only after a specific final approval"); sys.exit(1)
    cj = wd / "cleanup.json"
    if not cj.exists():
        print("CHECK FAILED: no cleanup.json, nothing is recorded as safe to recreate"); sys.exit(1)
    listed = json.loads(cj.read_text()).get("safe_to_recreate", [])
    plan, skipped = [], []
    for item in listed:
        p = (wd / item).resolve()
        if wd not in p.parents or not p.exists():
            skipped.append((item, "outside the work folder or missing")); continue
        if p.name in PROTECT_NAMES or p.name.startswith("source_raw"):
            skipped.append((item, "protected")); continue
        plan.append(p)
    for p in plan:
        print(("MOVE " if apply else "WOULD MOVE ") + str(p.relative_to(wd)))
    for item, why in skipped:
        print(f"SKIP {item}: {why}")
    if apply:
        arc = wd / "_cleanup_archive"; arc.mkdir(exist_ok=True)
        for p in plan:
            shutil.move(str(p), str(arc / p.name))
    print("CHECK PASSED")

main()
