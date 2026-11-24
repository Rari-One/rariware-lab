# RariWare Lab — Creative Standard

**No roadmap. Just because.**

A program that makes one sound, draws a strange shape, or does something you simply wanted to try belongs here. Choose any language, subject, style, or pace. An experiment can stand on its own, whether or not it ever appears in a gallery or player.

## Give the next person a way in

Give each experiment its own descriptively named directory at the repository root. Include the original source, the assets or scripts needed to run or regenerate it, and a short README. Tell someone opening the folder for the first time what they can expect to see, hear, or do. List any dependencies, give the commands to try it, and say where to find the result. Mention any network access, files written, or other side effects they should expect. If a seed or input matters, include it. A piece that deliberately changes on every run is welcome too.

For examples, follow a swallow from Go source to a moving print in [Carbon Paper](carbon-paper/), or see how JavaScript combs ribbons of color in [Endpaper Tide](endpaper-tide/). Two Python pieces share musical timing with their pictures: [Umbra Choir](umbra-choir/) turns notes into stars, and [The Twenty-Fifth Window](twenty-fifth-window/) lights a Christmas tree to a waltz.

## Choose how to share it

**Independent experiment.** The source, its README, and any needed assets are enough. A still, recording, or other preview can help people decide whether to try it. Gallery exports and player packages are optional.

**Website gallery.** RariWare.com presents selected Lab experiments as a public exhibition. The website may display still artwork, silent animation, or supported rich animation with optional sound. The website player is a smaller exhibition experience, not a replacement for the standalone Lab Player.

If you would like your experiment considered for exhibition, provide:

- The original source and a README explaining how to run or reproduce the work.
- A representative still, recording, or other accessible preview.
- The intended visual dimensions, frame rate, duration, and looping behavior, where applicable.
- A description of any audio, external assets, dependencies, and expected resource requirements.
- Creator credit, copyright and license information, including any third-party material and relevant permissions.

A compatible `.rwl` package may help demonstrate a richer animation, but it is not required for every experiment. The [Lab Player package specification](player/PACKAGES.md) describes that format.

**Website compatibility and exhibition are separate decisions.** The website has its own supported formats, rendering capabilities, performance budgets, accessibility requirements, and security restrictions. These may differ from the standalone player and change as the exhibition develops.

Meeting these candidate guidelines does not guarantee that an experiment will work on the website, qualify for conversion, be selected for exhibition, or be published. A repository contribution or accepted pull request is not website publication approval.

Maintainers evaluate exhibition candidates individually and may request additional information or a different export. Publication requires separate approval and appropriate rights for the intended website use. Experiments remain welcome in the Lab even if they are never exhibited.

**Lab Player.** Go, JavaScript, Python, or another language can generate a compatible `.rwl` file. Compatibility depends on the data you export. A package supplies a grid of colored characters for each frame and can include stereo audio, browsable source, and markers that connect particular frames to source lines. The player validates packages, reads their declared data locally, and plays them offline. Source listings are displayed and never executed. See the [package specification and first-artwork example](player/PACKAGES.md).

## Bringing your work to the Lab

AI-assisted experiments are welcome. When you’re ready to share, the [contribution guide](CONTRIBUTING.md) covers submitting a piece, choosing a public credit, and permissions for official publication.
