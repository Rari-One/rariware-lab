package main

import (
	"testing"
	"time"
)

func TestEditorialRange(t *testing.T) {
	pieces = []piece{{fps: 10, count: 12, markers: []marker{{Frame: 2, Line: 3, EndLine: 7}, {Frame: 8, Line: 15}}}}
	g := player{view: view{paused: true, lines: [][]string{make([]string, 50)}, follow: true}}
	for n, want := range map[int]int{2: 3, 5: 5, 7: 7, 8: 15, 11: 15, 14: 3} {
		g.since = time.Duration(n) * 100 * time.Millisecond
		m := g.activeMarker()
		if m == nil || m.Line != want {
			t.Fatal(n, m)
		}
	}
	g.sourceScroll(1)
	if g.follow {
		t.Fatal("manual scroll must take precedence")
	}
}
