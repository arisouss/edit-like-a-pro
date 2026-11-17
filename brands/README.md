# Brand profiles

Each file here is one look: colors, font and an optional end logo.

- `default.json` is used when a video has no `brand.json` in its work folder.
- To use your own look, copy `default.json` to `mybrand.json`, change the values, and put `{"profile": "mybrand"}` in a file called `brand.json` in the video's work folder.
- `end_logo` is a path to a PNG shown in the last 2 seconds. Leave it `null` for no logo.
- Optional keys: `"strict": true` (square corners, no glows or shadows on graphics), `"icon_prefix": "abc-"` (only icons whose name starts with that prefix are allowed), `"photo_wash": true` (a soft accent-color wash over generic photos).
