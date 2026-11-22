"""An inclined spiral seen through a transiting dark moon."""
import numpy as np
from score import strikes

W, H, FRAMES, FPS = 118, 44, 512, 24
rng = np.random.default_rng(716)
# Braille dots have nearly square physical spacing in the player's 2:1 cells.
yy, xx = np.mgrid[:H*4, :W*2]
x = xx-W+8
y = yy-H*2-2
theta = -.31
u = x*np.cos(theta)+y*np.sin(theta)
v = (-x*np.sin(theta)+y*np.cos(theta)) / .49
radius = np.hypot(u,v)
azimuth = np.arctan2(v,u)
grain = rng.random(xx.shape)
stars = rng.random(xx.shape)
bits = np.array([[1,8],[2,16],[4,32],[64,128]])
background = np.array([8,12,28])
events = list(strikes())

def image(n):
    cycle = 2*np.pi*n/FRAMES
    beat = n/16
    # Three folded arms circle a pale, almond-shaped nucleus.
    twist = 3*azimuth - .108*radius - cycle
    arms = (.5+.5*np.cos(twist+.48*np.sin(azimuth*2+cycle)))**3
    halo = np.exp(-radius/33)
    density = (.13+1.85*arms)*halo + .85*np.exp(-(radius/13)**2)
    dust = (.5+.5*np.cos(twist-.70))**9
    density *= 1-.72*dust
    field = grain < density
    color = np.empty((*xx.shape,3))
    warm = np.exp(-radius/32)*.94+.24*arms
    for c,(blue,amber) in enumerate(zip((83,129,211),(255,186,112))):
        color[:,:,c] = blue+(amber-blue)*np.minimum(warm,1)
    # A pin of glass becomes a star; the pitch selects its position on the arm.
    for when,pitch,voice in events:
        age = (beat-when)%32
        if age>2: continue
        angle = when*2.39 + cycle + voice*.3
        distance = 24+(pitch-52)*2.8
        a,b = distance*np.cos(angle), .49*distance*np.sin(angle)
        sx,sy = a*np.cos(theta)-b*np.sin(theta), a*np.sin(theta)+b*np.cos(theta)
        dx,dy = np.abs(x-sx),np.abs(y-sy)
        light = np.exp(-2.7*age)
        glint = ((dx<.8)&(dy<1+7*light))|((dy<.8)&(dx<1+9*light))
        field |= glint
        color[glint] = [187+62*light,176+64*light,231]
    distant = stars > .9986
    field |= distant
    color[distant] = [121,148,191]
    # Transit erases the stars behind the moon. Only its sunward rim is lit.
    mx,my = -129*np.cos(cycle), 19*np.sin(cycle)
    dx,dy = x-mx,y-my
    limb = np.hypot(dx,dy)
    field &= limb>13
    crescent = (limb>=12.0)&(limb<=13.5)&(dx*.76+dy*.65 < -2)
    field |= crescent
    color[crescent] = [238,167,115]
    dots = field.reshape(H,4,W,2)
    masks = (dots*bits[None,:,None,:]).sum(axis=(1,3))
    colors = (color*field[:,:,None]).reshape(H,4,W,2,3).sum(axis=(1,3))
    colors /= np.maximum(1,dots.sum(axis=(1,3)))[:,:,None]
    cells = np.zeros((H,W),dtype=[('glyph','<u2'),('ink','u1',3)])
    cells['glyph'] = np.where(masks,0x2800+masks,32)
    cells['ink'] = np.where(masks[:,:,None]>0,colors,background)
    return cells.tobytes()

