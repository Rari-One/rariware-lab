// The Margin of Error. Coordinates in the drawing are Braille dot pitches.
package main

import (
	"archive/zip"
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"strings"
)

const W, H, FPS, Frames = 72, 32, 15, 300
const rate = 48000
const tau = 2 * math.Pi

type pt struct{ x, y float64 }

func mix(a, b, t float64) float64 { return a + (b-a)*t }
func ramp(a, b, t float64) float64 {
	v := math.Max(0, math.Min(1, (t-a)/(b-a)))
	return v * v * (3 - 2*v)
}
func interp(a, b pt, t float64) pt { return pt{mix(a.x, b.x, t), mix(a.y, b.y, t)} }
func det(a, b pt) float64          { return a.x*b.y - a.y*b.x }
func sub(a, b pt) pt               { return pt{a.x - b.x, a.y - b.y} }

var paper = []pt{{-1, -.75}, {0, -.75}, {.54, -.75}, {1, -.75}, {1, 0}, {1, .75}, {.54, .75}, {0, .75}, {-1, .75}, {-1, 0}, {0, 0}}
var bird = []pt{{-.94, .15}, {-.45, -.98}, {.03, -.14}, {.55, -.41}, {1, -.25}, {.48, -.08}, {.12, .09}, {-.37, .75}, {-.91, .24}, {-1.09, .34}, {.06, .02}}

// The second wing creases one registration square late.
var beats = []float64{6.3, 6.99, 9.9, 10.59, 13.55, 14.24}

func beat(t float64) float64 {
	v := 0.
	for _, b := range beats {
		u := (t - b) / .61
		if u > 0 && u < 1 {
			v += math.Pow(math.Sin(math.Pi*u), 2)
		}
	}
	return v
}
func mesh(t float64) (v [11]pt, fold float64) {
	fold = ramp(1.2, 6.25, t) * (1 - ramp(16.7, 19.8, t))
	drift := ramp(5.3, 8, t) * (1 - ramp(16, 19.6, t))
	approach := ramp(14.3, 17.15, t) * (1 - ramp(17.25, 19.85, t))
	cx := 71 + drift*(5*math.Sin(t*.88)+6) - 24*approach
	cy := 65 + drift*(4*math.Cos(t*.95)-4) - 8*approach
	scale := 48 + 60*approach
	angle := -.09*(1-fold) + fold*(.015+.065*math.Sin(t*1.5)+.08*beat(t-.19))
	for i, p := range paper {
		target := bird[i]
		// Two brisk strokes and a held glide; the short wing trails the shoulder.
		if i == 1 {
			target.y += 1.15 * beat(t)
			target.x -= .16 * beat(t)
		}
		if i == 7 {
			target.x += .15 // one displaced square on the short wing
			target.y -= .72 * beat(t-.16)
			target.x += .14 * beat(t-.16)
		}
		delay := float64(i%3) * .33
		f := ramp(1.15+delay, 5.65+delay, t) * (1 - ramp(16.65+delay*.3, 19.78, t))
		q := interp(p, target, f)
		q.y += .19 * math.Sin(math.Pi*f) * math.Sin(float64(i)*1.7)
		v[i] = pt{cx + scale*(q.x*math.Cos(angle)-q.y*math.Sin(angle)), cy + scale*(q.x*math.Sin(angle)+q.y*math.Cos(angle))}
	}
	return
}

type rgb struct{ r, g, b byte }

var inks = []rgb{{0, 0, 0}, {236, 225, 190}, {209, 211, 189}, {247, 238, 207}, {174, 193, 183}, {131, 161, 159}, {78, 111, 116}, {248, 87, 66}, {76, 112, 124}}
var tones = [10]int{2, 3, 4, 1, 3, 2, 4, 5, 6, 4}

const SW, SH = W * 2, H * 4

type raster [SW * SH]byte

func dot(buf *raster, x, y, c int) {
	if x >= 0 && x < SW && y >= 0 && y < SH {
		buf[y*SW+x] = byte(c)
	}
}
func picture(t float64) []byte {
	var buf raster
	// Quiet drafting-table ticks survive the close pass of the bird.
	for x := 9; x < SW-8; x += 5 {
		h := 1
		if (x-9)%20 == 0 {
			h = 3
		}
		for j := 0; j < h; j++ {
			dot(&buf, x, SH-8+j, 8)
		}
	}
	for _, x := range []int{9, SW - 10} {
		for _, y := range []int{11, SH - 17} {
			for d := -2; d <= 2; d++ {
				dot(&buf, x+d, y, 8)
				dot(&buf, x, y+d, 8)
			}
		}
	}
	v, fold := mesh(t)
	order := []int{7, 6, 8, 9, 0, 1, 2, 3, 4, 5}
	for _, i := range order {
		j := (i + 1) % 10
		a, b, c := v[10], v[i], v[j]
		ab, ac := sub(b, a), sub(c, a)
		area := det(ab, ac)
		if math.Abs(area) < .01 {
			continue
		}
		xmin := int(math.Max(0, math.Floor(math.Min(a.x, math.Min(b.x, c.x)))))
		xmax := int(math.Min(SW-1, math.Ceil(math.Max(a.x, math.Max(b.x, c.x)))))
		ymin := int(math.Max(0, math.Floor(math.Min(a.y, math.Min(b.y, c.y)))))
		ymax := int(math.Min(SH-1, math.Ceil(math.Max(a.y, math.Max(b.y, c.y)))))
		for y := ymin; y <= ymax; y++ {
			for x := xmin; x <= xmax; x++ {
				d := sub(pt{float64(x) + .5, float64(y) + .5}, a)
				u, w := det(d, ac)/area, det(ab, d)/area
				if u < 0 || w < 0 || u+w > 1 {
					continue
				}
				sx := paper[i].x*u + paper[j].x*w
				sy := paper[i].y*u + paper[j].y*w
				hue := 1
				if fold > .10+float64(i%4)*.10 {
					hue = tones[i]
				}
				// The ruling stays attached to the material as the facets narrow.
				if math.Abs(math.Remainder(sx+.075, .15)) < .010 || math.Abs(math.Remainder(sy, .15)) < .009 {
					hue = 9 // blue ruling over the face of the paper
				}
				if fold > .35 && w < .014 && i%2 == 0 {
					hue = 6
				}
				dot(&buf, x, y, hue)
			}
		}
	}
	// A registration cross, fixed at material coordinates on the beak facet.
	eye := pt{v[10].x*.20 + v[3].x*.48 + v[4].x*.32, v[10].y*.20 + v[3].y*.48 + v[4].y*.32}
	ex, ey := int(math.Round(eye.x)), int(math.Round(eye.y))
	for d := -2; d <= 2; d++ {
		dot(&buf, ex+d, ey, 7)
		dot(&buf, ex, ey+d, 7)
	}
	bits := [8]uint16{1, 8, 2, 16, 4, 32, 64, 128}
	out := make([]byte, W*H*5)
	for y := 0; y < H; y++ {
		for x := 0; x < W; x++ {
			var count [10]int
			var mask, red uint16
			for n, bit := range bits {
				k := buf[(y*4+n/2)*SW+x*2+n%2]
				count[k]++
				if k != 0 {
					mask |= bit
				}
				if k == 7 {
					red |= bit
				}
			}
			hue := 1
			for k := 2; k < len(inks); k++ {
				if count[k] > count[hue] {
					hue = k
				}
			}
			if red != 0 {
				hue = 7
				mask = red
			}
			glyph := uint16(0x2800) + mask
			switch mask {
			case 0:
				glyph = 32
				hue = 0
			case 255:
				glyph = '█'
			case 192:
				glyph = '▂'
			case 228:
				glyph = '▄'
			case 246:
				glyph = '▆'
			}
			n := 5 * (y*W + x)
			binary.LittleEndian.PutUint16(out[n:], glyph)
			p := inks[hue]
			if count[9] > 0 && hue != 7 {
				strength := float64(count[9]) / 8
				p = rgb{byte(mix(float64(p.r), 64, strength)), byte(mix(float64(p.g), 105, strength)), byte(mix(float64(p.b), 126, strength))}
			}
			out[n+2] = p.r
			out[n+3] = p.g
			out[n+4] = p.b
		}
	}
	return out
}

type cue struct{ at, length, pitch, pan, gain float64 }

func score() []byte {
	cues := []cue{{1.2, .63, 425, -.63, .32}, {2.13, .4, 630, .23, .23}, {3.26, .77, 348, -.31, .34}, {4.58, .48, 516, .72, .33}, {5.38, .29, 810, .78, .26}, {15.7, 1.7, 245, -.66, .24}, {17.63, 1.49, 350, .48, .26}}
	for _, b := range beats {
		cues = append(cues, cue{b, .43, 335, -.58, .37}, cue{b + .16, .48, 478, .59, .27})
	}
	// One long breath underneath the creases. No noise or resonance crosses the seam.
	data := make([]byte, rate*20*4)
	seed := uint32(0x3a7)
	low := 0.
	slow := 0.
	for n := 0; n < len(data)/4; n++ {
		t := float64(n) / rate
		seed = 1664525*seed + 1013904223
		noise := float64(seed)/2147483648 - 1
		low += .21 * (noise - low)
		slow += .023 * (low - slow)
		air := (low - slow) * .052 * ramp(5, 9, t) * (1 - ramp(15, 19, t))
		l, r := air, air*.75
		for _, c := range cues {
			d := t - c.at
			if d < 0 || d >= c.length {
				continue
			}
			u := d / c.length
			env := math.Pow(math.Sin(math.Pi*u), 1.4)
			fiber := .48 + .52*math.Pow(math.Cos(tau*(13*d+19*d*d)), 4)
			grain := (low - slow) * 1.8 * fiber
			ring := math.Sin(tau*c.pitch*(d-.09*d*d))*.14 + math.Sin(tau*c.pitch*1.51*d)*.065
			amp := c.gain * env * (grain + ring)
			pan := c.pan + .17*(2*u-1)
			l += amp * math.Sqrt((1-pan)/2)
			r += amp * math.Sqrt((1+pan)/2)
		}
		for k, val := range []float64{l, r} {
			binary.LittleEndian.PutUint16(data[4*n+2*k:], uint16(int16(math.Round(val*30000))))
		}
	}
	return data
}
func check(err error) {
	if err != nil {
		panic(err)
	}
}
func main() {
	source, err := os.ReadFile("margin.go")
	check(err)
	notice, err := os.ReadFile("NOTICE.txt")
	check(err)
	var cells bytes.Buffer
	for f := 0; f < Frames; f++ {
		cells.Write(picture(float64(f) / FPS))
	}
	markers := []map[string]any{}
	lines := strings.Split(string(source), "\n")
	for _, s := range []struct {
		f      int
		needle string
	}{{0, "The ruling stays"}, {19, "func mesh("}, {70, "A registration cross"}, {95, "Two brisk strokes"}, {155, "for _, b := range beats"}, {227, "approach :="}, {270, "q := interp"}} {
		for i, line := range lines {
			if strings.Contains(line, s.needle) && !strings.Contains(line, "needle string") {
				markers = append(markers, map[string]any{"frame": s.f, "file": "source/margin.go", "line": i + 1})
				break
			}
		}
	}
	manifest, err := json.Marshal(map[string]any{"version": 1, "title": "The Margin of Error", "background": "#182e39", "cols": W, "rows": H, "fps": FPS, "frames": Frames, "sources": []string{"source/margin.go"}, "markers": markers, "audio": "audio.pcm"})
	check(err)
	f, err := os.Create("the-margin-of-error.rwl")
	check(err)
	z := zip.NewWriter(f)
	for _, m := range []struct {
		name string
		b    []byte
	}{{"manifest.json", manifest}, {"frames.bin", cells.Bytes()}, {"audio.pcm", score()}, {"source/margin.go", source}, {"NOTICE.txt", notice}} {
		w, err := z.Create(m.name)
		check(err)
		_, err = w.Write(m.b)
		check(err)
	}
	check(z.Close())
	check(f.Close())
	fmt.Println("the-margin-of-error.rwl")
}
