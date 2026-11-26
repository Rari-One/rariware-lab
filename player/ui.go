package main

import (
	e "github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/audio"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"github.com/hajimehoshi/ebiten/v2/text"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"image/color"
	"math"
	"path/filepath"
	"sort"

	"time"
)

type view struct {
	sound                                     *audio.Player
	ratio                                     float64
	dragging                                  bool
	listing                                   []styledLine
	start                                     time.Time
	nav, full, paused, follow                 bool
	file, line, column, offset, w, h, skipped int
	since                                     time.Duration
	lines                                     [][]string
	status                                    string
	libraryDir                                string
	libraryErr                                error
	scrubbing, resumeAfterScrub               bool
	scrubX                                    int
	navWidth, cardWidth, cardHeight           int
	cards                                     []libraryCard
	resizingNav, help, ide                    bool
}

func (g *player) selectPiece(i int) error {
	return g.loadPiece(i, pieces[i].path)
}

func (g *player) loadPiece(i int, path string) error {
	p, err := readPackage(path)
	if err != nil {
		g.status = "Could not open " + filepath.Base(path)
		return err
	}
	next, err := openTrack(p.pcm)
	if err != nil {
		g.status = "Audio unavailable for " + filepath.Base(path)
		return err
	}
	g.stopTrack()
	g.sound = next
	if i == len(pieces) {
		pieces = append(pieces, p.piece)
	} else {
		pieces[i] = p.piece
	}
	g.id = i
	g.cardWidth = 0
	g.revealCard(i)
	g.scrubbing = false
	g.dragging = false
	g.last = -1
	g.raw = p.raw
	g.lines = p.lines
	g.line = 0
	g.column = 0
	g.file = 0
	g.prepareListing()
	g.follow = len(p.markers) > 0
	g.paused = false
	g.since = 0
	g.start = time.Now()
	g.status = ""
	g.pixels = make([]byte, p.w*p.h*9*18*4)
	if g.tex != nil {
		g.tex.Deallocate()
	}
	g.tex = e.NewImage(p.w*9, p.h*18)
	if g.sound != nil {
		g.sound.Play()
	}
	return nil
}
func (g *player) elapsed() time.Duration {
	if g.paused {
		return g.since
	}
	if g.sound != nil {
		return g.sound.Position()
	}
	return g.since + time.Since(g.start)
}
func (g *player) frame() int {
	p := pieces[g.id]
	return int(g.elapsed()*time.Duration(p.fps)/time.Second) % p.count
}
func (g *player) activeMarker() *marker {
	m := pieces[g.id].markers
	n := g.frame()
	i := sort.Search(len(m), func(i int) bool { return m[i].Frame > n })
	if i == 0 {
		return nil
	}
	mark := m[i-1]
	if mark.EndLine > mark.Line {
		end := pieces[g.id].count
		if i < len(m) {
			end = m[i].Frame
		}
		span := end - mark.Frame
		if span > 1 {
			mark.Line += (n - mark.Frame) * (mark.EndLine - mark.Line) / (span - 1)
		}
	}
	return &mark
}
func (g *player) left() int {
	if g.nav && !g.full {
		return g.sidebarWidth()
	}
	return 0
}
func (g *player) split() int {
	ratio := g.ratio
	if ratio == 0 {
		ratio = .68
	}
	return max(120, min(g.h-108, int(float64(g.h)*ratio)))
}
func (g *player) sourceScroll(delta int) {
	if len(g.lines) == 0 {
		return
	}
	g.follow = false
	g.line = max(0, min(len(g.lines[g.file])-1, g.line+delta))
}
func (g *player) Update() error {
	x, y := e.CursorPosition()
	click := inpututil.IsMouseButtonJustPressed(e.MouseButtonLeft)
	key := inpututil.IsKeyJustPressed
	if files := e.DroppedFiles(); files != nil {
		g.openDrop(files)
	}
	if g.scrubbing {
		err := g.updateScrub(x, e.IsMouseButtonPressed(e.MouseButtonLeft), false)
		g.followMarker()
		return err
	}
	if key(e.KeyF1) || !g.help && !g.full && click && y < 36 && x >= 460 && x < 540 {
		g.help = !g.help
		g.dragging, g.resizingNav = false, false
		e.SetCursorShape(e.CursorShapeDefault)
		return nil
	}
	if g.help {
		if key(e.KeyEscape) || click {
			g.help = false
		}
		g.followMarker()
		return nil
	}
	if key(e.KeyT) || !g.full && click && y < 36 && x >= 540 && x < 640 {
		g.ide = !g.ide
	}
	if g.resizingNav {
		g.resizeLibrary(x)
		g.resizingNav = e.IsMouseButtonPressed(e.MouseButtonLeft)
		if !g.resizingNav {
			e.SetCursorShape(e.CursorShapeDefault)
		}
		return nil
	}
	if key(e.KeyBracketLeft) {
		g.moveWork(-1)
	} else if key(e.KeyBracketRight) {
		g.moveWork(1)
	}
	if key(e.KeyF) || key(e.KeyEscape) && g.full || click && ((!g.full && y < 36 && x >= 320 && x < 460) || (g.full && x >= g.w-90 && y < 36)) {
		g.dragging = false
		e.SetCursorShape(e.CursorShapeDefault)
		g.full = !g.full
		return nil
	}
	if !g.full && (key(e.KeyTab) || click && y < 36 && x < 100) {
		g.nav = !g.nav
	}
	if g.tex != nil {
		if g.paused && (key(e.KeyComma) || key(e.KeyPeriod)) {
			delta := 1
			if key(e.KeyComma) {
				delta = -1
			}
			count := pieces[g.id].count
			if err := g.seekFrame((g.frame() + delta + count) % count); err != nil {
				return err
			}
		}
		if key(e.KeySpace) || !g.full && click && y < 36 && x >= 100 && x < 210 {
			g.togglePause()
		}
		if key(e.KeyR) || !g.full && click && y < 36 && x >= 210 && x < 320 {
			if err := g.restart(); err != nil {
				return err
			}
		}
	}
	if g.full {
		return nil
	}
	onSidebar := g.nav && !g.dragging && y >= 36 && x >= g.left()-5 && x <= g.left()+4
	if onSidebar {
		e.SetCursorShape(e.CursorShapeEWResize)
		if click {
			g.resizingNav = true
		}
		g.followMarker()
		return nil
	}
	bar := g.timeline()
	if g.tex != nil && click && x >= bar.left-4 && x <= bar.right+4 && y >= bar.y-10 && y <= bar.y+10 {
		g.resumeAfterScrub = !g.paused
		if !g.paused {
			g.togglePause()
		}
		g.scrubbing = true
		err := g.updateScrub(x, true, true)
		g.followMarker()
		return err
	}
	onDivider := g.tex != nil && x >= g.left() && y >= g.split()-6 && y < g.split()+5
	if click && onDivider {
		g.dragging = true
	}
	if !e.IsMouseButtonPressed(e.MouseButtonLeft) {
		g.dragging = false
	}
	if onDivider || g.dragging {
		e.SetCursorShape(e.CursorShapeNSResize)
	} else {
		e.SetCursorShape(e.CursorShapeDefault)
	}
	if g.dragging {
		g.ratio = float64(max(120, min(g.h-108, y))) / float64(g.h)
		return nil
	}
	_, wheel := e.Wheel()
	if g.nav && x < g.left() && y >= 36 {
		g.libraryInput(x, y, click, wheel)
	}
	if g.tex == nil || len(g.lines) == 0 {
		return nil
	}
	if x >= g.left() && y >= g.split() {
		if wheel != 0 {
			g.sourceScroll(-int(wheel) * 3)
		}
		if click && y < g.split()+30 {
			local := x - g.left()
			if local < 100 {
				g.file = (g.file + 1) % len(g.lines)
				g.prepareListing()
				g.line = 0
				g.column = 0
				g.follow = false
			} else if local < 225 && len(pieces[g.id].markers) > 0 {
				g.follow = !g.follow
			}
		}
	}
	if key(e.KeyPageDown) {
		g.sourceScroll(g.rowsVisible())
	}
	if key(e.KeyPageUp) {
		g.sourceScroll(-g.rowsVisible())
	}
	if key(e.KeyArrowDown) {
		g.sourceScroll(1)
	}
	if key(e.KeyArrowUp) {
		g.sourceScroll(-1)
	}
	if key(e.KeyArrowRight) {
		g.column = min(262144, g.column+8)
		g.follow = false
	}
	if key(e.KeyArrowLeft) {
		g.column = max(0, g.column-8)
		g.follow = false
	}
	g.followMarker()
	return nil
}

func (g *player) followMarker() {
	if g.follow {
		if m := g.activeMarker(); m != nil {
			for i, s := range pieces[g.id].sources {
				if s == m.File {
					if g.file != i {
						g.file = i
						g.column = 0
						g.line = 0
						g.prepareListing()
					}
					g.reveal(m.Line - 1)
					break
				}
			}
		}
	}
}

func (g *player) Draw(s *e.Image) {
	palette := g.colors()
	ink, accent := palette.ink, palette.accent
	s.Fill(palette.background)
	if g.help {
		defer g.drawShortcuts(s)
	}
	label := func(x, y int, str string, c color.Color) { text.Draw(s, str, g.face, x, y, c) }
	left := g.left()
	top, bottom := 38, g.split()-40
	if g.full {
		top = 0
		bottom = g.h
	}
	if g.tex != nil {
		g.paint()
		p := pieces[g.id]
		aw, ah := float64(p.w*9), float64(p.h*18)
		scale := math.Min(float64(g.w-left)/aw, float64(bottom-top)/ah)
		op := &e.DrawImageOptions{}
		op.GeoM.Scale(scale, scale)
		op.GeoM.Translate(float64(left)+(float64(g.w-left)-aw*scale)/2, float64(top)+(float64(bottom-top)-ah*scale)/2)
		s.DrawImage(g.tex, op)
	}
	if g.full {
		label(g.w-80, 22, "[Exit F]", accent)
		g.drawMessage(s, g.status, 8, 24, g.w-110)
		return
	}
	button := "[Pause]"
	if g.paused {
		button = "[Play]"
	}
	label(10, 24, "[Library]", accent)
	label(110, 24, button, accent)
	label(220, 24, "[Restart]", accent)
	label(330, 24, "[Art view F]", accent)
	label(460, 24, "[Keys]", accent)
	theme := "[Theme Lab]"
	if g.ide {
		theme = "[Theme IDE]"
	}
	label(540, 24, theme, accent)
	if g.nav {
		g.drawLibrary(s)
	}
	g.drawMessage(s, g.libraryStatus(), left+10, top+20, g.w-left-20)
	if g.tex == nil {
		g.drawMessage(s, g.emptyMessage(), left+10, top+120, g.w-left-20)
		return
	}
	g.drawTimeline(s)
	split := g.split()
	vector.DrawFilledRect(s, float32(left), float32(split), float32(g.w-left), 30, palette.panel, false)
	vector.DrawFilledRect(s, float32(left), float32(split-2), float32(g.w-left), 2, palette.divider, false)
	vector.DrawFilledRect(s, float32((g.w+left)/2-17), float32(split-3), 34, 4, ink, false)
	if len(g.lines) == 0 {
		label(left+10, split+21, "No source included", ink)
		return
	}
	label(left+8, split+21, "[File >]", accent)
	if len(pieces[g.id].markers) > 0 {
		v := "[Follow off]"
		if g.follow {
			v = "[Follow on]"
		}
		label(left+100, split+21, v, accent)
	}
	label(left+229, split+21, pieces[g.id].sources[g.file], ink)
	g.drawListing(s)
}
func (g *player) Layout(w, h int) (int, int) {
	g.w, g.h = max(640, w), max(420, h)
	return g.w, g.h
}
