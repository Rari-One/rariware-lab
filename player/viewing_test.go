package main

import (
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func withLibrary(t *testing.T) {
	t.Helper()
	old := pieces
	pieces = nil
	t.Cleanup(func() { pieces = old })
}

func TestLibraryCardLayout(t *testing.T) {
	withLibrary(t)
	for i := 0; i < 16; i++ {
		pieces = append(pieces, piece{name: "The Twenty-Fifth Window"})
	}
	g := player{view: view{nav: true}}
	g.Layout(640, 420)
	g.resizeLibrary(128)
	g.layoutCards()
	narrow := g.cards[0]
	if strings.Join(narrow.lines, "") != "TheTwenty-FifthWindow" || len(narrow.lines) < 3 {
		t.Fatal(narrow.lines)
	}
	g.revealCard(15)
	last := g.cards[15]
	if last.top+last.height-g.offset > g.h-cardsTop {
		t.Fatal("last card outside viewport")
	}
	g.resizeLibrary(900)
	g.layoutCards()
	if g.left() != 280 || len(g.cards[0].lines) != 1 || g.timeline().right <= g.timeline().left {
		t.Fatal("wide layout", g.left(), g.cards[0])
	}
	g.resizeLibrary(20)
	if g.left() != 0 {
		t.Fatal("library did not collapse")
	}
	g.nav = true
	if g.left() != 280 {
		t.Fatal("library lost width")
	}
}

func TestTimeline(t *testing.T) {
	withLibrary(t)
	g := player{view: view{paused: true, w: 640, h: 420, nav: true}}
	pieces = []piece{{count: 896, fps: 14, markers: []marker{{Frame: 301}}}}
	p := pieces[0]
	bar := g.timeline()
	x := bar.frameX(301, p.count)
	for _, tt := range []struct {
		x           int
		held, first bool
		want        int
	}{
		{x, true, true, 301}, {x, true, false, 301}, {bar.left - 20, true, false, 0}, {bar.right + 20, false, false, 895},
	} {
		if err := g.updateScrub(tt.x, tt.held, tt.first); err != nil || g.frame() != tt.want || !g.paused {
			t.Fatalf("scrub %+v: frame=%d paused=%t err=%v", tt, g.frame(), g.paused, err)
		}
	}
	g.resumeAfterScrub = true
	if err := g.updateScrub(x, false, true); err != nil || g.paused || g.scrubbing {
		t.Fatalf("playing scrub release: paused=%t err=%v", g.paused, err)
	}
	g.paused = true
	for fps := 1; fps <= 60; fps++ {
		pieces[0].fps = fps
		for n := 0; n < p.count; n++ {
			if err := g.seekFrame(n); err != nil || g.frame() != n {
				t.Fatalf("seek frame %d at %d fps: got %d, %v", n, fps, g.frame(), err)
			}
		}
	}
}

func TestLibraryMessages(t *testing.T) {
	withLibrary(t)
	dir := t.TempDir()
	check := func(path, want string, skips int) {
		t.Helper()
		g := player{}
		g.libraryDir = path
		g.skipped, g.libraryErr = discover(path)
		if !strings.Contains(g.emptyMessage(), want) || g.skipped != skips {
			t.Fatalf("%s, skipped %d", g.emptyMessage(), g.skipped)
		}
	}
	check(filepath.Join(dir, "missing"), "extract the whole archive", 0)
	check(dir, "No artworks here yet", 0)
	path := filepath.Join(dir, "invalid.rwl")
	if err := os.WriteFile(path, []byte("invalid"), 0600); err != nil {
		t.Fatal(err)
	}
	check(dir, "No playable artworks", 1)
	check(path, path, 0)
}

func TestSessionOpeningAndNavigation(t *testing.T) {
	withLibrary(t)
	dir, err := filepath.Abs("artworks")
	if err != nil {
		t.Fatal(err)
	}
	if skipped, err := discover(dir); err != nil || skipped != 0 || len(pieces) != 4 {
		t.Fatalf("showcase: %d pieces, %d skipped, %v", len(pieces), skipped, err)
	}
	g := player{view: view{w: 640, h: 420, nav: true}}
	defer g.stopTrack()
	if err := g.selectPiece(0); err != nil {
		t.Fatal(err)
	}
	g.full = true
	for _, want := range []int{3, 2, 1, 0} {
		g.moveWork(-1)
		if g.id != want || !g.full || g.follow != (len(pieces[want].markers) > 0) {
			t.Fatalf("previous work %d: %+v", want, g.status)
		}
	}
	g.moveWork(1)
	if g.id != 1 {
		t.Fatal("next work", g.status)
	}
	external, err := filepath.Abs(filepath.Join("..", "long-way-round", "long-way-round.rwl"))
	if err != nil {
		t.Fatal(err)
	}
	g.openPath(external)
	if len(pieces) != 5 || g.id != 4 || g.sound == nil || !g.follow {
		t.Fatal("open sounding work", g.status)
	}
	g.togglePause()
	m := pieces[g.id].markers[len(pieces[g.id].markers)-1]
	if err := g.seekFrame(m.Frame); err != nil {
		t.Fatal(err)
	}
	g.followMarker()
	if g.frame() != m.Frame || pieces[g.id].sources[g.file] != m.File {
		t.Fatal("seek did not follow marker")
	}
	g.sourceScroll(1)
	file, line := g.file, g.line
	if err := g.seekFrame(0); err != nil {
		t.Fatal(err)
	}
	g.followMarker()
	if g.follow || g.file != file || g.line != line {
		t.Fatal("seek moved manual source")
	}
	sound := g.sound
	g.openPath(filepath.Join(t.TempDir(), "missing.rwl"))
	if !strings.Contains(g.status, "missing.rwl") || g.sound != sound || !g.paused || g.id != 4 || len(pieces) != 5 {
		t.Fatal("failed open changed playback", g.status)
	}
	g.openPath(external)
	if len(pieces) != 5 || !g.follow || g.status != "" {
		t.Fatal("reopen", g.status)
	}
	g.openPath(pieces[0].path)
	pieces = pieces[:1]
	g.togglePause()
	g.moveWork(1)
	if !g.paused || g.id != 0 {
		t.Fatal("single work restarted")
	}
}

// Match the desktop drop contract: Ebitengine supplies the actual path on
// the directory entry. A drop need not be relative to the player directory.
type desktopEntry struct {
	fs.DirEntry
	path string
}

func (d desktopEntry) AbsPath() string { return d.path }

type desktopDrop struct {
	fs.FS
	entries []fs.DirEntry
}

func (d desktopDrop) ReadDir(string) ([]fs.DirEntry, error) { return d.entries, nil }

func TestDroppedArtwork(t *testing.T) {
	withLibrary(t)
	path, err := filepath.Abs(filepath.Join("artworks", "00-carbon-paper.rwl"))
	if err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	g := player{}
	d := desktopDrop{entries: []fs.DirEntry{desktopEntry{fs.FileInfoToDirEntry(info), path}}}
	g.openDrop(d)
	g.openDrop(d)
	if len(pieces) != 1 || pieces[0].path != path || g.tex == nil {
		t.Fatal("drop", g.status)
	}
}
