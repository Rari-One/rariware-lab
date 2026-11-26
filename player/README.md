# RariWare Lab Player

Watch a swallow lift off carbon paper, hear a moon cross a galaxy, or open an experiment of your own. Lab Player is a portable application for Windows x64 and Linux x64. Each artwork brings its own pictures, timing and optional music in a single `.rwl` file. Everything plays offline.

## Open the player

Download the archive for your operating system and `SHA256SUMS.txt` from the same [official Lab Player release](https://github.com/Rari-One/rariware-lab/releases). Each archive contains the player and four artworks. The source archives are for building from code.

### Windows x64

1. Download `LabPlayer-Showcase-Collection-windows-x64.zip`. In PowerShell, open the download folder and run `Get-FileHash .\LabPlayer-Showcase-Collection-windows-x64.zip -Algorithm SHA256`. Compare the full hash with the Windows entry in `SHA256SUMS.txt`. Continue when they match.
2. In File Explorer, choose **Extract All**. Open the extracted collection folder and double-click **LabPlayer.exe**. Keep the executable and its `artworks/` folder together.
3. The executable is unsigned. If Windows SmartScreen displays an unfamiliar-publisher warning, **More info** shows the program details. Choose **Run anyway** only if you trust the download.

### Linux x64

Download `LabPlayer-Showcase-Collection-linux-x64.tar.gz`. From a terminal in the download folder, run:

```sh
sha256sum --ignore-missing -c SHA256SUMS.txt
```

Look for `LabPlayer-Showcase-Collection-linux-x64.tar.gz: OK` before extracting and launching:

```sh
tar -xzf LabPlayer-Showcase-Collection-linux-x64.tar.gz
cd LabPlayer-Showcase-Collection-linux-x64
./lab-player
```

The archive preserves execute permission. If a file manager loses it while copying the folder, run `chmod +x lab-player` in the extracted folder. The portable player can launch directly. The optional desktop entry and application icons are in `branding/` for desktop packagers.

**Linux compatibility.** Use a glibc-based x86-64 desktop with OpenGL graphics and an X11 display. XWayland is expected to provide the display on Wayland desktops. For sound, use PulseAudio or PipeWire with PulseAudio compatibility. Earlier Linux playback tests used Ubuntu 24.04 with a virtual X11 display and a PulseAudio virtual output. Physical desktop launcher icons, PipeWire playback and Wayland configurations still need direct testing. ALSA-only audio is unverified. The executable imports unversioned glibc symbols. A minimum working glibc version has not been established.

## Follow a drawing back to its source

Choose **Carbon Paper**. A swallow lifts off a blue impression as a cut travels across the paper. Press **Space** to pause. Click the second tick on the timeline. The picture jumps to frame 8, and **Follow** highlights line 150 of `source/carbon.go`. At 20 frames per second, that frame begins 0.4 seconds into the piece. Press **period** to advance one frame or **comma** to step back.

Each tick marks a passage the artist chose. Drag the timeline to preview frames in silence. Release it to resume if the piece was playing. Follow starts on for works with markers. Scroll the source or click **File** to read at your own pace. Click **Follow** to return to the passage for the current frame.

## Find your way around

- Click a title, or press `[` and `]` to move between works. **F** fills the window with the artwork. The exit hint fades as you watch. Move the pointer or use a playback key to reveal it. **F** or **Escape** returns to the regular view. **R** restarts the piece.
- Drag the library’s right edge to give long titles more room. Drag it to the left edge to hide the library. **Tab** opens or closes it. Drag the divider below the timeline to give the source more room.
- Open **Controls** for the keyboard shortcuts, timeline gestures and file drop. **F1** also opens it in Art view. **T** switches between the Lab and IDE themes. IDE gives the viewer a black background and changes the source text colors.
- For pieces with sound, use your system’s sound output and volume controls.

## Open another artwork

Drop a local `.rwl` onto the window. The player reads the file where you dropped it from and remembers its path until you quit. If you select that title again, the player reads the same file again. To keep a work in the library across launches, copy it into `artworks/` beside the executable. The player scans that folder in filename order at startup. The showcase contains the four works listed below.

You can also open a file from PowerShell. After building from the repository, try this from the `player/` folder:

```powershell
.\LabPlayer.exe ..\long-way-round\long-way-round.rwl
```

On Linux, the equivalent command from that folder is `./lab-player ../long-way-round/long-way-round.rwl`.

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

For a Windows x64 build, install the Go toolchain specified in [go.mod](go.mod). The player uses Ebitengine v2.10.6 for the window, graphics, input and audio. The Go image library (golang.org/x/image v0.48.0) loads the font and draws text. Go downloads missing modules into its cache. For the Windows executable icon, install the build tool once with `go install github.com/akavel/rsrc@v0.10.2` and put the Go binary directory on your PATH. The generation step writes `player/icon_windows_amd64.syso`, which Go links into the executable. From the repository root, run these commands in Windows PowerShell to test the player and write the executable to player/LabPlayer.exe.

```powershell
cd player
$env:GOOS = "windows"
$env:GOARCH = "amd64"
$env:CGO_ENABLED = "0"
go generate .
go test .
go build -trimpath -ldflags "-s -w -H windowsgui" -o LabPlayer.exe .
.\LabPlayer.exe
```

On a Linux x64 build machine with the same Go toolchain, run these commands from the repository root:

```sh
cd player
CGO_ENABLED=0 go test ./...
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o lab-player .
./lab-player
```

For a portable distribution, put the executable, `artworks/`, the [dependency notices](notices/), the [MIT license](../LICENSE) and the platform’s branding assets in one collection folder. Use a ZIP for Windows and a gzip-compressed tar archive for Linux, with the Linux executable set to mode 0755.

The [identity assets](identity/README.md) include the SVG masters, Linux desktop icon and instructions for regenerating the artwork.

Discuss changes to the player with the maintainer before submitting them. In a pull request, explain what changed, how to try it, what the viewer should see or hear, and what you tested. For playback changes, try both a silent piece and a piece with sound. The [contribution guide](../CONTRIBUTING.md) describes review and distribution permissions.

Viewing controls, library and themes

Made with: GPT-6 (OpenAI), using Codex
