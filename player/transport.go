package main

import (
	"bytes"
	"github.com/hajimehoshi/ebiten/v2/audio"
	"time"
)

func openTrack(data []byte) (*audio.Player, error) {
	if len(data) == 0 {
		return nil, nil
	}
	ctx := audio.CurrentContext()
	if ctx == nil {
		ctx = audio.NewContext(48000)
	}
	stream := audio.NewInfiniteLoop(bytes.NewReader(data), int64(len(data)))
	return ctx.NewPlayer(stream)
}
func (g *player) stopTrack() {
	if g.sound != nil {
		g.sound.Pause()
		g.sound.Close()
		g.sound = nil
	}
}
func (g *player) togglePause() {
	g.since = g.elapsed()
	g.paused = !g.paused
	g.start = time.Now()
	if g.sound != nil {
		if g.paused {
			g.sound.Pause()
		} else {
			g.sound.Play()
		}
	}
}
func (g *player) restart() error {
	if g.sound != nil {
		if err := g.sound.SetPosition(0); err != nil {
			return err
		}
	}
	g.since = 0
	g.start = time.Now()
	return nil
}
