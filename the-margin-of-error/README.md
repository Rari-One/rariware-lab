# The Margin of Error

A sheet of graph paper folds one square out of register. Follow the red cross as it becomes a bird’s eye. The crooked wing beats a little late; in the glide you can hear the space between the strokes.

[Play the standalone package](the-margin-of-error.rwl) by copying it to the Lab Player’s artworks/ directory and reopening the player. The 72 × 32 drawing loops after 20 seconds at 15 FPS. Seven optional markers connect the paper, mesh and soundtrack to the [Go source](margin.go).

## Regenerate

From this directory, with Go (tested on 1.27.4):

```sh
go run margin.go
```

The generator uses the Go standard library. It reads margin.go and NOTICE.txt locally and replaces the-margin-of-error.rwl in the current directory. All facets, registration marks and stereo samples are generated offline. Look for the displacement of 0.15 in the short wing: it equals one period of the printed grid. The second stroke in the score arrives 0.16 seconds late.

Credit: RariWare Lab, created with OpenAI Codex. The original source is contributed under the [repository MIT license](../LICENSE). No external artwork, fonts or recordings are included. The package includes its [notice](NOTICE.txt). This is an independent Lab contribution.
