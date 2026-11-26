package main

import (
	"bytes"

	"encoding/binary"

	e "github.com/hajimehoshi/ebiten/v2"

	"golang.org/x/image/font"
	"golang.org/x/image/font/opentype"
	"golang.org/x/image/math/fixed"
	"image"
	"image/color"

	_ "embed"
	"os"
	"path/filepath"
)

//go:embed fonts/JetBrainsMono-Regular.ttf
var mono []byte

type player struct {
	id, last int
	view
	raw, pixels []byte
	tex         *e.Image
	masks       map[rune]*image.Alpha
	face        font.Face
}

func (g *player) mask(ch rune) *image.Alpha {
	if a := g.masks[ch]; a != nil {
		return a
	}
	a := image.NewAlpha(image.Rect(0, 0, 9, 18))
	switch {
	case ch >= 0x2800 && ch <= 0x28ff:
		bits := [4][2]int{{1, 8}, {2, 16}, {4, 32}, {64, 128}}
		for j, r := range bits {
			for i, b := range r {
				if int(ch-0x2800)&b != 0 {
					for y := 0; y < 2; y++ {
						for x := 0; x < 2; x++ {
							a.SetAlpha(1+5*i+x, 2+4*j+y, color.Alpha{255})
						}
					}
				}
			}
		}
	case ch >= '▁' && ch <= '█' || ch == '▀':
		for y := 0; y < 18; y++ {
			if (ch == '▀' && y < 9) || (ch != '▀' && y >= 18-(int(ch-'▁'+1)*18+4)/8) {
				for x := 0; x < 9; x++ {
					a.SetAlpha(x, y, color.Alpha{255})
				}
			}
		}
	default:
		d := font.Drawer{Dst: a, Src: image.White, Face: g.face, Dot: fixed.P(0, 14)}
		d.DrawString(string(ch))
	}
	g.masks[ch] = a
	return a
}
func (g *player) paint() {
	p := pieces[g.id]
	n := g.frame()
	if n != g.last {
		stride := p.w * p.h * 5
		f := g.raw[n*stride : (n+1)*stride]
		for i := 0; i < p.w*p.h; i++ {
			v := f[i*5:]
			if g.last >= 0 && bytes.Equal(v[:5], g.raw[g.last*stride+i*5:g.last*stride+i*5+5]) {
				continue
			}
			a := g.mask(rune(binary.LittleEndian.Uint16(v)))
			for y := 0; y < 18; y++ {
				base := ((i/p.w*18+y)*p.w*9 + i%p.w*9) * 4
				for x := 0; x < 9; x++ {
					alpha := int(a.Pix[y*9+x])
					for k := 0; k < 3; k++ {
						g.pixels[base+x*4+k] = byte((int(v[2+k])*alpha + int(p.bg[k])*(255-alpha) + 127) / 255)
					}
					g.pixels[base+x*4+3] = 255
				}
			}
		}
		g.tex.WritePixels(g.pixels)
		g.last = n
	}
}
func main() {
	f, err := opentype.Parse(mono)
	if err != nil {
		panic(err)
	}
	face, err := opentype.NewFace(f, &opentype.FaceOptions{Size: 15, DPI: 72, Hinting: font.HintingFull})
	if err != nil {
		panic(err)
	}
	g := player{face: face, masks: map[rune]*image.Alpha{}}
	exe, err := os.Executable()
	if err != nil {
		panic(err)
	}
	g.libraryDir = filepath.Join(filepath.Dir(exe), "artworks")
	g.skipped, g.libraryErr = discover(g.libraryDir)
	defer g.stopTrack()
	g.nav = true
	e.SetWindowTitle("RariWare Lab Player")
	e.SetWindowSize(1180, 860)
	e.SetWindowResizingMode(e.WindowResizingModeEnabled)
	if len(os.Args) > 1 {
		g.openPath(os.Args[1])
	}
	if g.tex == nil && len(pieces) > 0 {
		openError := g.status
		g.selectPiece(0)
		if openError != "" {
			g.status = openError
		}
	}
	if err = e.RunGame(&g); err != nil {
		panic(err)
	}
}
