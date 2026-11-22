"""The Twenty-Fifth Window. Evergreen, blown glass, folded paper, and falling snow."""
import math
import random
import struct
from music import tune
W,H=116,46
rng=random.Random(1225)
snow=[(rng.randrange(W),rng.randrange(39),rng.choice([1,2,3])) for _ in range(210)]
lights=[(244,68,65),(255,190,67),(76,201,211),(230,104,175),(132,215,106)]
arrivals=list(tune())
def width(y):
    # Each new tier overhangs the previous tier like a layered paper cutting.
    return max((2+(y-start)*slope for start,end,slope in
                [(5,14,1.36),(9,21,1.55),(14,28,1.73),(20,35,1.80),(25,39,2.40)]
                if start<=y<=end),default=0)
def paint(n):
    beat=n/16
    grid=[[(' ',(12,21,36))]*W for _ in range(H)]
    def put(x,y,ch,col):
        if 0<=x<W and 0<=y<H:grid[y][x]=(ch,col)
    def word(x,y,s,col):
        for i,ch in enumerate(s):put(x+i,y,ch,col)
    # Snow moves behind the window lead, with a different drift for each depth.
    for x,y,k in snow:
        yy=(y+39*k*n/384)%39
        xx=x+2*math.sin(2*math.pi*n/384+y)
        put(round(xx),int(yy),'·' if k==1 else '∙',(61+12*k,83+14*k,106+15*k))
    for y in range(40):
        for x in (13,14,99,100):put(x,y,'│',(78,65,66))
    for x in range(W):
        for y in (13,30):put(x,y,'─',(74,66,70))
        put(x,40,'▀',(178,130,90))
    for y in range(5,40):
        span=width(y)
        for x in range(math.ceil(58-span),math.floor(59+span)):
            dx=x-58
            # Needle clusters alternate blue shadow and warm fir on the leading edges.
            shade=.5+.5*math.sin(1.1*y+.21*abs(dx)+.6*math.sin(dx*.51))
            grain=(x*71+y*39+x*y*11)%23
            edge=abs(dx)>span-1.7
            ch=('▴' if edge else '█') if grain>5 else '▇'
            put(x,y,ch,(int(15+15*shade),int(55+49*shade+9*edge),int(45+25*shade)))
    # Light chases the melody across five chains of hand-blown baubles.
    beat0,key=max(((b,k) for b,k in arrivals if b<=beat),default=arrivals[0])
    pulse=math.exp(-3*(beat-beat0))
    for ring,(row,span) in enumerate(((10,6),(16,12),(22,17),(28,21),(34,27))):
        for i in range(-span,span+1):
            y=row+round(2*math.cos(i/span*math.pi/2)+.7*math.sin(.22*i+ring))
            col=lights[(i//4+ring)%5]
            glow=.52+.40*(.5+.5*math.cos(i*.25-beat*math.pi/1.5))+.08*pulse
            if (i+span)%4==0:
                put(58+i,y,'●',tuple(int(v*glow) for v in col))
                if (i+ring+span)%3==0:put(58+i,y+1,'◆',col)
            else:put(58+i,y,'·',(211,165,80))
    gold=(255,round(202+41*pulse),127)
    for y,s in enumerate(('   │   ','  ╲│╱  ','───◆───','  ╱│╲  ','   │   ')):
        for x,ch in enumerate(s):
            if ch!=' ':put(55+x,1+y,ch,gold)
    # A little forest of presents hides the foot of the tree.
    for x,y,w,h,col,ribbon in [(22,38,14,5,lights[0],lights[1]),(80,37,11,6,lights[2],gold),
            (40,39,13,4,lights[3],gold),(61,37,12,6,(172,52,68),lights[1]),(73,41,9,3,lights[1],lights[0]),
            (33,41,9,3,(74,148,119),gold),(50,41,10,3,lights[2],lights[3])]:
        for yy in range(h):
            for xx in range(w):
                color=ribbon if xx==w//2 or yy==1 else tuple(int(v*(.7+.2*(xx%3==0))) for v in col)
                put(x+xx,y+yy,'█',color)
        word(x+w//2-1,y-1,'◁◆▷',ribbon)
    for side in (-1,1):
        for y in range(40):
            fringe=round(7+8*(1+math.cos(y*math.pi/25))/2+3*math.exp(-((y-36)/5)**2))
            for i in range(fringe):
                c=(100+int(45*math.cos(i*.86)),28,46)
                put(i if side<0 else W-1-i,y,'█',gold if y==25 else c)
    word(3,44,'THE TWENTY-FIFTH WINDOW',(219,186,143))
    word(95,44,'DECEMBER  /  25',(219,186,143))
    return b''.join(struct.pack('<HBBB',ord(ch),*rgb) for line in grid for ch,rgb in line)

