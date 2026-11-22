# Working on Lab Player

Use [PACKAGES.md](PACKAGES.md) for the version 1 byte layout, limits and marker semantics. Keep it in step with the loader in packages.go. Frames are row-major five-byte cells. Optional UTF-8 source listings, timed source annotations and one bounded PCM track are data.

Preserve existing silent packages. Playback stays offline and portable, with no telemetry. Source is displayed only. Keep package paths relative, validate declared sizes before allocation, and read known members directly. Changes to trusted capabilities or resource limits require explicit discussion and documentation.

Use original or appropriately licensed code, art, audio and fonts. Retain required notices. The examples illustrate techniques; contributors choose their own languages and subjects.
