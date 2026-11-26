package main

import (
	"bytes"
	"embed"
	"image"
	"image/png"

	e "github.com/hajimehoshi/ebiten/v2"
)

//go:generate rsrc -arch amd64 -ico identity/lab-player.ico -o icon_windows_amd64.syso

//go:embed identity/*.png
var identity embed.FS

func identityImage(name string) image.Image {
	data, err := identity.ReadFile("identity/" + name + ".png")
	if err != nil {
		panic(err)
	}
	img, err := png.Decode(bytes.NewReader(data))
	if err != nil {
		panic(err)
	}
	return img
}

var labMark = e.NewImageFromImage(identityImage("mark-lab"))
var ideMark = e.NewImageFromImage(identityImage("mark-ide"))

func setWindowIcon() {
	e.SetWindowIcon([]image.Image{
		identityImage("icon-16"), identityImage("icon-32"),
		identityImage("icon-48"), identityImage("icon-256"),
	})
}
