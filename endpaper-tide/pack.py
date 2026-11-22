from pathlib import Path
import json
from zipfile import ZipFile, ZIP_DEFLATED

root=Path(__file__).resolve().parent
title="Endpaper Tide"
sources=["tide.mjs"]
W,H,count,fps,bg=112,40,240,20,"#263639"
cues=[(0,0,"Pull the bath","const drift"),(58,0,"Neighbouring teeth","const wake"),
      (118,0,"Small eddies","return ink"),(183,0,"Mix four subcell","cell(x,y,'█',tone)")]
def line(file,phrase):
    return next(i for i,s in enumerate((root/file).read_text(encoding="utf-8").splitlines(),1) if phrase in s)
markers=[dict(frame=n,file="source/"+sources[i],line=line(sources[i],a),endLine=line(sources[i],b)) for n,i,a,b in cues]
header=dict(version=1,title=title,cols=W,rows=H,frames=count,fps=fps,background=bg,
            sources=["source/"+s for s in sources],markers=markers)

with ZipFile(root.parent / "player"/"artworks"/(root.name+".rwl"),"w",ZIP_DEFLATED) as z:
    z.writestr("manifest.json",json.dumps(header))
    for s in sources:z.write(root/s,"source/"+s)
    z.write(root.parent/"LICENSE","LICENSE.txt")
    raw=root/"frames.bin"
    if raw.stat().st_size!=W*H*count*5:raise ValueError("Regenerate frames with node tide.mjs frames.bin")
    z.write(raw,"frames.bin")
