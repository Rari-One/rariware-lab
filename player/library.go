package main

import (
	"errors"
	"fmt"
	"io/fs"
	"path/filepath"
	"runtime"
	"strings"

	e "github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/text"
	"github.com/hajimehoshi/ebiten/v2/vector"
)

func (g *player) openPath(path string) {
	abs, err := filepath.Abs(path)
	if err != nil || !strings.EqualFold(filepath.Ext(path), ".rwl") {
		g.status = "Choose a .rwl artwork file: " + filepath.Base(path)
		return
	}
	for i, p := range pieces {
		if abs == p.path || runtime.GOOS == "windows" && strings.EqualFold(abs, p.path) {
			g.selectPiece(i)
			return
		}
	}
	if len(pieces) >= 128 {
		g.status = "Library is full. Could not open " + filepath.Base(path)
		return
	}
	g.loadPiece(len(pieces), abs)
}

func (g *player) openDrop(files fs.FS) {
	entries, err := fs.ReadDir(files, ".")
	if err != nil || len(entries) != 1 {
		g.status = "Drop one .rwl artwork at a time."
		return
	}
	entry := entries[0]
	path, ok := entry.(e.AbsPather)
	if !ok || entry.IsDir() {
		g.status = "Choose a .rwl artwork file: " + entry.Name()
		return
	}
	g.openPath(path.AbsPath())
}

func (g *player) moveWork(delta int) {
	if len(pieces) == 0 || len(pieces) == 1 && g.tex != nil {
		return
	}
	g.selectPiece((g.id + delta + len(pieces)) % len(pieces))
}

func (g *player) emptyMessage() string {
	switch {
	case errors.Is(g.libraryErr, fs.ErrNotExist):
		return "Couldn’t find the artworks folder beside the player. If you downloaded the showcase, extract the whole archive and open the player again. You can also drop a .rwl file here."
	case g.libraryErr != nil:
		return "Couldn’t read the artworks folder: " + g.libraryDir
	case len(pieces) > 0:
		return "Choose a work from the library or drop a .rwl file here."
	case g.skipped > 0:
		return "No playable artworks found. Drop a .rwl file here to play it."
	default:
		return "No artworks here yet. Drop a .rwl file here to play it."
	}
}

func (g *player) libraryStatus() string {
	if g.skipped == 0 {
		return g.status
	}
	return strings.TrimSpace(fmt.Sprintf("%d skipped  %s", g.skipped, g.status))
}

func (g *player) drawMessage(s *e.Image, message string, x, y, width int) {
	advance, _ := g.face.GlyphAdvance('0')
	cols := max(1, width/max(1, advance.Ceil()))
	for _, line := range wrapText(message, cols) {
		vector.DrawFilledRect(s, float32(x-2), float32(y-16), float32(len([]rune(line))*advance.Ceil()+4), 19, g.colors().background, false)
		text.Draw(s, line, g.face, x, y, g.colors().ink)
		y += 20
	}
}

func wrapText(message string, cols int) []string {
	var lines []string
	r := []rune(message)
	for len(r) > 0 {
		n := min(len(r), cols)
		if n < len(r) {
			for i := n; i > 0; i-- {
				if r[i] == ' ' {
					n = i
					break
				}
			}
		}
		lines = append(lines, string(r[:n]))
		r = r[n:]
		if len(r) > 0 && r[0] == ' ' {
			r = r[1:]
		}
	}
	return lines
}
