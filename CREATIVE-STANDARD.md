# RariWare Lab — Creative Standard

**No roadmap. Just because.**

This is a workshop for original experiments. Curiosity is a sufficient reason to make something.

## 1. Make things freely

Create text art, terminal animations, generative scenes, playful utilities, odd little programs, or something that doesn't fit a category. There are no required subjects, seasons, schedules, or product goals.

Experiment with scale, timing, color, movement, and technique. A piece does not have to be suitable for a gallery to belong here.

## 2. Make it original

Create original code and artwork. Do not copy someone else's work and present it as your own. Respect third-party licenses, credit requirements, and permissions. Do not include secrets, personal data, or material you lack the right to distribute.

## 3. Keep it understandable and runnable

Give each experiment its own descriptively named folder. Include a short README explaining what it does, how to run it, and any dependencies or unusual requirements.

Prefer straightforward, portable code when practical. Python is welcome, but a creative experiment may use other tools or libraries. If it needs network access, external services, or other side effects, disclose that clearly and avoid surprising behavior.

## 4. Keep the source with the work

Preserve the original source and any assets needed to reproduce the result. Generated previews or exports can accompany the source, but should not replace it.

For reproducible work, document any seeds, settings, or inputs needed to recreate the result. Experiments that intentionally vary between runs are welcome.

## 5. Gallery-ready work is optional

A piece intended for the RariWare Lab gallery needs a compatible, self-contained export. This is an exhibition format, **not a rule for every experiment in this repository**.

For the current text-animation format, prepare:

- One standalone Python 3.10+ script using only the standard library, with no network access, subprocesses, native-code execution, or dynamic code execution.
- A `manifest.json` describing the piece and its display settings.
- A deterministic `frames.json` exported by the script, with matching dimensions, frame count, and timing.
- A useful still frame and a plain-language description of the artwork.

The gallery-ready script should run as a terminal animation by default, support `--still` and `--still --no-color`, and emit the reproducible frames JSON with `--export`. Keep its output in UTF-8 and make it runnable without downloading extra dependencies.

### Current gallery compatibility limits

| Property | Supported range |
| --- | --- |
| Width | 40–160 columns |
| Height | 12–60 rows |
| Width-to-height ratio | 2–6 |
| Frame rate | 1–30 FPS |
| Frame count | 1–900 |
| Loop duration | Up to 60 seconds |
| Colors | 1–36 |
| Export size | Up to 3 MB uncompressed and 250 KB compressed |
| Changed cells | Average at most 25% per frame; maximum 50% in any frame, including the loop boundary |
| Redraw rate | Average at most 15,000 changed cells per second |

Gallery text uses single-width characters supported by the display font: ordinary ASCII and selected Latin, line-drawing, block, geometric, arrow, and mathematical symbols. Avoid emoji, wide characters, and control characters in gallery exports. Use lowercase `#rrggbb` colors and readable contrast against a near-black background.

The export uses `format: "rariware-lab-frames"` with `cols`, `rows`, `fps`, `loop`, `palette`, `frames`, and `colors`. Each frame is a newline-separated grid with exactly the declared width and height. Each corresponding color grid uses one base-36 palette index (`0-9`, `a-z`) per cell. The manifest uses `format: "rariware-lab-manifest"` and records `id`, `title`, `description`, `alt`, `source`, `frames`, `cols`, `rows`, `fps`, `frameCount`, `stillFrame`, `license`, `copyright`, `featured`, and `order`.

An experiment that exceeds these limits is still welcome as an independent work. Gallery inclusion is selective and may require an adapted export.

## 6. Share the work clearly

Original code is MIT-licensed under the repository [LICENSE](LICENSE). Include appropriate copyright and license notices with standalone gallery scripts. Keep attribution and license notices for permitted third-party material.

Do not imply that every experiment is an official application or supported product. Explain any limitations that matter to someone trying it.

## 7. Keep the workshop simple

Favor the experiment over process. A folder, source, and a short explanation are usually enough. No elaborate proposal, milestone, or release machinery is required.

Make something interesting. Or strange. Or beautiful. Or simply because you can.
