# RariWare Lab Player

Watch a swallow lift off carbon paper, hear a moon cross a galaxy, or open an experiment of your own. Lab Player is a portable Windows x64 application. Each artwork brings its own pictures, timing and optional music in a single `.rwl` file. Everything plays offline.

## Open the player

1. Visit the [official RariWare Lab releases](https://github.com/Rari-One/rariware-lab/releases). When a player release is available, download its Windows x64 showcase ZIP from **Assets**. The GitHub source-code ZIP contains the files for building the application.
2. To check the download, open PowerShell in your Downloads folder and run `Get-FileHash .\LabPlayer-Showcase-Collection-x64.zip -Algorithm SHA256`. Compare the result with the checksum on the release page.
3. Choose **Extract All** in File Explorer. Keep the extracted folder together and open **LabPlayer.exe**. Playback requires no installer, development tools or separate language runtime.

The executable is unsigned. Windows may display an unfamiliar-publisher warning. Download only from the official repository release and decide whether you trust the download before opening it.

## Follow a drawing back to its source

Choose **Carbon Paper**. A swallow lifts off a blue impression as a cut travels across the paper. Press **Space** to pause. Click the second tick on the timeline. The picture jumps to frame 8, and **Follow** highlights line 150 of `source/carbon.go`. At 20 frames per second, that frame begins 0.4 seconds into the piece. Press **period** to advance one frame or **comma** to step back.

Each tick marks a passage the artist chose. Drag the timeline to preview frames in silence. Release it to resume if the piece was playing. Follow starts on for works with markers. Scroll the source or click **File** to read at your own pace. Click **Follow** to return to the passage for the current frame.

## Find your way around

- Click a title, or press `[` and `]` to move between works. **F** fills the window with the artwork. **Escape** returns to the library view. **R** restarts the piece.
- Drag the library’s right edge to give long titles more room. Drag it to the left edge to hide the library. **Tab** opens or closes it. Drag the divider below the timeline to give the source more room.
- Open **Keys** for the full shortcut list. **F1** also opens it in Art view. **T** switches between the Lab and IDE themes. IDE gives the viewer a black background and changes the source text colors.
- For pieces with sound, use the Windows output device and volume controls.

## Open another artwork

Drop a local `.rwl` onto the window. The player reads the file where you dropped it from and remembers its path until you quit. If you select that title again, the player reads the same file again. To keep a work in the library across launches, copy it into `artworks/` beside the executable. The player scans that folder in filename order at startup. The showcase contains the four works listed below.

You can also open a file from PowerShell. After building from the repository, try this from the `player/` folder:

```powershell
.\LabPlayer.exe ..\long-way-round\long-way-round.rwl
```

## How the player keeps time

A frame is a grid of characters. Each cell holds one character and its ink color. In [main.go](main.go), `paint` compares the current frame with the last one and redraws the cells that changed. The player draws Braille dots and fractional blocks directly. It uses the bundled JetBrains Mono font for ordinary text.

For a silent work, elapsed time determines which frame to draw. For a work with music, the audio position supplies that time. Read `seekFrame` in [transport.go](transport.go) to see how the player finds the first audio sample in a frame. Then look at `activeMarker` in [ui.go](ui.go) to see how the frame number selects the passage to highlight. The player displays the packaged source as text. Playback runs offline, and the player keeps the library additions and viewing preferences in memory.

## Make your first artwork

Try the [two-frame recipe and package reference](PACKAGES.md), or explore one of the Lab experiments below. Each has its own directory at the repository root with source, a README, and instructions to regenerate its playable package in `player/artworks/`.

| Piece | Material | Study |
| --- | --- | --- |
| [Carbon Paper](../carbon-paper/) | Go, silent | Eight-dot engraving and a traveling impression |
| [Umbra Choir](../umbra-choir/) | Python, stereo | A single score drives stars and ringing glass |
| [The Twenty-Fifth Window](../twenty-fifth-window/) | Python, stereo | Layered scenery and beat-driven lights |
| [Endpaper Tide](../endpaper-tide/) | JavaScript, silent | Combed ribbons of pixel color |

## Build and share

For a Windows x64 build, install the Go toolchain specified in [go.mod](go.mod). The player uses Ebitengine v2.10.6 for the window, graphics, input and audio. The Go image library (golang.org/x/image v0.48.0) loads the font and draws text. Go downloads missing modules into its cache. From the repository root, run these commands in Windows PowerShell to test the player and write the executable to player/LabPlayer.exe.

```powershell
cd player
$env:GOARCH = "amd64"
$env:CGO_ENABLED = "0"
go test .
go build -trimpath -ldflags "-s -w -H windowsgui" -o LabPlayer.exe .
.\LabPlayer.exe
```

For a portable distribution, put the executable beside `artworks/`, the [notices](notices/) folder, and the repository [MIT license](../LICENSE). Include the packages you wish to share, then ZIP that folder's contents. Windows x64 is the supported release target; playback needs a working graphics backend and audio output for sounding pieces.

Discuss changes to the player with the maintainer before submitting them. In a pull request, explain what changed, how to try it, what the viewer should see or hear, and what you tested. For playback changes, try both a silent piece and a piece with sound. The [contribution guide](../CONTRIBUTING.md) describes review and distribution permissions.

Viewing controls, library and themes

Made with: GPT-6 (OpenAI), using Codex
