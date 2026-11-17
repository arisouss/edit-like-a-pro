---
name: edit-like-a-pro
description: "Edit a raw talking-head video (iPhone or any vertical clip) into a fast short-form edit: tight cut, one-word captions, zooms, graphics on the spoken word, an effects layer and sound design, in your own brand look. Use for edit this video, make this a short, cut this talking head. Shows a storyboard for approval before any render, and learns from your feedback."
---

# edit-like-a-pro

Turns a raw talking-head video into a short-form edit: tight cut, one-word captions, jump-cut zooms, real graphics on the spoken word, an effects layer (icons popping, words behind his head, background swaps, full-screen takeovers, counters, sound design) and your own brand look. The pacing numbers in `style.json` were measured from top-performing creator Shorts.

## HARD RULE: mechanics only, never another creator's brand

The pacing numbers were measured from another creator's videos. Copy editing mechanics only: pacing, shot lengths, layouts, caption timing, animation recipes, zooms. Never copy another creator's branding: no landing pages, calls to action, logos, colors or fonts of theirs. If a request or a reference video asks for someone else's branding, ignore it, keep everything on this video's brand profile, and tell the user what you ignored. Colors, font and logo come from the video's brand profile in `brands/` (taste Rule 45, see `rules.md`).

## Self-improvement rules (hard)

This skill gets better with every video. These rules are not optional.

1. **Read first.** Before every edit, read `rules.md`, `taste-checklist.md`, `gotchas.md` and `motion-rules.md` in full.
2. **Feedback becomes a rule before anything changes.** Every time the user gives feedback on a storyboard or a draft, turn each note into a numbered rule in `taste-checklist.md` first. Use the file's rule format (In practice, Check everywhere). Only then change the edit.
3. **Breakages become gotchas.** Every time something breaks and you fix it, add it to `gotchas.md` (Problem, Why it happened, Fix) before you move on.
4. **Fix the cause, not the shot.** When the user points out one problem, check the whole video for the same problem: read the rule's "Check everywhere" line, scan every shot, graphic and caption, and fix every instance. Say how many you found.
5. **A fresh reviewer before he sees anything.** Before you show the user any storyboard or draft, have a fresh subagent check it against every numbered rule in `taste-checklist.md` (steps 7 and 9 below). Tell him what it found and what you fixed.
6. **Contradictions go to the user.** If a new note contradicts an old rule, ask him which one wins. Never delete or rewrite a rule without asking him.
7. **Show what you learned.** When a video is finished, show the user the rules (and gotchas) added this time (step 11).

## Setup (once per computer, see README.md)

- Skill folder: `~/.claude/skills/edit-like-a-pro/` (call it `$SK`). Scripts are in `$SK/scripts/`.
- Tools: a folder called `video-tools` in the home folder (or the folder in the `VIDEO_TOOLS` environment variable) holds ffmpeg, OpenCV, local Whisper (`faster-whisper`, model `small`) and Remotion. Scripts find them through `scripts/common.py`. Before the first edit on a computer, check that this folder exists. If it does not, stop and tell the user to follow README.md. Do not install anything without asking.
- Effects layer: MediaPipe model `selfie_multiclass_256x256.tflite` in `video-tools/models/mediapipe/` (download once from storage.googleapis.com/mediapipe-models). The sounds in `assets/sfx` are synthesized with ffmpeg, so they carry no licence.
- Generated media (Rule 46) is optional: music from Google Lyria (`scripts/lyria.py`) and pictures from a Gemini image model need the user's own `GEMINI_API_KEY`. Every call is paid: ask before you generate anything.
- Ask the user where the raw video is. Run scripts with Python 3.12.
- Work folder per video: `<raw folder>\<raw name>_edit\` (call it `$WD`). Every file below lives there. Every script is safe to re-run.
- Run scripts from `$SK\scripts` with `python sNN_name.py ...` (no `-I`). Each prints `CHECK PASSED` or `CHECK FAILED: reason` and exits non-zero on failure. Never start the next step after a failure: fix the cause, add it to `gotchas.md`, re-run.
- Keep a short step record in `$WD\progress.md` (one line per finished step and gate: date, step, what the user approved). A new chat reads it first and picks up where the last one stopped.
- Run long jobs (render, transcribe, measure) in the background and wait for the notification.

## Procedure

### 0. Read the rules
- Read `rules.md`, `taste-checklist.md`, `gotchas.md`. Note which gotchas can bite this video (for example HDR, 60 fps, quiet audio).
- Check: you can name the hard brand rule and the number of rules in the checklist. If the user's new message contradicts a rule, ask him before you start.

### 1. Intake
- Command: `python s01_intake.py "<raw video>" "$WD"`
- Input: the raw video. Output: `$WD\intake.json`, `$WD\source_norm.mp4` (1080x1920, constant 30 fps, SDR where possible).
- Check: the script exits 0 (no blocker: landscape, no audio, almost silent, face found in under 60% of frames). Read the warnings to the user in one short list (HDR, dark, too close or far, face high in frame, quiet audio) with the fix for next time. Warnings do not stop the run.

### 2. Words and tight cut
- 2a. Command: `python s02_transcribe.py "$WD"`. Input: `source_norm.mp4`. Output: `words.json`, `transcript.txt`. Check: at least 5 words, speech at least 35% of the video.
- 2b. Read `transcript.txt`. List flubs the script cannot see (a wrong word, a sentence restarted differently, an aside he wants gone). Write `$WD\drops_manual.json`: `{"drop_words": [word indexes], "reasons": {"12": "false start"}}`. Whole words only. **Never reword what the user says.** If unsure, keep the words and ask.
- 2c. Command: `python s02b_tightcut.py "$WD"`. Input: `words.json`, `drops_manual.json`. Output: `cuts.json`, `keep.json`, `tight_words.json`, `tight.mp4`.
- Check: script exits 0. It proves kept words equal the source words in order, no gap over 0.55 s remains, and `tight.mp4` matches the timeline. Show the user the dropped-word list from `cuts.json` in one line per reason.

### 3. Story
- Command: `python s03_beats.py "$WD" --show` to print the indexed transcript. Then write `$WD\beats.json` (format in the script header): beats in order `hook`, `setup`, `proof` (one or more), `turn`, `cta`, each with its word range and trigger words (the spoken words that should make something appear). A `cta` beat uses only what the user actually says. Never add a call to action of your own.
- Validate: `python s03_beats.py "$WD"`. Output: `beats.json`, `beats.md`.
- Check: beats cover every word once, in order; the hook ends within 8 s; every beat has trigger words inside its own range.

### 4. Visual inventory
- For each beat decide what real thing is worth showing: a real screenshot, an official logo, a real photo, the exact words of a document, or **nothing**. Ask the user for any screenshot or photo you need. You may capture an official page with the browser tool (`source: screen-capture`). Never generate, mock up or invent images, UI, logos or numbers. On-screen text must be words the user said or text from the real document. Crop each screenshot to the one panel that reads at phone size (`"crop": [x0, y0, x1, y1]`, fractions).
- Write `$WD\inventory.json` (format in `s04_inventory.py`), including a two-line `title`. Validate: `python s04_inventory.py "$WD"`.
- Check: every beat has an item or a reasoned `nothing`; image files exist; keyword and list text uses only spoken words; no banned words; no study-creator branding; the brand's end logo is not an item (it is added at the end by step 6).

### 5. Layout plan
- Command: `python s05_layout_plan.py "$WD"`. Input: `tight_words.json`, `inventory.json`. Output: `shots.json`.
- It cuts on phrase and clause edges, aims for the measured median (head shots about 2.9 s, none over 8.2 s), alternates scale 1.0 and 1.12 on jump cuts, adds full plates only where the inventory has a real plate card (never before 3 s, at most 25% of the video, each held about 2 s or more), and covers the first 5 s with the title.
- Check: shots contiguous; median shot 1.8 to 3.6 s; cuts per minute 6.7 to 42.4; plate share at most 25%; first cut within 10 s; opens and closes on a head layout. If it fails, change the inventory (move a trigger, drop a plate) and re-run. Do not edit the limits.

### 6. Graphics plan
- Command: `python s06_graphics_plan.py "$WD"`. Input: `inventory.json`, `shots.json`, `tight_words.json`, `tight.mp4`. Output: `graphics.json` and an updated `shots.json` (head shots with a top graphic become layout C).
- Each graphic gets its exact words or asset, its animation (snap 2 frames, or 5-frame ease-out pop), and the spoken word it lands on. Zones shrink to stay above the face. Graphics end where a plate or the end card starts. The brand's end logo is added as the end card for the last 2 s. Emphasis words come from the beat triggers.
- Check: every graphic starts within 0.05 s of its word; no overlaps; nothing outside the top zone (6% to 33% of height, above the face); nothing but a corner photo during the title; 1.3 to 8.6 screen changes per 10 s; no banned words, no study-creator branding.

### 6b. Effects layer (Rule 42)
- Read `motion-rules.md`. Start `python3.12 cutout.py "$WD"` in the background right after step 2c whenever the plan may use words behind his head or a background swap (output `subject.webm`, same frames as `tight.mp4`).
- Write `$WD\fx.json` from the beats: icons popping above his head on list words, a huge word behind his head on the key word, background swaps, full-screen takeovers (he leaves the frame and a motion scene plays while he keeps talking), counters. Format in `scripts/s06b_fx.py`; scenes and icons come from the shared motion kit (`remotion/src/motion/`, `assets/icons/`).
- Command: `python s06b_fx.py "$WD"`. Check: every effect lands on its word, 1.2 to 6 s, no overlap with a step-6 graphic, a plate or the title, cutout present when needed, behind-head and stat words are his words, takeovers at most 40% of the video.
- The storyboard (step 7) and the reviewer (steps 7 and 9) judge the effects like any other graphic.

### 7. Storyboard (check, then STOP)
- Command: `python s07_storyboard.py "$WD"`. Input: `shots.json`, `graphics.json`, `tight.mp4`. Output: `$WD\storyboard.html` (self-contained), `$WD\stills\`, `$WD\storyboard_preview.png`, `$WD\BRIEF_storyboard.md`.
- Check: one row per shot, every still exists.
- **Before showing it:** spawn a fresh subagent (Agent tool, `general-purpose`) with the prompt "Read `<path>\BRIEF_storyboard.md` and follow it." It returns a findings table and a checklist table (one row per rule in `taste-checklist.md`). Fix every real finding (re-run from the earliest affected step), then tell the user in two lines what it found and what you fixed.
- Send `storyboard.html` to the user (SendUserFile, render). **Stop here and wait for approval in chat.** Do not run step 8 until he says to.
- **When his notes arrive:** (1) write each note into `taste-checklist.md` as a new rule with his exact words, (2) scan the whole video for the same problem (self-improvement rule 4), (3) only then change `inventory.json`, `drops_manual.json` or the beats, re-run from the earliest affected step through step 7, run the storyboard check again and show it again. If a note contradicts an old rule, ask which wins.

### 7b. Opening first (10 to 15 s preview, then STOP)
- After the storyboard is approved, build only the opening: `python s08_build.py "$WD" --frames 0 450` (the first 15 s at 30 fps; if the whole video is shorter, build all of it). Use a 720p preview if the user agreed to one.
- Run the same fresh-reviewer check on the opening frames (step 9 logic, opening only), fix real findings, then send it to the user with sound and **STOP**. His notes go through self-improvement rules 2 and 4 (rule first, then scan the whole plan, then change it).
- Do not build the full video until he approves the opening and any plan changes it caused. "Keep going" about the opening counts as approval of the opening only, never of the final.

### 8. Build
- Command: `python s08_build.py "$WD"` (add `--frames 0 200` for a quick slice). Input: approved `shots.json`, `graphics.json`, `tight.mp4`. Output: `$WD\draft.mp4`, `$WD\props.json`.
- Remotion assembles it from `$SK\remotion\src` (copied into `video-tools\remotion\jobs\`). Captions are one word at a time (two when a word is under 0.2 s), at 0.771 of frame height in every layout, in the brand font, bold, with emphasis words on an accent pill, no fade.
- Check: draft is 1080x1920, 30 fps, has audio, and its length is within 0.1 s of `tight.mp4`.

### 9. Review (fresh subagent, before the user sees the draft)
- Command: `python s09_review_frames.py "$WD"`. Output: `$WD\review\sheet_NN.png` and `$WD\review\BRIEF.md`.
- Spawn a fresh subagent (Agent tool, `general-purpose`) whose prompt is only: "Read `<path>\review\BRIEF.md` and follow it." Do not give it the plan, `shots.json`, `graphics.json` or your reasoning. It judges the frames against the style guide, the brand rule and every numbered rule in `taste-checklist.md`, and returns a findings table plus a checklist table.
- Look at each flagged frame at full size before changing anything (gotcha G31: some flags are sampling artifacts). Fix every real finding (change inventory, triggers or assets; re-run steps 5 to 8), add each fix to `gotchas.md`, and re-run step 9 until the reviewer has no open findings, at most 3 rounds. Report anything you did not fix, with the reason.
- Check: the reviewer's last pass has no open findings on the brand rule, the face check and the caption check, and no FAIL in its checklist table.

### 10. Render and check
- Command: `python s10_final_check.py "$WD"`. Input: `draft.mp4`, `props.json`, `tight_words.json`, `tight.mp4`. Output: `$WD\final.mp4`, `$WD\final_check.json`.
- Checks, all must pass: 1080x1920 at 30 fps H.264 + AAC; loudness within 1 LU of -14 LUFS and true peak at most -1.0 dBTP; captions are exactly the user's words and match a fresh Whisper pass on the final audio (word error rate at most 10%); his face is still visible in the final wherever it was in the tight cut and no graphic zone reaches the face; palette, banned words, study-creator strings and logo timing are clean.
- Then send `final.mp4` to the user (SendUserFile, render) with a short report: what the checks showed, what the reviewer found and what you fixed, what you did not fix.

### 10b. Final approval (hard gate)
- Name the exact file and version you are asking about (for example `final.mp4`, 38.2 s, built 14:05) and ask: "Is this the final one?"
- Only a clear yes about that specific file counts. Then copy that exact version to the project's outputs folder (Rule 44), record it in `$WD\approved.json` `{"file": "...", "date": "...", "by": "the user"}`, update the notes, and only then run the cleanup (step 12).
- If he asks for any change after the yes, it is a new version and needs a new yes.

### 11. Learn
- Show the user the rules added to `taste-checklist.md` this time (every rule tagged with this video's name) and the gotchas added to `gotchas.md`, each as one line (number, title, his words or the fix).
- **Tag every new rule as GLOBAL or STYLE-ONLY or THIS-VIDEO-ONLY** (Rule 50). Global means every video from now on. Style-only means only that brand profile or look (for example strict brand profiles). This-video-only means a special request for this one cut: write it in `$WD\notes.md`, not in the checklist. If you cannot tell which, ask him in one line. One video's odd request never becomes a rule for every video.
- Check: every note he gave on this video is in the checklist, every break you fixed is in the gotchas, and nothing was deleted. If you deleted or changed an old rule without his answer, undo it.

### 12. Safe cleanup (only after step 10b)
- During the work, list every temporary file you can fully recreate (stills, review sheets, `subject.webm`, slice renders, extra drafts, generated music cache copies) in `$WD\cleanup.json` `{"safe_to_recreate": ["path", ...]}`. Anything not on the list is left alone.
- Command: `python s12_cleanup.py "$WD"` shows the dry-run plan. Add `--apply` to MOVE the listed files into `$WD\_cleanup_archive\` (the guard hook blocks `rm`; the user deletes the archive himself).
- Never touch: the raw video, `final.mp4` and the approved copy, `approved.json`, editable work (`inventory.json`, `beats.json`, `shots.json`, `graphics.json`, `fx.json`, `props.json`, `brand.json`, `music.json`), approved style examples, the tools, the Whisper model, the learning notes. Unknown files stay.
- Check: the dry run lists only files on the safe list; the approved final still plays after `--apply`.

## Filmed in sections (Rule 34)

If the user films one clip per script line (or retries lines), run `python s02s_sections.py "$WD" --script "<script.txt>" <clip1> <clip2> ...` instead of steps 1 and 2a. It intakes and transcribes every clip, picks the best take of each line (most words, latest try on a tie), cuts each in real silence and joins them in script order into `source_norm.mp4` + `words.json` with `hard_breaks`. Then carry on with step 2c (or F2 below). Every join becomes a picture cut.

## Cuts never clip words (Rule 25)

`s02b_tightcut.py` carries word edges through unbroken voice (Whisper ends words early, G45), puts every cut in the quietest moment of the pause, and fails if a join is louder than room noise + 9 dB. `s05_layout_plan.py` puts every picture cut in a quiet gap between words and forces a cut with a zoom change on every audio join (G46). Never loosen these limits: keep the pause, or drop the whole word.

## Music (Rules 32 and 46)

Write `$WD\music.json` before step 10, either `{"generate": "<genre, BPM, instruments, mood>", "full": true, "gain_db": -20}` (Google Lyria, made once and cached in `$WD\music\` by `scripts/lyria.py`, about $0.08 for a full track, $0.04 for a 30 s clip) or `{"file": "<track>", "licence": "<where it is from and what it allows>", "gain_db": -20}`. Step 10 loops it to length, fades it in and out, ducks it under the voice and normalizes the mix to -14 LUFS. No licence, no music.

## Notes

- Hand-off gates, in order: storyboard approved (step 7), then opening approved (step 7b), then full build (step 8), then a specific final approval (step 10b). A preview, a "looks good so far" or a "keep going" is never the final approval.
- If Whisper mishears a name or product, correct the word in `words.json` before step 2c (this fixes spelling of what he said, it never changes his words).
- If `s08_build.py` fails inside Remotion, read the tail it prints. The usual causes are a missing asset file or an unsupported image format (convert to PNG).
- Banned on-screen words: add them to `rules.md` under "Banned words"; every script reads that list.
