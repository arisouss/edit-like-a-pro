# Motion rules (effects layer, Rule 42)

Read before step 6b. Distilled on 2026-10-22 from three references the user picked: ranahaani/i-hate-editing (MIT: motion, hooks, sound), tenfoldmarc/video-edit-skill (words behind the head, cut-out speaker, inserts), and the "Let Claude edit your reels" guide (hook variants). Mechanics only, no one's branding.

## What the effects layer can do (fx.json, checked by s06b_fx.py, drawn by remotion/src/FxLayer.jsx)

| kind | What happens | Use it when he says... |
|---|---|---|
| `icon_pop` | Icons (with 1-word labels) pop into the space above his head, each on its own word | a list of things, tools, steps ("building, creating and doing") |
| `behind_words` | One or two huge words appear BEHIND his head (his hair covers the bottom quarter) | the one key word of a sentence ("skills", "agents", "thirty seconds") |
| `bg_swap` | His background is replaced while he keeps talking: the brand pattern drifting, a real image (optionally scrolling up), or a full motion scene behind him | a change of topic, a "world" moment, a scroll of real work behind him |
| `takeover` | He leaves the frame; a full-screen scene plays (IconSwarm, Kinetic, IconList, Compare, StatSlam, DocFly, PhotoPunch, CTA). Voice and captions continue | a comparison, a number, a process, a list of 3+, anything with structure |
| `stat` | A number counts up above his head with an impact | he says a number that is in a real source |

`behind_words` and `bg_swap` need `subject.webm` from `cutout.py` (about 5 s of processing per 1 s of video on the Mac; run it in the background right after step 2c).

## Density (his Rule 41 and 42)

- Something new arrives at least every 3 to 4 s while he talks: a step-6 graphic, an fx, a zoom cut or a caption accent.
- Takeovers at most 40% of the video; he stays the host. Never two takeovers back to back.
- One fx at a time. Fx never overlap a step-6 graphic or a full plate (the check enforces it): move the graphic out of the inventory if the fx is better.
- Rotate the form: icons, then behind-head word, then a takeover, then a background swap. Three of the same in a row reads as a template.

## Craft

- **Land on the word.** The effect's start equals its word's start (within 0.05 s). Late reads as accidental.
- **Fast in, slow landing, never linear.** Pops overshoot slightly; anything that travels gets motion blur.
- **Zoom is emphasis, not an entrance.**
- **Hold 1.5 to 3 s**, then hand back to his face (takeovers up to 6 s if something new happens inside every 3 s).
- **Behind-head words:** at most the bottom quarter of the letters hidden by his hair; if he leans a lot in that window, use `icon_pop` or a top keyword instead.
- **Never on the face.** Icons and stats sit above the head (6% to 33% of height); captions stay where they are.
- **Text on screen is his words** (Rule 11). Takeover scenes may show numbers only from a real source he names.

## Sound (every arrival has one)

pop for an icon or word, whoosh for something sliding or a background swap, whip into a takeover, riser into impact for the one biggest number, click for a selection. Never two hits on the same frame. Sounds live in `assets/sfx` (synthesized, no licence question). The voice always wins: effects sit under his peaks.

## Hook (first 3 s)

Visual, verbal and text hooks fire together and make the same promise. First frame is his face. Something changes inside the first 1.5 s (a zoom cut, an icon, a behind-head word). Offer 3 title variants for the first 3 s when he wants to test (the guide's "hook_A, hook_B, hook_C").

## Weight, handoffs and honest review (added 2026-11-01, Rule 49)

From a motion design brief (ideas only, nothing installed). Always inside the video's brand profile: for a strict brand profile (Rule 47) no glows, no shadows on graphics and no blur or glitch transitions, so weight there comes from timing and easing alone. Shadows, blur and depth are allowed for personal and ads profiles.

- **Show the idea as an action.** A choice gets selected, a stack builds, a number changes, a panel opens to reveal something. Prefer this to an icon that only decorates.
- **Objects have weight.** A heavy panel starts slow, lands with a short settle. A paper note drifts and flutters. A small label snaps. Never the same bounce on everything. Decide how each object starts, speeds up, lands and settles.
- **Handoffs.** Carry one thing into the next moment: a word becomes the title, a line becomes a divider, a panel expands into the takeover scene, a shape becomes the next frame. Use it where it helps the story; let other moments hold. Aim for at least one handoff per 15 s in videos with takeovers. This is the answer to plain text cards.
- **Camera still, objects move.** Keep the camera steady while a graphic builds unless a reframe has a purpose.
- **Sound hits the contact.** The impact sound lands on the frame where the object lands, not where it starts. Not a sound on every word; leave quiet moments; keep speech clear.
- **Inspect the render.** Before showing a version, view fast transitions frame by frame (every 2 to 3 frames around each handoff) and check caption timing and edges. If you cannot see or hear a part, write "I could not check this part" in the report. Never claim a review you did not do.
