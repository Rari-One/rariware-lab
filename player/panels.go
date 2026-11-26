package main

import (
	"fmt"
	"image"
	"image/color"
	"strings"

	e "github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/text"
	"github.com/hajimehoshi/ebiten/v2/vector"
)

type palette struct {
	background, panel, selected, divider, ink, accent color.RGBA
	syntax                                            [5]color.RGBA
}

var labPalette = palette{
	background: color.RGBA{15, 20, 24, 255}, panel: color.RGBA{34, 47, 50, 255}, selected: color.RGBA{40, 61, 58, 255},
	divider: color.RGBA{70, 92, 93, 255}, ink: color.RGBA{201, 215, 215, 255}, accent: color.RGBA{137, 226, 191, 255},
	syntax: [5]color.RGBA{{201, 215, 215, 255}, {145, 166, 164, 255}, {190, 174, 220, 255}, {181, 199, 151, 255}, {219, 184, 137, 255}},
}
var idePalette = palette{
	background: color.RGBA{0, 0, 0, 255}, panel: color.RGBA{26, 29, 36, 255}, selected: color.RGBA{31, 51, 76, 255},
	divider: color.RGBA{79, 89, 106, 255}, ink: color.RGBA{220, 224, 233, 255}, accent: color.RGBA{128, 194, 255, 255},
	syntax: [5]color.RGBA{{220, 224, 233, 255}, {135, 169, 133, 255}, {196, 157, 246, 255}, {242, 175, 142, 255}, {158, 211, 195, 255}},
}

func (g *player) colors() *palette {
	if g.ide {
		return &idePalette
	}
	return &labPalette
}

type libraryCard struct {
	top, height int
	lines       []string
}

const cardsTop = 64

func (g *player) sidebarWidth() int {
	width := g.navWidth
	if width == 0 {
		width = 220
	}
	return max(128, min(width, max(640, g.w)-360))
}

func (g *player) resizeLibrary(x int) {
	if x < 64 {
		g.nav = false
		return
	}
	g.nav = true
	g.navWidth = max(128, min(x, g.w-360))
}

func (g *player) layoutCards() {
	width := g.sidebarWidth()
	if g.cardWidth != width || len(g.cards) != len(pieces) {
		g.cards = g.cards[:0]
		g.cardHeight = 0
		cols := max(1, (width-42)/9)
		for _, p := range pieces {
			lines := wrapText(strings.TrimSpace(p.name), cols)
			h := len(lines)*19 + 12
			g.cards = append(g.cards, libraryCard{g.cardHeight, h, lines})
			g.cardHeight += h + 4
		}
		g.cardWidth = width
	}
	g.offset = max(0, min(g.offset, g.cardHeight-max(1, g.h-cardsTop)))
}

func (g *player) revealCard(i int) {
	g.layoutCards()
	c := g.cards[i]
	g.offset = min(c.top, max(g.offset, c.top+c.height-max(1, g.h-cardsTop)))
}

func (g *player) libraryInput(x, y int, click bool, wheel float64) {
	g.layoutCards()
	g.offset -= int(wheel * 38)
	g.layoutCards()
	if click && x >= 8 && x < g.left()-10 && y >= cardsTop {
		pos := y - cardsTop + g.offset
		for i, c := range g.cards {
			if pos >= c.top && pos < c.top+c.height {
				g.selectPiece(i)
				break
			}
		}
	}
}

func (g *player) drawLibrary(s *e.Image) {
	g.layoutCards()
	p := g.colors()
	w := g.left()
	heading := "ARTWORKS"
	if g.skipped > 0 {
		count := fmt.Sprintf("%d skipped", g.skipped)
		heading += "  " + count
		if len(heading)*9 > w-20 {
			heading = count
		}
	}
	text.Draw(s, heading, g.face, 12, 55, p.ink)
	list := s.SubImage(image.Rect(0, cardsTop, w-5, g.h)).(*e.Image)
	for i, c := range g.cards {
		y := cardsTop + c.top - g.offset
		if y >= g.h {
			break
		}
		if y+c.height <= cardsTop {
			continue
		}
		bg, fg := p.panel, p.ink
		active := i == g.id && g.tex != nil
		if active {
			bg, fg = p.selected, p.accent
		}
		vector.DrawFilledRect(list, 8, float32(y), float32(w-18), float32(c.height), bg, false)
		if active {
			vector.DrawFilledRect(list, 8, float32(y), 3, float32(c.height), p.accent, false)
		}
		for j, line := range c.lines {
			text.Draw(list, line, g.face, 19, y+20+j*19, fg)
		}
	}
	vector.DrawFilledRect(s, float32(w-2), 36, 2, float32(g.h-36), p.divider, false)
	vector.DrawFilledRect(s, float32(w-3), float32((g.h+36)/2-16), 4, 32, p.ink, false)
}

var shortcuts = [][2]string{
	{"Space", "Pause or resume"}, {"R", "Restart work"}, {"[  /  ]", "Previous / next work"},
	{",  /  .", "Step one frame while paused"}, {"F  /  Esc", "Toggle Art view / leave Art view"},
	{"Tab", "Hide or show library"}, {"Up / Down", "Scroll source one line"}, {"Page Up / Down", "Scroll source one page"},
	{"Left / Right", "Scroll source horizontally"}, {"T", "Switch Lab / IDE theme"}, {"F1  /  Esc", "Toggle controls / close guide"},
	{"Click tick / drag", "Jump to a marker / seek"}, {"Drop a .rwl", "Open a work for this session"},
}

func (g *player) drawShortcuts(s *e.Image) {
	p := g.colors()
	w, h := 520, 80+len(shortcuts)*24
	x, y := (g.w-w)/2, (g.h-h)/2
	vector.DrawFilledRect(s, float32(x), float32(y), float32(w), float32(h), p.divider, false)
	vector.DrawFilledRect(s, float32(x+1), float32(y+1), float32(w-2), float32(h-2), p.panel, false)
	text.Draw(s, "Controls", g.face, x+20, y+30, p.ink)
	text.Draw(s, "[Close]", g.face, x+w-84, y+30, p.accent)
	for i, row := range shortcuts {
		base := y + 66 + i*24
		text.Draw(s, row[0], g.face, x+20, base, p.accent)
		text.Draw(s, row[1], g.face, x+186, base, p.ink)
	}
}
