# RariWare Lab Player

Watch a swallow lift off carbon paper, hear a moon cross a galaxy, or open an experiment of your own. Lab Player is a portable Windows x64 application. Each artwork brings its own pictures, timing and optional music in a single `.rwl` file. Everything plays offline.

## Open the player

1. Visit the [official RariWare Lab releases](https://github.com/Rari-One/rariware-lab/releases). When a player release is available, download its Windows x64 showcase ZIP from **Assets**. The GitHub source-code ZIP contains the files for building the application.
2. To check the download, open PowerShell in your Downloads folder and run `Get-FileHash .\LabPlayer-Showcase-Collection-x64.zip -Algorithm SHA256`. Compare the result with the checksum on the release page.
3. Choose **Extract All** in File Explorer. Keep the extracted folder together and open **LabPlayer.exe**. Playback requires no installer, development tools or separate language runtime.

The executable is unsigned. Windows may display an unfamiliar-publisher warning. Download only from the official repository release and decide whether you trust the download before opening it.

## Watch and explore

Click a title in the library. **Space** pauses or resumes, **R** restarts, and **F** fills the window with the artwork. Press **Escape** to return. **Tab** collapses or opens the library. Audio uses the Windows output device and volume controls.

Drag the horizontal divider to make more room for the source. Click **File** to browse the included files. Scroll over the listing or use the arrow and Page Up / Page Down keys. Left and right arrows reveal long lines. **Follow** is available when the artist has annotated the timeline. It highlights the lines the artist chose for the current moment. Scrolling or changing files returns you to manual browsing.

The player looks in `artworks/` beside the executable on each launch. Add a compatible package there, or move one out to remove it from the library, then relaunch. Titles come from the packages and appear in filename order. Any compatible collection works, including an empty folder.

## Inside an artwork

A frame is one picture made from a rectangular grid. Each cell stores a character and its ink color. The Go player uses Ebitengine to draw Braille dots and fractional blocks directly and JetBrains Mono for ordinary text. It updates changed cells and fits the grid to the window while keeping the cell proportions. A silent piece advances with elapsed time. A sounding piece uses the position in its audio track to select the picture and source annotation. The source listing is readable text and is never executed.

## Make your first artwork

Try the [two-frame recipe and package reference](PACKAGES.md), or explore one of the Lab experiments below. Each has its own directory at the repository root with source, a README, and instructions to regenerate its playable package in `player/artworks/`.

| Piece | Material | Study |
| --- | --- | --- |
| [Carbon Paper](../carbon-paper/) | Go, silent | Eight-dot engraving and a traveling impression |
| [Umbra Choir](../umbra-choir/) | Python, stereo | A single score drives stars and ringing glass |
| [The Twenty-Fifth Window](../twenty-fifth-window/) | Python, stereo | Layered scenery and beat-driven lights |
| [Endpaper Tide](../endpaper-tide/) | JavaScript, silent | Combed ribbons of pixel color |

## Build and share

For a Windows x64 build, install the Go toolchain specified in [go.mod](go.mod). From the repository root, run these PowerShell commands. The first build downloads the Go modules.

```powershell
cd player
$env:GOARCH = "amd64"
$env:CGO_ENABLED = "0"
go test .
go build -trimpath -ldflags "-s -w -H windowsgui" -o LabPlayer.exe .
.\LabPlayer.exe
```

For a portable distribution, put the executable beside `artworks/`, the [notices](notices/) folder, and the repository [MIT license](../LICENSE). Include the packages you wish to share, then ZIP that folder's contents. Windows x64 is the supported release target; playback needs a working graphics backend and audio output for sounding pieces.

Contributions are welcome through a pull request. Give each new Lab experiment its own top-level directory alongside these four. For artwork, include the original source, regeneration instructions, its package, and the notices for any material you distribute. For a player change, explain what the viewer or author can now do and check playback with an existing silent and sounding package.
