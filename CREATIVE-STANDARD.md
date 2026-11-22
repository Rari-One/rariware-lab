# RariWare Lab — Creative Standard

**No roadmap. Just because.**

A program that makes one sound, draws a strange shape, or does something you simply wanted to try belongs here. Choose any language, subject, style, or pace. An experiment can stand on its own, whether or not it ever appears in a gallery or player.

## Give the next person a way in

Give each experiment its own descriptively named directory at the repository root. Include the original source, the assets or scripts needed to run or regenerate it, and a short README. Tell someone opening the folder for the first time what they can expect to see, hear, or do. List any dependencies, give the commands to try it, and say where to find the result. Mention any network access, files written, or other side effects they should expect. If a seed or input matters, include it. A piece that deliberately changes on every run is welcome too.

For examples, follow a swallow from Go source to a moving print in [Carbon Paper](carbon-paper/), or see how JavaScript combs ribbons of color in [Endpaper Tide](endpaper-tide/). Two Python pieces share musical timing with their pictures: [Umbra Choir](umbra-choir/) turns notes into stars, and [The Twenty-Fifth Window](twenty-fifth-window/) lights a Christmas tree to a waltz.

## Choose how to share it

**Independent experiment.** The source, its README, and any needed assets are enough. A still, recording, or other preview can help people decide whether to try it. Gallery exports and player packages are optional.

**Website gallery.** The website displays a still or plays a silent text animation from exported data. Its submission format pairs a manifest and deterministic frame JSON with a downloadable standalone Python script. The site checks that the script reproduces the committed export byte for byte. Consult the [website gallery specification](https://github.com/Rari-One/rariware/blob/main/docs/LAB-STANDARD.md) for the schemas, UTF-8 serialization, supported characters, and limits on size, timing, and redraws. If you cannot access the website repository, ask a maintainer for the current specification. Its validator also checks for a Rari-One copyright notice. If your work carries a different notice, keep it and raise that issue with the gallery maintainer.

**Lab Player.** Go, JavaScript, Python, or another language can generate a compatible `.rwl` file. Compatibility depends on the data you export. A package supplies a grid of colored characters for each frame and can include stereo audio, browsable source, and markers that connect particular frames to source lines. The player validates packages, reads their declared data locally, and plays them offline. Source listings are displayed and never executed. See the [package specification and first-artwork example](player/PACKAGES.md).

## Credit the work

AI-assisted contributions are welcome with the same expectations for originality, rights, documentation, and safety as any other contribution. Share work you created or have permission to distribute. Keep secrets and private data out of the source, sample inputs, and exports.

Accepted original code is shared under the repository’s [MIT license](LICENSE). Preserve the applicable copyright and license notices, including contributors’ own notices. Identify third-party material such as fonts, samples, or images, and keep the credits, licenses, and permissions that travel with it.
