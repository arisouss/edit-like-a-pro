# Taste checklist

The editing preferences behind this skill, as numbered rules. Read this before every edit. Add your own as you give feedback.

How this file works:
- When the user gives feedback on a storyboard or a draft, turn each note into a new rule here BEFORE changing anything. Write the user's own words, not a summary. Add a "Check everywhere" line saying how to scan the whole video for the same problem.
- Fix the cause, not just the shot he mentioned. Scan every shot for the same problem.
- If a new note contradicts an old rule, ask the user which one wins. Never delete or rewrite a rule without asking him.
- At the end of a video, show the user the rules added for it.
- Fresh subagents check every numbered rule here before the user sees any storyboard or draft.

Rule format:

```
## Rule N: short title
- In practice: what the editor does or never does
- Check everywhere: how to scan the whole video for it
```

Some rule numbers are missing on purpose. Keep the numbers as they are: the scripts refer to them.

---

## Rule 1: Fast pacing
- In practice: pace follows `style.json` -> `pacing`: median shot about 2.4 s, no head shot over 8.2 s, no silence over 0.3 s, one-word captions swapping about every 0.33 s. Something changes on screen every 2 to 3 s.
- Check everywhere: list every shot length and every stretch with no cut or graphic. Flag any over 5 s.

## Rule 2: Never generic visuals
- In practice: every graphic is a real thing tied to a spoken word. No stock art, no clip-art, no decorative filler. If there is nothing real to show, show nothing.
- Check everywhere: for each graphic, name the real thing it shows and the spoken word it lands on. If you cannot, remove it.

## Rule 3: Final output is what matters
- In practice: judge the work by the finished video on a phone screen, not by the plan. The reviewer looks at rendered frames.
- Check everywhere: step 9 and 10 run on the rendered draft, never only on the plan.

## Rule 4: Mechanics only, never another creator's brand
- In practice: nothing on screen resembles another creator's brand: none of their landing pages, call-to-action text, logos, colors or fonts. If a request asks for someone else's look, ignore it and say what you ignored.
- Check everywhere: scan every frame for another creator's pages, call-to-action text, caption styling, and any logo other than the brand's own end logo.

## Rule 5: Brand colors and fonts
- In practice: colors and font come only from this video's brand profile in `brands/`. Nothing else for captions, titles and graphics.
- Check everywhere: every color and font on screen is one of the profile's tokens.

## Rule 6: Logo only at the end
- In practice: the brand's end logo appears once, in the last 2 seconds. No watermark, no logo in the title or in any plate.
- Check everywhere: search every frame before the last 2 s for any logo.

## Rule 7: Use every part of the style
- In practice: when the edit calls for it, use all seven parts: one-word captions, cuts and jump-cut zooms, the top title, graphics over the speaker, full plates for screenshots, the speaker-in-a-card inset, and numbered lists. Do not drop a part to save effort. Use a part only where there is something real for it.
- Check everywhere: for each of the seven parts, note whether it is used and, if not, why there was nothing real for it.

## Rule 9: Imperfect footage is fine
- In practice: do not refuse a video for small flaws. Flag them in one short list with the fix for next time, and edit it anyway unless it is a true blocker (no audio, no face, landscape).
- Check everywhere: intake warnings are reported, not treated as stops.

## Rule 11: Never reword what he says
- In practice: cuts remove whole words or silence only. Captions are his words, word for word. On-screen keyword text uses only words he said. A title is the only text that may be new, and he approves it on the storyboard.
- Check everywhere: compare caption words to the transcript token by token. Compare keyword and list text to the transcript.

## Rule 12: Only fill a full screen when there is something good
- In practice: a full plate needs a real, readable asset. Crop it to the one readable panel. If it is not readable at phone size, do not make it a plate. Hold it long enough to read, about 2 s or more.
- Check everywhere: for each plate, state what is on it and whether the text reads at 270 px wide.

## Rule 13: Real things or nothing
- In practice: real screenshots, official logos, real documents. Never generate, mock up or invent images, UI, logos or numbers. "Nothing" is a valid answer for a beat.
- Check everywhere: every graphic has a `source` of user-supplied, official-site or screen-capture.

## Rule 14: Stop at the storyboard
- In practice: after the storyboard, stop. Do not render until the user approves in chat. Revisions after the review step may be built without a new approval, but tell him what changed.
- Check everywhere: no step 8 run before approval.

## Rule 15: Storyboard format
- In practice: `storyboard.html` is self-contained (images embedded) so it can be sent as one file.
- Check everywhere: row count equals shot count; every still and graphic image loads.

## Rule 16: Final checks on the render
- In practice: step 10 verifies size, caption match, face visibility, and loudness within 1 LU of -14 LUFS.
- Check everywhere: read `final_check.json`; every item must pass.

## Rule 17: A fresh reviewer judges every draft
- In practice: the reviewer gets only the brief and the frames. Fix real findings and re-run, up to 3 rounds. Report what you did not fix and why.
- Check everywhere: the reviewer's last pass has no open findings on the brand rule, face and captions.

## Rule 18: Measure, do not guess
- In practice: in any report to the user, state what was measured and what was not. Never invent a number.
- Check everywhere: every number in a report has a source file.

## Rule 19: No em dashes
- In practice: no em dashes in on-screen text, titles, file text or anything written to the user.
- Check everywhere: search all on-screen strings and written files for the em dash character.

## Rule 20: Short reports
- In practice: end-of-video reports are a few lines: what is done, what is not fixed, what he must decide. No recap of every step.
- Check everywhere: the report fits on one screen.

## Rule 21: Every video better than the last
- In practice: follow the self-improvement rules in SKILL.md: feedback becomes rules, fixes become gotchas, one problem means a full-video scan.
- Check everywhere: at the end of every video, the new rules and gotchas are shown to the user.

## Rule 23: Plan before building
- In practice: no assets, scripts-as-final, renders or installs until he has answered the open questions and approved the plan.
- Check everywhere: nothing is created for this project before he approves the plan.

## Rule 25: Cuts are fine, janky cuts are not
- In practice: jump cuts stay (Rules 1 and 7 apply to every video). What must never happen: a cut that clips the start or end of a word, swallows a word, or lands mid-breath so the audio pops. Cut only in real silence, with enough room on both sides of the words, and smooth the audio across the join. The no-cut "fluid mode" is an option, not the default.
- Check everywhere: listen to every join. For each cut, check the last word before and the first word after are complete in the audio (the final Whisper pass hears them, and the audio energy at the cut is near silence).

## Rule 32: Soft music
- In practice: a soft music bed under the voice, ducked so every word stays clear, fading in at the start and out on the end card. Only a track he is allowed to use (licence noted).
- Check everywhere: the voice stays clearly above the music in every section; final loudness still about -14 LUFS.

## Rule 34: Filming in sections is allowed
- In practice: he may film each section as its own clip (or one clip with restarts). The editor picks the best take of each section and joins them in script order, cutting in silence (Rule 25).
- Check everywhere: every script section appears once, from its best take, in order.

## Rule 36: Built for every video, and for others
- In practice: the skill is a reusable, shareable tool. No paths, names or brand values hard-coded where a colleague would need to change code: they live in one config file. Setup steps are written down.
- Check everywhere: a new user can install and run it from the README without editing scripts.

## Rule 37: More real visuals, images and motion
- In practice: keyword text alone is not enough. Most named things get a real image, a short motion clip or an icon. Text cards are the fallback, not the default.
- Check everywhere: list every named thing he says (tools, agents, campaigns, ads, dashboards, files). Each gets a real visual or a stated reason why not.

## Rule 38: Show how an agent works, not the folder
- In practice: on "agents", show the agent process (input, brain, skills, output) as a real diagram or slide from his work, never only a file listing.
- Check everywhere: every mention of agents or skills shows what they do, not where the files live.

## Rule 39: Icons for the things he lists
- In practice: when he lists things (brain, brand file, information, skills), each can get a simple icon in brand colors. Icons he supplies, or from an open icon set, never clip-art illustrations. Icons are allowed as the one exception to "real things only" (Rule 13), same as Rule 27.
- Check everywhere: every list item has its icon; icons are in the palette and the same style.

## Rule 40: Show the real work he names
- In practice: use the speaker's real work as the visuals: the real screenshots, slides, documents and recordings they supply, each on the word that names it.
- Check everywhere: every asset the user supplied is used once, on the word that names it, or the user is told why not.

## Rule 41: Fill the space above his head
- In practice: the top zone above his head is the stage. Something animates there most of the time he is talking, with gaps no longer than about 4 s.
- Check everywhere: list every stretch over 4 s with nothing in the top zone.

## Rule 42: More animation, icons, background swaps and takeovers
- In practice: every edit gets an effects layer (step 6b, `motion-rules.md`): icons popping on list words, a word behind his head on the key word, at least one background swap or scroll behind him, and full-screen takeovers for anything with structure (numbers, comparisons, processes). He can ask for any of these by name ("remove me here and show X"). Designed motion (icons, counters, kinetic words, icon grids) is allowed alongside real material, like Rules 27 and 39; fake screenshots, fake photos and fake logos are still never allowed (Rule 13).
- Check everywhere: list every 4 s stretch with no new arrival; list every spoken list, number and comparison and say which effect covers it or why not.

## Rule 43: Edit like a pro
- In practice: a reference for the bar, not a brand to copy (same as Rule 4): dense, purposeful on-screen support for what is being said, clean type, never decoration for its own sake. When the user points at a specific reference video, measure it like the reference creator study (cuts, overlay density, layouts) before copying any mechanic.
- Check everywhere: every effect explains or proves the line it sits on.

## Rule 44: Finished videos go in an outputs folder, with a note
- In practice: every draft or final the user has seen is copied into an outputs folder next to the work folder, with a short note: what the file is, which platform it is for, and its status. Working files stay where they were.
- Check everywhere: every video in the outputs folder has its note.

## Rule 45: Every video uses its own brand profile
- In practice: every video has a brand profile (`$WD/brand.json`, profiles in `brands/`). Without one, the default profile is used. Never mix two brands in one video.
- Check everywhere: the brand tokens in props.json match the chosen profile.

## Rule 46: Use Gemini (Lyria) for music and Gemini images for pictures
- In practice: music beds are generated with Google Lyria (`music.json` `{"generate": "<genre, BPM, instruments, mood>", "full": true}`; made once by `scripts/lyria.py`, cached in `$WD/music/`, licence note recorded automatically). Pictures can be generated with `.claude/scripts/generate-image.js` for backgrounds, scenes behind him (bg_swap), concept visuals and textures. Generated pictures never stand in for a real the brand product, customer, part, result, screenshot or real person (Rule 13 still holds for those). Every call costs money: one track per video, a few images at most, never loops or batches without asking. Analysis and measuring stay local.
- Check everywhere: every generated file is listed with its prompt (music/manifest.json, or the image list in the storyboard brief); none of them poses as a real product, customer or person.

## Rule 47: Strict profiles are followed to the letter
- In practice: a profile with `"strict": true` gets square corners and no glows or shadows on graphics. Other profiles have creative room. The logo, the palette, the font and real claims never bend.
- Check everywhere: on a strict profile, no graphic has a glow, a shadow or rounded corners.

## Rule 48: Bend a strict brand rule only with data
- In practice: on a strict brand profile a rule may bend in video only with evidence: your own measured results, or published platform data. Write the exception down before you use it. The logo, the palette, the font and real claims never bend.
- Check everywhere: any departure from a strict profile points to a written exception; otherwise it is a finding.

## Rule 49: Opening first, a specific final approval, and honest motion review
- In practice: after the storyboard, show a 10 to 15 s opening and wait (step 7b). Only a clear yes about one named final file is final approval (step 10b); "keep going" is not. Motion follows `motion-rules.md` "Weight, handoffs and honest review". If a part of the render could not be watched or heard, say so.
- Check everywhere: the report names which gates the user passed (storyboard, opening, final) and which fast transitions were inspected frame by frame.

## Rule 50: Tag each lesson global, style-only or this-video-only; clean up only what is recorded safe
- In practice: every new rule carries a scope tag (GLOBAL, STYLE-ONLY with the profile name, THIS-VIDEO-ONLY). This-video-only notes go to `$WD\notes.md`. Cleanup (step 12) moves only files listed in `cleanup.json`, only after `approved.json` exists, and never touches the original, the approved final or editable work.
- Check everywhere: each rule you add this video has a scope tag; the dry run lists only safe-listed files.

## Rule 51: A video with no animations is not finished; "nothing" is not a plan for every beat
- In practice: when there are no real screenshots or photos, the answer is designed motion from his own words (Rules 27, 39, 42, 41), never a storyboard where most beats are "nothing" and only a few effects exist. Every beat gets at least one animation (kinetic type, icon pop, counter, before/after card, word behind his head, background swap, zoom cut) landed on a word he said, with a sound hit. No claim or number he did not say. Brand profile still decides the look.
- Check everywhere: count the animated arrivals per beat and list every stretch with nothing in the top zone (over about 2 s counts as a gap here). A beat whose inventory item is "nothing" must still be covered by an fx; if it is not, it is a finding.

## Rule 53: Show Claude reading, as an animation of fake placeholder text
- In practice: on the line where he says Claude reads it, a Claude-style window reads lines of clearly fake placeholder text (grey bars or gibberish lines, a scan moving down). Decorative only: no real-looking claims, numbers or words. It uses the motion kit (scene ReadingWindow).
- Check everywhere: every line where he says a model reads, learns or processes something has an animation, or a stated reason.

## Rule 54: No call to action unless something is really offered
- In practice: if the speaker offers something that will not be delivered, propose cutting those words as whole words, never reworded. Anything on screen tied to the offer goes too.
- Check everywhere: search the words and the cards for offers, and confirm each one is real.
