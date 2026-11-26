package main

import (
	"archive/zip"
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"unicode"
	"unicode/utf8"
)

type marker struct {
	Frame, Line, EndLine int
	File                 string
}
type manifest struct {
	Version, Cols, Rows, FPS, Frames int
	Title, Background, Audio         string
	Sources                          []string
	Markers                          []marker
}
type piece struct {
	name, path       string
	w, h, fps, count int
	bg               [3]byte
	sources          []string
	markers          []marker
}
type loaded struct {
	piece
	raw, pcm []byte
	lines    [][]string
}

var pieces []piece

func readPackage(path string) (loaded, error) {
	var out loaded
	bad := fmt.Errorf("invalid or oversized package")
	st, err := os.Lstat(path)
	if err != nil || !st.Mode().IsRegular() || st.Size() > 16<<20 {
		return out, bad
	}
	z, err := zip.OpenReader(path)
	if err != nil {
		return out, err
	}
	defer z.Close()
	if len(z.File) > 12 {
		return out, bad
	}
	files := map[string]*zip.File{}
	for _, f := range z.File {
		if !fs.ValidPath(f.Name) || strings.ContainsAny(f.Name, "\\:") || files[f.Name] != nil || !f.Mode().IsRegular() {
			return out, bad
		}
		files[f.Name] = f
	}
	read := func(name string, limit int) ([]byte, error) {
		f := files[name]
		if f == nil || f.UncompressedSize64 > uint64(limit) {
			return nil, bad
		}
		r, e := f.Open()
		if e != nil {
			return nil, e
		}
		defer r.Close()
		b, e := io.ReadAll(io.LimitReader(r, int64(limit+1)))
		if len(b) > limit {
			return nil, bad
		}
		return b, e
	}
	b, err := read("manifest.json", 65536)
	var m manifest
	if err != nil || json.Unmarshal(b, &m) != nil || m.Version != 1 || len(m.Title) > 80 || strings.TrimSpace(m.Title) == "" || strings.IndexFunc(m.Title, unicode.IsControl) >= 0 || m.Cols < 1 || m.Cols > 160 || m.Rows < 1 || m.Rows > 60 || m.FPS < 1 || m.FPS > 60 || m.Frames < 1 || m.Frames > 900 || len(m.Sources) > 8 || len(m.Markers) > 1024 {
		return out, bad
	}
	bg, e := hex.DecodeString(strings.TrimPrefix(m.Background, "#"))
	if e != nil || len(bg) != 3 {
		return out, bad
	}
	out.piece = piece{m.Title, path, m.Cols, m.Rows, m.FPS, m.Frames, [3]byte(bg), m.Sources, m.Markers}
	size := m.Cols * m.Rows * m.Frames * 5
	if size > 24<<20 {
		return out, bad
	}
	out.raw, err = read("frames.bin", size)
	if err != nil || len(out.raw) != size {
		return out, bad
	}
	for i := 0; i < size; i += 5 {
		v := rune(binary.LittleEndian.Uint16(out.raw[i:]))
		if unicode.IsControl(v) || !utf8.ValidRune(v) {
			return out, bad
		}
	}
	if m.Audio != "" {
		if m.Audio != "audio.pcm" {
			return out, bad
		}
		samples := 48000 * m.Frames
		if samples%m.FPS != 0 {
			return out, bad
		}
		length := samples / m.FPS * 4
		if length > 12<<20 {
			return out, bad
		}
		out.pcm, err = read(m.Audio, length)
		if err != nil || len(out.pcm) != length {
			return out, bad
		}
	}
	counts := map[string]int{}
	for _, s := range m.Sources {
		if !strings.HasPrefix(s, "source/") || counts[s] != 0 || len(s) > 160 || strings.IndexFunc(s, unicode.IsControl) >= 0 {
			return out, bad
		}
		b, e := read(s, 256<<10)
		if e != nil || !utf8.Valid(b) || bytes.ContainsRune(b, 0) {
			return out, bad
		}
		lines := strings.Split(strings.ReplaceAll(string(b), "\r\n", "\n"), "\n")
		if len(lines) > 12000 {
			return out, bad
		}
		out.lines = append(out.lines, lines)
		counts[s] = len(lines)
	}
	for i, mk := range m.Markers {
		if mk.Frame < 0 || mk.Frame >= m.Frames || mk.Line < 1 || mk.Line > counts[mk.File] || (mk.EndLine != 0 && (mk.EndLine < mk.Line || mk.EndLine > counts[mk.File])) || (i > 0 && mk.Frame <= m.Markers[i-1].Frame) {
			return out, bad
		}
	}
	return out, nil
}
func discover(dir string) (skipped int, err error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		// Windows can report a missing path when an ordinary file occupies
		// the directory's location.
		if st, statErr := os.Stat(dir); statErr == nil && !st.IsDir() {
			return 0, fmt.Errorf("%s is not a directory", dir)
		}
		return 0, err
	}
	for _, f := range entries {
		if !strings.EqualFold(filepath.Ext(f.Name()), ".rwl") {
			continue
		}
		if len(pieces)+skipped >= 128 {
			skipped++
			continue
		}
		p, e := readPackage(filepath.Join(dir, f.Name()))
		if e != nil {
			skipped++
			continue
		}
		pieces = append(pieces, p.piece)
	}
	return
}
