"""Run from anywhere. Writes may-i-have-my-coat.rwl next to this file."""
import json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from stage import cells,FPS,N,W,H
from pit import render
ROOT=Path(__file__).resolve().parent
def main():
    names=['stage.py','pit.py','pack.py']
    sources={'source/'+name:(ROOT/name).read_bytes() for name in names}
    markers=[]
    for frame,file,needle in [(0,'stage','A rail of empty hooks'),(24,'stage','near cuff is offered'),
       (53,'pit',"handshake's aftermath"),(71,'stage','Nose and chin'),(82,'stage','Shoes move before'),
       (110,'stage','coat breaks the stalemate'),(170,'pit','Eight two-beat bars'),
       (208,'stage','embrace=dance'),(269,'stage','Empty collar'),(348,'pit','last step belongs')]:
        path='source/'+file+'.py'
        line=next(i for i,v in enumerate(sources[path].decode().splitlines(),1) if needle in v)
        markers.append(dict(frame=frame,file=path,line=line))
    meta=dict(version=1,title='May I Have My Coat?',cols=W,rows=H,fps=FPS,frames=N,
              background='#78666d',audio='audio.pcm',sources=list(sources),markers=markers)
    members={'manifest.json':json.dumps(meta,separators=(',',':')).encode(),
             'frames.bin':b''.join(cells(f/FPS) for f in range(N)),
             'audio.pcm':render(),**sources,'NOTICE.txt':(ROOT/'NOTICE.txt').read_bytes()}
    with ZipFile(ROOT/'may-i-have-my-coat.rwl','w') as out:
        for name,data in members.items():
            item=ZipInfo(name);item.create_system=3;item.external_attr=0o100644<<16
            out.writestr(item,data,compress_type=ZIP_DEFLATED,compresslevel=9)
if __name__=='__main__':main()

