"""A miniature proscenium. Units are Braille dot pitches: 168 across, 120 down."""
import math
import numpy as np
from PIL import Image, ImageDraw

W,H,FPS,N = 84,30,16,384
# Wall, plaster shadow, brass, warm lamp, suit, wool, velvet shadow, lining, skin, hair, shoe.
PALETTE=np.array([(120,102,109),(98,82,94),(186,145,94),(254,218,156),(38,40,55),
 (158,45,62),(102,36,55),(251,191,144),(224,164,134),(57,43,54),(41,34,43),
 (197,73,76),(211,180,157),(73,64,80)],dtype=np.uint8)
def ease(a,b,t):
    u=min(1,max(0,(t-a)/(b-a)))
    return u*u*(3-2*u)
def keys(t,*pairs):
    for (a,x),(b,y) in zip(pairs,pairs[1:]):
        if t<=b: return x+(y-x)*ease(a,b,t)
    return pairs[-1][1]
def trade(t):
    # The coat breaks the stalemate by taking the first travelling step.
    return keys(t,(0,0),(6.6,0),(7.3,-5),(8.3,-5),(9.6,-16),(10.1,-16),
                (11.55,2),(12,2),(13.4,16),(14,16),(15.55,-4),(16.2,-4),(17.8,-13),(19,0))
def gesture(t):
    hold=keys(t,(0,0),(0.6,0),(1.7,1),(18.85,1),(20.35,0))
    shake=keys(t,(0,0),(2.4,0),(2.63,-4),(2.90,4),(3.12,-3),(3.4,0))
    return hold,shake

def picture(t):
    im=Image.new('L',(336,240)); d=ImageDraw.Draw(im)
    def pts(p):return [(round(x*2),round(y*2)) for x,y in p]
    def poly(p,k):d.polygon(pts(p),fill=k)
    def line(p,k,w=1):d.line(pts(p),fill=k,width=max(1,round(w*2)),joint='curve')
    def oval(x,y,rx,ry,k):d.ellipse(pts([(x-rx,y-ry),(x+rx,y+ry)]),fill=k)
    def limb(p,k,w):
        line(p,k,w)
        for x,y in p[1:-1]:oval(x,y,w/2,w/2,k)
    # A rail of empty hooks, one burning sconce, a strip of parquet.
    line([(8,22),(157,22)],1,2);line([(9,20),(155,20)],2,1)
    for x in [24,48,72,96,120,144]:
        line([(x-2,23),(x-2,28),(x,30),(x+2,28)],2,1.3)
    for x in [9,159]:
        line([(x,40),(x,48)],2,1);poly([(x-3,39),(x-2,33),(x+2,33),(x+3,39)],3)
    line([(4,99),(164,99)],1,2)
    for x in range(-20,190,21):line([(x,115),(x+15,103)],1,.8)
    hold,shake=gesture(t)
    dance=ease(6.5,7.25,t)*(1-ease(18.2,19.25,t))
    phase=2*math.pi*(t-7)/1.5
    bow=keys(t,(0,0),(3.5,0),(4.4,1),(5.1,1),(6.05,0))
    step=trade(t)
    ax=52+step+keys(t,(0,0),(1,0),(2.4,6),(18.85,6),(20,14),(20.7,11),(22.3,-5),(23.93,0))
    cx=120+step-8*hold-18*dance
    bob=dance*1.8*math.cos(phase)
    drift=dance*2.5*math.sin(phase)
    lift=keys(t,(0,0),(6.3,0),(7.1,4),(18.4,4),(19.5,0))
    cy=32-lift+bob
    swing=dance*7*math.sin(phase-.8)
    hem=trade(t-.21)-step+swing
    turn=dance*(.5-.5*math.cos(phase*.5))**2
    # Shoes move before the body commits. One last tap after the music is over.
    toe=keys(t,(0,0),(5.05,0),(5.48,6),(5.95,6),(6.45,0))
    last=keys(t,(0,0),(22.35,0),(22.68,7),(22.87,7),(23.28,0))
    for side in [-1,1]:
        foot=ax+side*(5+7*dance*math.sin(phase))+(toe+last if side==1 else 0)
        fy=96-(4*dance*max(0,side*math.cos(phase))+(last*.52 if side==1 else 0))
        limb([(ax+side*3,69+bob),(ax+side*4+drift,84),(foot,fy)],4,4.4)
        poly([(foot-2,fy-2),(foot+2,fy-2),(foot+6,fy),(foot+5,fy+2),(foot-2,fy+2)],10)
        line([(foot+2,fy),(foot+5,fy)],12,.8)
    shoulder=(ax+2,50+bob+bow*2)
    # One hand keeps the coat-check ticket behind the attendant's back.
    limb([(ax-4,52+bob),(ax-11,64+bob),(ax-6,69+bob)],4,4)
    poly([(ax-9,66+bob),(ax-5,64+bob),(ax-3,69+bob),(ax-7,71+bob)],12)
    poly([(ax-6,49+bob),(ax+4,49+bob),(ax+7,61+bob),(ax+5,74+bob),
          (ax-2,72+bob),(ax-7,77+bob),(ax-6,61+bob)],4)
    poly([(ax-1,49+bob),(ax+4,50+bob),(ax+3,58+bob)],12)
    # Nose and chin change direction together; the shoes stay in the audience's sightline.
    # Pivot the whole profile around the nape; leave air below the forward jaw.
    hx=ax+1+4.5*bow;hy=38+bob+bow
    theta=.83*bow
    def head(x,y):
        return (hx+x*math.cos(theta)-y*math.sin(theta),hy+x*math.sin(theta)+y*math.cos(theta))
    limb([(ax,51+bob),head(-1,4)],8,3.8)
    poly([head(x,y) for x,y in [(-4,-4),(1,-6),(5,-3),(5,-1),(8,1),(5,2),(5,5),(2,7),(-3,5),(-5,0)]],8)
    poly([head(x,y) for x,y in [(-5,2),(-6,-4),(-3,-8),(1,-8),(4,-6),(5,-3),(0,-3),(-2,1)]],9)
    line([head(2,-1),head(4,-1)],10,1.15)
    # The near cuff is offered, shaken, then held out through an uncomfortable rest.
    cuffx=cx-10-17*hold
    cuffy=cy+30-10*hold+shake+dance*(2+2*math.sin(phase))
    reach=keys(t,(0,0),(1.18,0),(2.34,1),(18.95,1),(20.27,0))
    hand=(ax+6+(cuffx-(ax+6))*reach,67+bob+(cuffy-(67+bob))*reach)
    limb([shoulder,(ax+8+7*reach,63+bob-8*reach),hand],4,4.2)
    oval(*hand,2.6,1.9,8)
    # Empty collar and opening: the wall is visible straight through the neck.
    width=9-4*turn
    poly([(cx-5,cy),(cx+4,cy),(cx+width,cy+5),(cx+width-1,cy+20),
          (cx+12+hem,cy+49),(cx+2+hem,cy+53),(cx-12+hem,cy+50),(cx-6,cy+19),(cx-width,cy+5)],5)
    poly([(cx+1,cy+8),(cx+4,cy+20),(cx+10+hem,cy+49),(cx+2+hem,cy+52)],6)
    poly([(cx,cy+14),(cx+2,cy+31),(cx+hem+3,cy+52),(cx+hem-1-5*turn,cy+49)],7)
    poly([(cx-5,cy),(cx+4,cy),(cx,cy+6)],0)
    line([(cx-5,cy+1),(cx-3,cy+8),(cx,cy+6)],11,1.6)
    limb([(cx-width+1,cy+6),(cx-11-4*hold,cy+22-10*hold), (cuffx+2,cuffy)],5,5.4)
    line([(cuffx+1,cuffy-2),(cuffx+2,cuffy+2)],7,1.8)
    embrace=dance*(.5-.5*math.cos(phase*.25))**2
    far=((1-embrace)*(cx+9-dance*(13+8*math.cos(phase)))+embrace*(ax+7),
         (1-embrace)*(cy+31-dance*19)+embrace*(50+bob))
    limb([(cx+width-1,cy+5),(cx+14,cy+18-dance*10),far],6,4.6)
    line([(far[0]-1,far[1]),(far[0]+2,far[1]+1)],7,1)
    return np.asarray(im)

def cells(t):
    # Majority color makes the wool read as a mass; sparse edge coverage becomes dots.
    a=picture(t).reshape(H,4,2,W,2,2).transpose(0,3,1,4,2,5).reshape(H,W,8,4)
    freq=np.stack([(a==i).sum(axis=(2,3)) for i in range(len(PALETTE))],axis=-1)
    ink=1+freq[:,:,1:].argmax(axis=-1)
    mask=(a!=0).sum(axis=-1)>=2
    bits=(mask*np.array([1,8,2,16,4,32,64,128])).sum(axis=-1)
    glyph=np.where(bits==0,32,np.where(bits==255,0x2588,0x2800+bits))
    for b,g in [(192,0x2582),(228,0x2584),(246,0x2586),(27,0x2580)]:
        glyph[bits==b]=g
    # Braille masks contain space between every pair of dots. Use contiguous
    # ink for clothes and limbs; tint edge cells by actual covered area.
    figure=(a>=4)&(a<=12)
    covered=figure.sum(axis=(2,3))
    top=figure[:,:,:4,:].sum(axis=(2,3))
    bottom=covered-top
    solid=covered>=3
    lower=solid&(top<=1)&(bottom>=3)
    upper=solid&(bottom<=1)&(top>=3)
    glyph[solid]=0x2588
    glyph[lower]=0x2584
    glyph[upper]=0x2580
    ink=np.where(solid,4+freq[:,:,4:13].argmax(axis=-1),ink)
    rgb=PALETTE[np.where(bits,ink,0)].copy()
    alpha=np.minimum(1,(covered/np.where(lower|upper,16,32))**.70)
    rgb[solid]=np.rint(PALETTE[0]*(1-alpha[solid,None])+PALETTE[ink[solid]]*alpha[solid,None])
    out=np.empty((H,W,5),np.uint8)
    out[:,:,0]=glyph%256;out[:,:,1]=glyph//256;out[:,:,2:]=rgb
    return out.tobytes()

