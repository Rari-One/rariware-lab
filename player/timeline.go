package main

import (
	"fmt"

	e "github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/text"
	"github.com/hajimehoshi/ebiten/v2/vector"
)

type timeline struct{ left, right, y int }

func (g *player) timeline() timeline {
	return timeline{g.left() + 168, g.w - 14, g.split() - 22}
}

func (t timeline) frameX(frame, count int) int {
	return t.left + (frame*(t.right-t.left)+(count-1)/2)/max(1, count-1)
}

func (t timeline) frameAt(x int, p piece, snap bool) int {
	x = min(t.right, max(t.left, x))
	width := t.right - t.left
	frame := ((x-t.left)*(p.count-1) + width/2) / width
	if snap && x != t.left && x != t.right {
		best := 5
		for _, m := range p.markers {
			d := x - t.frameX(m.Frame, p.count)
			if d < 0 {
				d = -d
			}
			if d < best {
				best, frame = d, m.Frame
			}
		}
	}
	return frame
}

func (g *player) updateScrub(x int, held, first bool) error {
	if first || x != g.scrubX {
		frame := g.timeline().frameAt(x, pieces[g.id], first)
		if err := g.seekFrame(frame); err != nil {
			return err
		}
		g.scrubX = x
	}
	if !held {
		g.scrubbing = false
		if g.resumeAfterScrub {
			g.togglePause()
		}
	}
	return nil
}

func clockLabel(frames, fps int) string {
	tenths := frames * 10 / fps
	return fmt.Sprintf("%d:%02d.%d", tenths/600, tenths/10%60, tenths%10)
}

func (g *player) drawTimeline(s *e.Image) {
	colors := g.colors()
	ink, accent := colors.ink, colors.accent
	t, p := g.timeline(), pieces[g.id]
	frame := g.frame()
	label := clockLabel(frame, p.fps) + " / " + clockLabel(p.count, p.fps)
	text.Draw(s, label, g.face, g.left()+6, t.y+5, ink)
	vector.DrawFilledRect(s, float32(t.left), float32(t.y), float32(t.right-t.left+1), 2, colors.divider, false)
	for _, m := range p.markers {
		vector.DrawFilledRect(s, float32(t.frameX(m.Frame, p.count)), float32(t.y-6), 2, 7, ink, false)
	}
	vector.DrawFilledRect(s, float32(t.frameX(frame, p.count)-2), float32(t.y-4), 5, 10, accent, false)
}
