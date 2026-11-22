from pathlib import Path
import json
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parent

from scene import paint,W,H
from music import score
title="The Twenty-Fifth Window"
sources=["scene.py","music.py"]
count,fps,bg=384,24,"#0c1524"
cues=[(0,0,"Snow moves behind","put(round(xx)"),(48,1,"A struck tooth","add(beat,.40"),
      (144,0,"Light chases","pulse=math.exp"),(192,1,"A low bowed","add(bar*3+step"),
      (288,0,"A little forest","word(x+w//2"),(336,1,"Sleigh bells shake","add(bar*3+2.5")]
def line(file,phrase):
    return next(i for i,s in enumerate((root/file).read_text(encoding="utf-8").splitlines(),1) if phrase in s)
markers=[dict(frame=n,file="source/"+sources[i],line=line(sources[i],a),endLine=line(sources[i],b)) for n,i,a,b in cues]
header=dict(version=1,title=title,cols=W,rows=H,frames=count,fps=fps,background=bg,
            sources=["source/"+s for s in sources],markers=markers)
header["audio"]="audio.pcm"
with ZipFile(root.parents[1]/"artworks"/(root.name+".rwl"),"w",ZIP_DEFLATED) as z:
    z.writestr("manifest.json",json.dumps(header))
    for s in sources:z.write(root/s,"source/"+s)
    z.write(root.parents[2]/"LICENSE","LICENSE.txt")
    z.writestr("audio.pcm",score().tobytes())
    with z.open("frames.bin","w") as out:
        for n in range(count):out.write(paint(n))
