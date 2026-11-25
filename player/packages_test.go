package main

import (
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestRepositoryPackages loads every .rwl in the repository (and in RWL_DIR,
// when set) with the player's own loader.
func TestRepositoryPackages(t *testing.T) {
	roots := []string{".."}
	if extra := os.Getenv("RWL_DIR"); extra != "" {
		roots = append(roots, extra)
	}
	found := 0
	for _, root := range roots {
		err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return err
			}
			if d.IsDir() && d.Name() == ".git" {
				return filepath.SkipDir
			}
			if !d.IsDir() && strings.EqualFold(filepath.Ext(path), ".rwl") {
				found++
				if _, e := readPackage(path); e != nil {
					t.Errorf("%s: %v", path, e)
				}
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	if found == 0 {
		t.Fatal("no packages found")
	}
}
