package main

import (
	"fmt"
	e "github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/text"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"golang.org/x/image/math/fixed"
	"image/color"
	"path/filepath"
	"strings"
	"unicode"
)

const rowHeight = 22

type styledLine struct {
	chars  []rune
	styles []byte
}

// Each scanner carries only its file's multiline string delimiter between lines.
type scanner func([]rune, []byte, string) string

var scanners = map[string]scanner{".py": pythonLine, ".pyw": pythonLine}
var syntaxColors = []color.RGBA{ink, {145, 166, 164, 255}, {190, 174, 220, 255}, {181, 199, 151, 255}, {219, 184, 137, 255}}

const pythonWords = " False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield "

func pythonLine(r []rune, style []byte, delimiter string) string {
	for i := 0; i < len(r); {
		start := i
		kind := byte(0)
		switch {
		case delimiter != "" || r[i] == '\'' || r[i] == '"':
			kind = 3
			if delimiter == "" {
				delimiter = string(r[i])
				if i+2 < len(r) && r[i] == r[i+1] && r[i] == r[i+2] {
					delimiter = strings.Repeat(delimiter, 3)
				}
				i += len(delimiter)
			}
			for i < len(r) {
				if r[i] == '\\' {
					i = min(len(r), i+2)
					continue
				}
				if i+len(delimiter) <= len(r) && string(r[i:i+len(delimiter)]) == delimiter {
					i += len(delimiter)
					delimiter = ""
					break
				}
				i++
			}
			if len(delimiter) == 1 && (len(r) == 0 || r[len(r)-1] != '\\') {
				delimiter = ""
			}
		case r[i] == '#':
			kind = 1
			i = len(r)
		case unicode.IsLetter(r[i]) || r[i] == '_':
			i++
			for i < len(r) && (unicode.IsLetter(r[i]) || unicode.IsDigit(r[i]) || r[i] == '_') {
				i++
			}
			if strings.Contains(pythonWords, " "+string(r[start:i])+" ") {
				kind = 2
			}
		case unicode.IsDigit(r[i]):
			kind = 4
			i++
			for i < len(r) && (unicode.IsDigit(r[i]) || r[i] == '.' || r[i] == '_') {
				i++
			}
		default:
			i++
		}
		for n := start; n < i; n++ {
			style[n] = kind
		}
	}
	return delimiter
}
func (g *player) prepareListing() {
	g.listing = nil
	if len(g.lines) == 0 {
		return
	}
	scan := scanners[strings.ToLower(filepath.Ext(pieces[g.id].sources[g.file]))]
	state := ""
	for _, line := range g.lines[g.file] {
		l := styledLine{chars: []rune(strings.ReplaceAll(line, "\t", "    "))}
		if scan != nil {
			l.styles = make([]byte, len(l.chars))
			state = scan(l.chars, l.styles, state)
		}
		g.listing = append(g.listing, l)
	}
}
func (g *player) rowsVisible() int { return max(1, (g.h-g.split()-36)/rowHeight) }
func (g *player) reveal(line int) {
	rows := g.rowsVisible()
	// The middle third is a quiet zone for adjacent annotations.
	if line >= g.line+rows/3 && line <= g.line+(rows-1)*2/3 {
		return
	}
	g.line = max(0, min(len(g.lines[g.file])-rows, line-rows/2))

}
func (g *player) drawListing(s *e.Image) {
	left, top := g.left(), g.split()+34
	advance, _ := g.face.GlyphAdvance('0')
	marker := g.activeMarker()
	for row := 0; row < g.rowsVisible() && g.line+row < len(g.listing); row++ {
		index := g.line + row
		y := top + row*rowHeight
		if g.follow && marker != nil && marker.File == pieces[g.id].sources[g.file] && marker.Line == index+1 {
			vector.DrawFilledRect(s, float32(left), float32(y), float32(g.w-left), rowHeight, color.RGBA{40, 61, 58, 255}, false)
			vector.DrawFilledRect(s, float32(left), float32(y), 3, rowHeight, accent, false)
		}
		text.Draw(s, fmt.Sprintf("%5d", index+1), g.face, left+8, y+16, syntaxColors[1])
		line := g.listing[index]
		x := left + 70
		start := min(g.column, len(line.chars))
		end := min(len(line.chars), start+(g.w-x)*64/max(1, int(advance)))
		for i := start; i < end; {
			j := i + 1
			kind := byte(0)
			if line.styles != nil {
				kind = line.styles[i]
				for j < end && line.styles[j] == kind {
					j++
				}
			} else {
				j = end
			}
			text.Draw(s, string(line.chars[i:j]), g.face, x+int((advance*fixed.Int26_6(i-start)).Round()), y+16, syntaxColors[kind])
			i = j
		}
	}
}
