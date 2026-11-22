from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
from sky import image,W,H,FRAMES,FPS
from score import render

root = Path(__file__).resolve().parent
files = ['sky.py','score.py']
def cue(frame,file,first,last):
    lines=(root/file).read_text().splitlines()
    def locate(s):return next(i for i,line in enumerate(lines,1) if s in line)
    return dict(frame=frame,file='source/'+file,line=locate(first),endLine=locate(last))
markers=[
 cue(0,'sky.py','Three folded arms','field = grain'),
 cue(64,'score.py','Glass has a bright','place(beat, .34'),
 cue(128,'sky.py','Transit erases','color[crescent]'),
 cue(192,'score.py','At conjunction','place(4*bar+.25'),
 cue(256,'sky.py','A pin of glass','light = np.exp'),
 cue(320,'score.py','The bow opens','place(4*bar, .29'),
 cue(384,'sky.py','Transit erases','color[crescent]'),
 cue(448,'score.py','Wrap ringing tails','mix[:len(wave)-first]'),
]
header=dict(version=1,title='Umbra Choir',cols=W,rows=H,fps=FPS,frames=FRAMES,
 background='#080c1c',sources=['source/'+f for f in files],markers=markers,audio='audio.pcm')
with ZipFile(root.parents[1]/'artworks'/'umbra-choir.rwl','w',ZIP_DEFLATED) as z:
 z.writestr('manifest.json',json.dumps(header))
 for f in files:z.write(root/f,'source/'+f)
 z.write(root.parents[2]/'LICENSE','LICENSE.txt')
 z.writestr('audio.pcm',render().tobytes())
 with z.open('frames.bin','w') as out:
  for n in range(FRAMES):out.write(image(n))
