# edit-like-a-pro

A Claude Code skill that edits a raw talking-head video (iPhone or any vertical clip) into a polished short-form video. It transcribes, cuts in real silence, plans shots and graphics, shows you a storyboard for approval, renders with Remotion, then checks the result with a fresh reviewer.

Made by @itsarisouss, with Claude. Questions or ideas: itsarisouss@gmail.com

## What it does

- Tight cut: removes silences and false starts. It never rewords what you say.
- One-word captions, timed to your voice.
- Jump-cut zooms and layouts, with pacing numbers measured from top-performing Shorts.
- Graphics that land on the spoken word, plus an effects layer: icons, words behind your head, background swaps, counters and sound design.
- Your own brand look, from one small file in `brands/`.
- A storyboard you approve before anything renders.
- It learns: your feedback becomes numbered rules in `taste-checklist.md`, so each video comes out closer to your taste.

## What is in here

| File or folder | What it is |
|---|---|
| `SKILL.md` | The procedure Claude follows, step by step |
| `rules.md`, `taste-checklist.md`, `gotchas.md` | The hard rules, the numbered preferences, and every problem hit and fixed. Claude reads all three before every edit |
| `style.json` | The measured pacing and layout numbers |
| `brands/` | Brand profiles: colors, font, optional end logo |
| `scripts/` | One script per step |
| `remotion/src/` | The video templates |
| `assets/` | Roboto fonts, Lucide icons and synthesized sound effects |

## Set up (once per computer)

You need Claude Code, Python 3.12, Node 22 or newer, and about 20 minutes.

1. Put this folder at `~/.claude/skills/edit-like-a-pro`.
2. Make a folder called `video-tools` in your home folder (or anywhere, and set the `VIDEO_TOOLS` environment variable to it). It needs:
   - `bin/ffmpeg` and `bin/ffprobe` (from ffmpeg.org)
   - `py/` with `opencv-python-headless<5`, `faster-whisper`, `numpy`, `Pillow` and `mediapipe`, installed with `pip install --target py ...`
   - `models/mediapipe/` with `selfie_multiclass_256x256.tflite`, `hand_landmarker.task` and `face_landmarker.task` from MediaPipe's model page. The Whisper `small` model downloads on first run
   - `remotion/` with `npm install remotion @remotion/cli @remotion/bundler @remotion/renderer react react-dom`
3. Open Claude Code and say: `edit this video`, with the path to your raw file.

The simplest way to do step 2: open Claude Code and say "Read the README of the edit-like-a-pro skill and set up the video tools folder for me. Ask before you install anything."

## Good to know

- **Remotion's licence:** free for individuals and for companies with up to 3 employees. Larger companies need Remotion's company licence.
- **Music:** bring a track you are allowed to use, and write its licence in `music.json`. The optional Lyria script needs your own Gemini API key and costs money per call.
- **Other creators:** the pacing numbers were measured from public videos. Nothing of any other creator's branding or footage is in this repo, and the skill is told never to copy it.

## Licences

- This skill: MIT (see `LICENSE`).
- Roboto: Apache 2.0 (`assets/fonts/LICENSE-roboto-apache2.txt`).
- Lucide icons: ISC (`assets/icons/LICENSE.txt`).
