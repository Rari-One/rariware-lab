# May I Have My Coat?

The last coat in the cloakroom offers its empty sleeve. The attendant shakes it and waits. Watch the shoes: the first sideways step is a question, and the last heel tap comes after the orchestra has finished.

[Play the standalone package](may-i-have-my-coat.rwl) by copying it to the Lab Player’s artworks/ directory and reopening the player. Try one loop muted, then listen for the eight-bar exchange between the reed, plucked string and heels. The piece runs for 24 seconds at 16 FPS on an 84 × 30 grid. Ten optional source markers follow the invitation, dance and last step.

## Regenerate

From this directory, with Python 3.12 (tested on 3.12.14):

```sh
python -m pip install Pillow==13.0.0 numpy==2.3.5
python pack.py
```

Dependency installation may use the network. Generation runs offline, reads the three Python listings and NOTICE.txt, and replaces may-i-have-my-coat.rwl beside them. [stage.py](stage.py) uses hand-posed joints, a delayed hem and shaded character cells. [pit.py](pit.py) synthesizes the full stereo score. [pack.py](pack.py) assembles both into a v1 package.

Credit: RariWare Lab, created with OpenAI Codex. The original source is contributed under the [repository MIT license](../LICENSE). The figures, choreography, music and sound effects were created for this piece. No external artwork or recordings are included. The package preserves its [original candidate notice](NOTICE.txt). Website exhibition requires separate rights documentation and publication approval.
