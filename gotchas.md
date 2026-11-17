# Gotchas

Every technical problem hit while building or running this skill, as Problem, Why it happened, Fix. Read this before every edit. When something breaks and you fix it, add it here before moving on.

Format:

```
## G<number>: short title
- Problem: what went wrong
- Why it happened: the cause
- Fix: what to do, and where it lives now
```

Some numbers are missing on purpose.

---

## G1: OpenCV face detector missing
- Problem: `AttributeError: module 'cv2' has no attribute 'CascadeClassifier'`.
- Why it happened: `pip install opencv-python-headless` pulled OpenCV 5, which dropped the old Haar detector.
- Fix: install `opencv-python-headless<5` (4.x) into `video-tools\py`. Already done.

## G2: Whisper cannot open the video file
- Problem: `TypeError: open() got an unexpected keyword argument 'metadata_errors'` inside faster-whisper.
- Why it happened: the PyAV that faster-whisper uses to read files is older than the code expects.
- Fix: never pass a file path. `s02_transcribe.py` decodes audio with ffmpeg to a 16 kHz mono float32 array and passes the array.

## G3: Whisper reports 0 words on a screen recording
- Problem: transcription returned 0 words with no error.
- Why it happened: the clip had no speech (a silent screen recording).
- Fix: not a bug. `s02_transcribe.py` fails with "only N words found. Is there speech?" when under 5 words.

## G4: Whisper word ends stretch into pauses
- Problem: the tight cut saved only 2.9 s on a clip with 1 s pauses, so dead air stayed.
- Why it happened: Whisper sets each word's end close to the next word's start, so a pause looks like part of the word.
- Fix: `s02b_tightcut.py` refines every word's start and end from the audio itself (10 ms RMS, voiced above noise floor + 9 dB) before cutting. Saved 7.2 s on the same clip.

## G5: Auto repeat rule drops emphasis
- Problem: the repeated-word rule would drop the first "really" in "really really cool", changing what the user said.
- Why it happened: the rule treated every immediate repeat as a false start.
- Fix: `KEEP_REPEATS` in `s02b_tightcut.py` protects intensifiers and short words (really, very, so, no, yes, ha, hey, way, many, much, bye, go, more, again, sorry, that, had). Add words there if another emphasis repeat gets dropped.

## G6: ffmpeg 9 rejects `-filter_complex_script`
- Problem: `Unrecognized option 'filter_complex_script'`.
- Why it happened: ffmpeg 9 removed it.
- Fix: use `-/filter_complex <file>`. In `s02b_tightcut.py`.

## G7: ffmpeg `tile` with `-frames:v 10`
- Problem: `Cannot write more than one file with the same name` when cutting a frame strip.
- Why it happened: `-frames:v` counts output frames, and `tile` outputs one image for ten inputs.
- Fix: put `-frames:v 1` after the tile filter.

## G8: Layout planner cut too rarely
- Problem: median shot 4.2 s on continuous speech, failing the 1.8 to 3.6 s check.
- Why it happened: cuts were only allowed at sentence ends and pauses of 0.12 s or more, which are rare in fast speech.
- Fix: `s05_layout_plan.py` now has three strengths of cut: phrase edge, clause start (and, but, so, because, which, if, when, or, then), and any safe word edge that does not follow a function word. It picks the strongest within 0.7 s of the target.

## G9: Text graphic kinds crash the graphics plan
- Problem: `KeyError: 'width_frac'` for keyword_text, numbered_list and plate_inset.
- Why it happened: only image kinds have a width in `style.json`.
- Fix: `s06_graphics_plan.py` uses `.get("width_frac", 0.8)`.

## G10: A variable and a function shared a name
- Problem: `TypeError: '>=' not supported between 'float' and 'function'` in `s06_graphics_plan.py`.
- Why it happened: a new helper `face_top()` replaced the variable `face_top`.
- Fix: renamed the helper `face_top_at`. Check for name clashes when adding helpers inside a long `main`.

## G11: Top graphic ran into a full plate
- Problem: two cards on screen at once: a card over a full plate.
- Why it happened: graphics were timed only against their own spoken word and hold, not against plate shots.
- Fix: `s06_graphics_plan.py` ends a top graphic where a plate starts, drops one that starts inside a plate, and also ends all graphics where the end card starts.

## G12: Plate too short to read
- Problem: the plate held its asset for exactly the 1.0 s minimum.
- Why it happened: the planner ended a plate at the last phrase boundary in the window, and fast speech has few.
- Fix: `s05_layout_plan.py` ends a plate at a clause edge at or after 2.0 s (never over 5.2 s).

## G13: Keyword text hung too long and repeated the title
- Problem: "test run" stayed up 4 s and repeated title line 2 and the caption.
- Why it happened: keyword text used the same 1.2 to 4.0 s hold as cards.
- Fix: `style.json` -> `animation.keyword_hold_s` is 1.0 to 1.6 s. Keep the title text different from the keywords.

## G14: Graphic zone too close to a high face
- Problem: step 10 flagged the graphic zone reaching the face top.
- Why it happened: the zone was fixed at 6% to 33% of height, but some people sit higher in frame.
- Fix: `s06_graphics_plan.py` samples the face top while each graphic is up, applies the punch-in scale, and shortens the zone to 0.04 above it. Fails if under 0.10 of height remains.

## G15: Whole-page screenshots unreadable
- Problem: a full web page at card size shows tiny text.
- Why it happened: the card is about 0.7 of the frame width, so a 3200 px page shrinks to about 0.25.
- Fix: inventory items take `"crop": [x0, y0, x1, y1]` (fractions). `s04_inventory.py` saves the cropped copy as `asset_used`. Crop to one readable panel and end on a clean line, never through a line of text.

## G16: Captions looked grey and faded
- Problem: reviewers saw faded grey captions on beige clothing and on plates.
- Why it happened: a 2-frame fade-in at the moment the sheet sampled, white on a light shirt with a soft shadow, and muted grey text on a pale plate.
- Fix: no fade (opacity 1), heavier text shadow, ink text on plates. In `Edit.jsx`.

## G17: Logo and title hard to read on a bright ceiling
- Problem: white logo and thin title line vanished against vents and lights. A dark box behind the logo looked pasted on.
- Why it happened: white on a bright, busy background.
- Fix: a soft top gradient scrim (ink, 50% to 0%) behind the title and the end logo, a drop shadow on the logo, no box. Title line 2 is 68 px bold.

## G18: Storyboard plan column was blank
- Problem: the planned-layout picture was a gray box for head shots.
- Why it happened: the mock drew overlays but never the footage.
- Fix: `s07_storyboard.py` draws the still under the overlay and applies the planned punch-in scale about the face centre.

## G19: Storyboard loses its images when sent alone
- Problem: the HTML references `stills/` and `assets/`, which do not travel with one file.
- Why it happened: relative image paths.
- Fix: `s07_storyboard.py` embeds every image as base64. The page is one self-contained file.

## G25: Local files cannot be screenshotted in the browser pane
- Problem: `This tab shows a local file, not a web page; page tools can't act on it`.
- Why it happened: the pane treats files outside the project as static snapshots.
- Fix: screenshot with headless Edge: `msedge --headless=new --screenshot=out.png file:///...`. Then read the PNG.

## G26: A heredoc python script returned exit 107
- Problem: `python -I - <<EOF` printed nothing and exited with 107 in the Bash tool.
- Why it happened: unclear (the `-I` isolated mode with stdin on this shell).
- Fix: write analysis code to a `.py` file and run the file. Do not use `-I` for the skill scripts; they import `common.py` from their own folder.

## G27: Whisper model download warns about symlinks
- Problem: a warning that Windows needs Developer Mode for symlinks.
- Why it happened: Hugging Face caches use symlinks.
- Fix: harmless. Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` to hide it. The model downloads and works.

## G28: npm warns about esbuild's install script
- Problem: `1 package has install scripts not yet covered by allowScripts` after installing Remotion.
- Why it happened: npm 11 holds install scripts for review.
- Fix: harmless here. Remotion renders without approving it.

## G29: iPhone footage can be quiet
- Problem: raw audio measured -33 LUFS.
- Why it happened: phone mic, speaker a little back from the phone.
- Fix: intake warns; step 10 normalizes to -14 LUFS (two-pass loudnorm). For next time, film closer or use a mic.

## G30: A graphic inside the title window
- Problem: a card and the title shared the top band.
- Why it happened: the first keyword trigger fell inside the title's first seconds.
- Fix: `s06_graphics_plan.py` fails if a non-photo graphic starts inside the title window (first 5 s). Move the trigger word or use a corner photo.

## G31: Reviewer flags that are sampling artifacts
- Problem: the reviewer called a caption "faded" and a card "ghosted".
- Why it happened: review sheets sample at shot start plus 0.15 s and every 2 s, which can land inside an entrance animation, and a screenshot's own pale edge looks like a ghost against a bright ceiling.
- Fix: before changing anything, extract the frame at full size and look. Fix real problems, note artifacts.

## G32: MediaPipe 1.x needs matplotlib just to import
- Problem: `ModuleNotFoundError: No module named 'matplotlib'` when importing `mediapipe.tasks.python.vision`.
- Why it happened: its drawing helper imports matplotlib at import time, and we install MediaPipe with `--no-deps` to avoid pulling a second OpenCV.
- Fix: `track_body.py` stubs `matplotlib` and `matplotlib.pyplot` in `sys.modules` before importing MediaPipe. Drawing is never used.

## G33: Import order hides the tools folder
- Problem: `ModuleNotFoundError: No module named 'cv2'` in a new script.
- Why it happened: `import cv2` ran before `from common import ...`, and `common.py` is what adds `video-tools\py` to `sys.path`.
- Fix: in every script, import `common` first, then `cv2`, `numpy`, `mediapipe`, `faster_whisper`.

## G34: MediaPipe prints a traceback when the script exits
- Problem: `TypeError: 'NoneType' object is not callable` from `face_landmarker.py ... __del__` at the end of a run.
- Why it happened: the landmarker is cleaned up after Python has already torn down its modules.
- Fix: harmless, the output file is already written. Check the JSON, not the traceback.

## G45: Whisper ends words early, so cuts clipped them
- Problem: in the test edit the cut after "animations," landed on the "-tions" (14.7 dB over the room). Other joins sat 5 to 8 dB over it, in breath or onsets.
- Why it happened: Whisper put the word end at 21.02 s, the voice ran to 21.42 s, and the old edge refinement capped the end at Whisper's end + 0.03 s. Pads were only 0.06 and 0.10 s, with 6 ms fades.
- Fix: `s02b_tightcut.py` carries word edges through unbroken voice (floor + 8 dB, up to 0.6 s, never into the next word), cuts in the quietest moment of the pause (lead 0.04 to 0.25 s, tail 0.06 to 0.30 s), uses 12 ms fades, and fails on any join over floor + 9 dB. Same clip: loudest join 4.4 dB.

## G46: Picture cuts ignored the audio joins
- Problem: the layout planner chose its own cut times, so a join where time was removed could fall mid-shot on the same zoom. That reads as a glitch. Its cuts at word edges were rounded to frames and could land inside a word.
- Why it happened: s05 never read keep.json, and used Whisper word edges as cut times.
- Fix: `s05_layout_plan.py` makes every join a cut (with the scale change), keeps a short join shot instead of merging it away, places every other cut at the quietest point between two words (skipping spots where words run together), and fails if a join has no picture cut.

## G47: A section matched on a common word
- Problem: section 2 ("how to create ...") matched from "to" in an earlier line, so its cut fell between "how" and "to".
- Why it happened: candidate starts included any of the first three script words, and ties went to the later start.
- Fix: `s02s_sections.py` starts candidates on the section's first word, ranks by coverage, then a match that begins at the first word, then the latest try. Section edges are cut at the first real silence (`silent_edge` in `common.py`).

## G48: numpy not found on the Mac
- Problem: `ModuleNotFoundError: No module named 'numpy'` in s01 and s02.
- Why it happened: the scripts import numpy before `common.py` adds `video-tools/py` to the path. The work PC has numpy installed system-wide; the Mac does not.
- Fix: a `video-tools.pth` file in python3.12's user site-packages points at `~/video-tools/py`. Already done on the Mac.

## G49: mediapipe pulls in OpenCV 5
- Problem: two OpenCV builds (contrib 5 and headless 4) landed in one `cv2` folder.
- Why it happened: mediapipe depends on `opencv-contrib-python` with no upper limit, so it installs 5.x (see G1).
- Fix: `pip install --target py --upgrade --no-deps "opencv-contrib-python<5"`. cv2 reports 4.14 with CascadeClassifier. Already done on the Mac.

## G50: Text graphics failed the inventory check without a source
- Problem: `source must be one of [...]` on every keyword_text and numbered_list item.
- Why it happened: s04 checks `source` on every item, text kinds included.
- Fix: text made of his spoken words takes `"source": "user-supplied"`.

## G51: Finder-style folder listings unreadable as plates
- Problem: a full folder listing (names, sizes, dates) on a plate read at about 7 px at 270 px wide. The listing also showed the local path and the study-creator skill name.
- Why it happened: the crop kept every column.
- Fix: crop to the names column only (`[0.01, y0, 0.26, y1]` on a 720 px wide headless capture at 2x) and leave out any row naming the study creator.

## G52: Small cropped screenshots rendered tiny on plates
- Problem: both plate cards filled about 25 to 33% of the width and read at about 3 px at 270 px wide.
- Why it happened: `Edit.jsx` sizes plate images with maxWidth and maxHeight only, so it never enlarges a crop. A 360 px crop stays 360 px.
- Fix: `s04_inventory.py` scales plate crops up to fill the 0.86 x 0.56 plate box (Lanczos). Capture at 2x or 3x so the upscale stays sharp.

## G55: Background removal needs its own model and leaves a small halo on curly hair
- Problem: words behind the head and background swaps need the user cut out of every frame; the first test showed a faint light patch on top of his hair.
- Why: MediaPipe's 256x256 multiclass selfie model is small; the wall behind his hair is a similar brightness.
- Fix: `cutout.py` refines the matte with a guided filter, steepens it and smooths it over time. Download the model once per computer. Keep swaps short (1.2 to 3 s) and avoid them on shots where he holds something.

## G56: React error #310 when an icon popped
- Problem: the render crashed with "Minified React error #310" inside `usePop`.
- Why: a hook was called after an early `return` inside a loop, so the hook count changed between frames.
- Fix: use `popAt(frame, fps, at)` (plain function) inside loops and conditions; keep `usePop` for unconditional use only.

## G57: Words "behind the head" floated above it
- Problem: the first behind-head test put the word well above his hair.
- Why: the placement used the study creator's face position from `style.json`, not the user's.
- Fix: `s08_build.py` passes his own `face_box_median` from `intake.json`; the word's top = hair top minus 0.72 of the font size, so his hair covers the bottom quarter.

## G59: Hebrew (any non-English) clip: transcription and checks were English-only
- Problem: `s02_transcribe.py` fed an English filler prompt and let Whisper guess the language; `s04_inventory.py` and `s10_final_check.py` tokenised with `[a-z0-9']+`, so Hebrew words were invisible (the caption-equals-speech check would pass on an empty list).
- Why it happened: the skill was built on English talking heads.
- Fix: `s02_transcribe.py <wd> --lang he` (no English prompt for other languages); the language goes into `words.json`; tokenisers in s04 and s10 now include `א-ת`; s10 passes the same language to the final Whisper pass. The `small` model is weak on fast Hebrew (about a dozen words wrong in 39 s): note every spelling fix in `spelling_fixes.json` and ask the user to check them; a larger model needs his OK to download.

## G60: Roboto has no Hebrew letters
- Problem: the `default` profile font (Roboto, assets/fonts) has no glyphs for U+05D0 to U+05EA. Hebrew only shows because the browser falls back to Arial, which is an accident, not a design.
- Why it happened: Roboto's woff2 files here are Latin only.
- Fix: for Hebrew videos set a font that has Hebrew in `$WD/brand.json` (Heebo is the closest to Roboto, free on Google Fonts, needs the user's OK to download; Arial Bold on the Mac is the safe stand-in) and add its files to `assets/fonts/` with `font_files`. Check the glyph with fontTools before building.

## G61: Right-to-left text lands wrong without `direction: rtl`
- Problem: measured in headless Chrome with coloured spans: in a left-to-right container "30 פעם" shows the 30 on the LEFT and "דקות," shows the comma on the RIGHT of the word. Both are wrong for Hebrew. A flex row of words (behind-head words, icon labels, list rows) also shows the first word on the left.
- Why it happened: the base direction of the page is left-to-right, so numbers and trailing punctuation take that side.
- Fix: `Edit.jsx` applies `direction: rtl; unicode-bidi: plaintext` to captions, title, keyword text and list cards when `props.rtl` is true (`s08_build.py` sets it from `words.json` language), and uses letter-spacing 0. Multi-word text inside flex rows (kit `Words`, IconList, Compare) is NOT mirrored yet: for Hebrew use one word per line there, or add `direction: rtl` to that container first. Never render a Hebrew storyboard or draft without checking one frame for comma side and digit side.

## G62: Hebrew speech chopped by pauses fails the median shot check
- Problem: `s05_layout_plan.py` failed: median shot 1.42 s (limit 1.8 to 3.6). Even with only the audio joins as cuts, the 14 kept phrases have a median of 1.65 s.
- Why it happened: the take has 13 pauses over 0.55 s in 39 s; every join must be a picture cut (G46), and the planner also added 6 extra cuts that left 1 s slivers.
- Fix: new opt-in `--min-shot 1.8` drops extra (non-join) cuts that leave a shot under that length: 18 shots became 15 and median 1.42 became 1.73. It still misses by 0.07 s, and the limit was NOT loosened. Next time: film with shorter pauses, or ask the user for a this-video-only exception.

## G66: Cut point picked by a different measure than the join check
- Problem: `s02b_tightcut.py` failed with "cut lands on voiced sound" at 9.2 dB over the room, in a pause that was only breath and room noise (about 6 dB over). No limit was too strict; one 10 ms click sat at the chosen cut.
- Why it happened: the cut was placed at the minimum of a 30 ms average (`common.quietest`), but the check takes the loudest of 3 neighbouring frames, so a single click passed the picker and failed the check.
- Fix: `quietest_join` in `s02b_tightcut.py` ranks frames by the loudest of 3 neighbours, the same measure as the check. The limit (floor + 9 dB) is unchanged.

## G64: A picture cut fell inside a word (overlapping Whisper times in fast Hebrew)
- Problem: the cut at 5.9 s sat inside "כוח" (5.88 to 6.26 s).
- Why it happened: Whisper gave overlapping times for "אין לי כוח", so the quietest-gap search had no clean gap.
- Fix: `s05_layout_plan.py` reads an optional `$WD/cut_overrides.json` `{"move": {"5.9": 6.3}}` (never moves an audio join). Check every non-join cut against word times in Hebrew videos.

## G65: Logo-less brands lost the last 2 s of graphics, and the storyboard hid the effects layer
- Problem: a personal video still reserved a 2 s end-card window (graphics cut off, reviewer asked for a logo); `s07_storyboard.py` drew only step-6 graphics, so the top zone looked empty.
- Fix: `s06_graphics_plan.py` makes the end-card window empty when the profile has no logo; `s07_storyboard.py` now pictures fx.json (icons, background swap, behind-head word). A reviewer applying brand rules to a non-the brand video is a false finding: tell it the brand profile in the brief.

## G68: Whisper tried to download a model on the Mac
- Problem: a quick language check hung for 15 minutes with no output.
- Why it happened: my own throwaway script called `WhisperModel("small")` without the model folder, so it tried to download into `~/.cache`. The real model is in `~/video-tools/models`.
- Fix: pass `download_root="~/video-tools/models", local_files_only=True`. The skill scripts already do this through `common.py`.

## G69: A new tight cut makes subject.webm and fx word indexes stale
- Problem: cutting the closing offer shortened tight.mp4 (29.3 s to 25.3 s) and moved word times, so beats, fx start times and the cut-out video no longer matched.
- Why it happened: every file after step 2c is keyed to tight_words.json times and indexes.
- Fix: after any change to drops_manual.json or a word's spelling, re-run s02b, rewrite the beats and fx from the new tight_words.json, and re-run cutout.py (old file kept as subject_old_29s.webm, safe to recreate). The median shot is now 1.83 s, so this plan passes without the waiver.
