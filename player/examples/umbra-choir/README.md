# Umbra Choir

A dark moon passes across an inclined spiral galaxy. In sky.py, an elliptical coordinate transform tilts the disk. A radial twist produces three arms, fixed seeded grain distributes the stars, and a moving mask removes the dots behind the moon. The remaining rim catches the warm core light.

In score.py, eight bars of glass tones ring over a bowed bass. Each strike also supplies a time and pitch to the sky, so the same event places a flash on a spiral arm. At 24 fps each beat lasts 16 frames. The 512-frame loop lasts 21⅓ seconds. Stereo tails wrap into the opening. Follow moves between the glass envelope, the transit mask, the bow and the wrapping tails.

## Regenerate

Use Python 3.10+ with NumPy. The packer generates the seeded scene, renders both audio channels and includes both Python listings. From the repository root:

```sh
cd player/examples/umbra-choir
python -m pip install numpy
python pack.py
```

The result replaces [the playable package](../../artworks/umbra-choir.rwl). Relaunch the player to see your changes. Original code and artwork use the repository’s [MIT license](../../../LICENSE).
