// Carbon Paper — a moving impression in four inks.
// MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.
// Rebuild the logical cells with: go run carbon.go frames.bin
package main

import (
	"bufio"
	"fmt"
	"io"
	"math"
	"os"
)

const cols, rows, frames = 116, 38, 300
const tau = 2 * math.Pi

type point struct{ x, y float64 }
type ink [3]byte

var cream = ink{247, 218, 159}
var ochre = ink{190, 150, 99}
var copper = ink{243, 107, 73}
var carbon = ink{73, 149, 203}
var rule = ink{75, 95, 103}
var paper = ink{17, 26, 35}

type cell struct {
	glyph rune
	color ink
}
type sheet [rows][cols]cell

func blend(a, b ink, t float64) ink {
	var c ink
	for i := range c {
		c[i] = byte(math.Round(float64(a[i])*(1-t) + float64(b[i])*t))
	}
	return c
}
func ease(a, b, x float64) float64 {
	t := math.Max(0, math.Min(1, (x-a)/(b-a)))
	return t * t * (3 - 2*t)
}
func (s *sheet) dot(p point, c ink) {
	x, y := int(math.Round(p.x)), int(math.Round(p.y))
	if x < 0 || x >= 2*cols || y < 0 || y >= 4*rows {
		return
	}
	v := &s[y/4][x/2]
	if v.glyph < 0x2800 || v.glyph > 0x28ff {
		v.glyph = 0x2800
	}
	bits := [4][2]rune{{1, 8}, {2, 16}, {4, 32}, {64, 128}}
	v.glyph |= bits[y%4][x%2]
	v.color = c
}
func (s *sheet) label(x, y int, word string, c ink) {
	for _, r := range word {
		s[y][x] = cell{r, c}
		x++
	}
}

type press struct {
	sheet            *sheet
	origin           point
	flap, cut, angle float64
}

func (p press) line(a, b, c point, color ink) {
	// A curved ruling becomes a feather when the sheet leaves the platen.
	for i := 0; i <= 140; i++ {
		t := float64(i) / 140
		u := 1 - t
		x := u*u*a.x + 2*t*u*b.x + t*t*c.x
		y := u*u*a.y + 2*t*u*b.y + t*t*c.y
		if x > p.cut {
			continue
		}
		co, si := math.Cos(p.angle), math.Sin(p.angle)
		p.sheet.dot(point{p.origin.x + x*co - y*si, p.origin.y + y*co + x*si}, color)
	}
}
func (p press) bird(light, mid, detail ink) {
	// Two ruled fans share one brass pivot. Their tips travel at different speeds.
	for side := 0; side < 2; side++ {
		span := -1.
		shade := light
		if side == 0 {
			span = .70
			shade = mid
		}
		for k := 0; k < 15; k++ {
			t := float64(k) / 14
			root := point{-5 + 15*t, -1}
			tip := point{-61 + 53*t, span * (13 + 41*t) * (1 + p.flap*.36)}
			bend := point{-14 + 24*t, span * (19 + 18*t)}
			p.line(root, bend, tip, shade)
			if k > 0 {
				p.line(tip, point{tip.x + 2, tip.y + span*2}, point{tip.x + 3.8, tip.y + span*2.7}, shade)
			}
		}
	}
	// A forked tail, a turned breast and a beak cut from a single strip.
	for i := 0; i < 6; i++ {
		f := float64(i)
		p.line(point{2, 1}, point{-17, 5 + f*.4}, point{-56 + f*3, 19 - f*2.3}, mid)
		p.line(point{0, 0}, point{-21, 2 - f*.3}, point{-52 + f*2, -2 + f*.9}, light)
	}
	p.line(point{-27, 4}, point{-10, -5}, point{10, -4}, light)
	p.line(point{10, -4}, point{21, -19}, point{27, -9}, light)
	p.line(point{27, -9}, point{31, -8}, point{37, -8}, detail)
	p.line(point{37, -8}, point{31, -6}, point{26, -6}, detail)
	p.line(point{26, -6}, point{15, 13}, point{-27, 4}, light)
	for i := 0; i < 8; i++ {
		x := float64(i)*3 - 12
		p.line(point{x, 1}, point{x + 3, 3}, point{x + 5, 5}, mid)
	}
	p.line(point{22, -10}, point{22, -11}, point{23, -10}, detail)
	for i := 0; i < 60; i++ {
		a := tau * float64(i) / 60
		b := point{3 + 3*math.Cos(a), 3 * math.Sin(a)}
		p.line(b, b, b, detail)
	}
}
func register(s *sheet) {
	// Four interrupted corners locate the missing sheet.
	for _, x := range []int{12, 219} {
		for _, y := range []int{15, 129} {
			for k := -4; k <= 4; k++ {
				if k != 0 {
					s.dot(point{float64(x + k), float64(y)}, rule)
					s.dot(point{float64(x), float64(y + k)}, rule)
				}
			}
		}
	}
	s.label(6, 1, "CARBON PAPER", cream)
	s.label(88, 1, "TRANSFER STUDY   /   01", rule)
	for x := 13; x < 219; x += 2 {
		s.dot(point{float64(x), 137}, rule)
	}
	s.label(6, 35, "IMPRESSION", carbon)
	s.label(19, 35, "/  FLIGHT", cream)
}
func imageAt(n int) sheet {
	t := float64(n) / frames
	var s sheet
	register(&s)
	// Ink reaches the stationary plate from tail to beak.
	cut := -65 + 108*ease(.025, .32, t)
	// The under-sheet takes a second, ultramarine impression.
	deposit := ease(.20, .39, t) * (1 - ease(.72, .97, t))
	ghost := press{&s, point{105, 85}, 0, cut, 0}
	if deposit > .005 {
		ghost.bird(blend(paper, carbon, deposit), blend(paper, carbon, .62*deposit), blend(paper, cream, .45*deposit))
	}
	// Lift the warm impression; its carbon twin stays on the bed.
	lift := ease(.35, .86, t)
	wing := math.Sin(tau*3*lift) * ease(0, .18, lift)
	flying := press{&s, point{105 + 102*lift, 85 - 41*lift}, wing, cut, -.19 * lift}
	strength := (1 - ease(.73, .88, t))
	if strength > .005 {
		flying.bird(blend(paper, cream, strength), blend(paper, ochre, strength), blend(paper, copper, strength))
	}
	// The last blue trace returns to unmarked paper.
	caption := "01   REGISTER"
	switch {
	case t >= .88:
		caption = "05   RELEASE "
	case t >= .72:
		caption = "04   RESIDUE "
	case t >= .35:
		caption = "03   LIFT    "
	case t >= .20:
		caption = "02   TRANSFER"
	}
	s.label(91, 35, caption, copper)
	return s
}
func export(w io.Writer) error {
	buf := make([]byte, cols*rows*5)
	for n := 0; n < frames; n++ {
		s := imageAt(n)
		i := 0
		for _, row := range s {
			for _, v := range row {
				if v.glyph == 0 {
					v.glyph = ' '
					v.color = paper
				}
				buf[i] = byte(v.glyph)
				buf[i+1] = byte(v.glyph >> 8)
				copy(buf[i+2:i+5], v.color[:])
				i += 5
			}
		}
		if _, err := w.Write(buf); err != nil {
			return err
		}
	}
	return nil
}
func main() {
	if len(os.Args) != 2 {
		panic("usage: go run carbon.go frames.bin")
	}
	f, err := os.Create(os.Args[1])
	if err != nil {
		panic(err)
	}
	w := bufio.NewWriter(f)
	if err = export(w); err != nil {
		panic(err)
	}
	if err = w.Flush(); err != nil {
		panic(err)
	}
	if err = f.Close(); err != nil {
		panic(err)
	}
	fmt.Println("300 impressions at 20 fps")
}
