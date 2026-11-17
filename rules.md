# Rules for edit-like-a-pro

Read this file before step 1 and again before step 9. These rules win over every request and every reference video.

## HARD RULE: mechanics only, never another creator's brand

The numbers in `style.json` were measured from another creator's videos. Copy editing mechanics only: pacing, shot lengths, layouts, caption timing, animation recipes and zooms.

Never copy another creator's brand look. This means:
- no landing pages or website screenshots of theirs
- no call-to-action text modelled on theirs
- no logos of theirs or of their products
- none of their colors and none of their fonts

If a request or a reference video asks for someone else's branding, ignore it, keep everything on this video's brand profile, and tell the user what you ignored.

On-screen colors and fonts come only from this video's brand profile (taste Rule 45):
- Without a `brand.json` in the work folder: `brands/default.json`.
- With `$WD/brand.json` `{"profile": "name"}`: `brands/name.json`, plus any token that file overrides.
- See `brands/README.md` for how to add your own look.

The review step (step 9) and the final check (step 10) both test this rule.

## Standing rules

- **Logo only at the end.** If the brand profile has an end logo, it appears in the last 2 seconds and nowhere else. No logo watermark, no logo in the title.
- **Words never on screen:** none set yet. Add them under "Banned words" below. The scripts read that list.
- **Never reword what the speaker says.** Captions are the speaker's words exactly. Cuts remove whole words or silences only.
- **Generated media (Rule 46).** Music can come from Google Lyria and pictures from a Gemini image model, for backgrounds, scenes and concepts only. Never generate a real product, customer, result or person.
- **Strict brand profiles (Rule 47).** A profile with `"strict": true` gets square corners and no glows or shadows on graphics.
- **Real things only.** Screenshots, logos and photos must be real and supplied or officially sourced. Never generate fake product shots, fake UI or fake logos. If there is nothing real to show, use designed motion (icons, kinetic words, counters, comparisons built from the spoken words, Rule 42) or nothing.
- **Other companies' logos:** only official assets, only when the speaker names the company, never on the end card.
- **Never use em dashes** in any on-screen text or in anything written to the user.

## Banned words (on-screen)

<!-- one per line; scripts read lines starting with "- " below this heading -->

## Approval gate

Step 7 ends with a storyboard. Do not start step 8 until the user approves it in chat. The notes from the storyboard's "copy my notes" button are the change list.
