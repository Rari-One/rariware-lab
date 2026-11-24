"""The wardrobe's pit orchestra: a bellows duet, gut bass and wood heels."""
import numpy as np

RATE=48000
def render():
    mix=np.zeros((24*RATE,2))
    rng=np.random.default_rng(119)
    def place(at,s,pan):
        i=round(at*RATE); n=min(len(s),len(mix)-i)
        mix[i:i+n]+=s[:n,None]*np.sqrt([(1-pan)/2,(1+pan)/2])
    def reed(at,note,length,vol,pan=.34):
        t=np.arange(round(length*RATE))/RATE
        hz=440*2**((note-69)/12)
        env=(1-np.exp(-t/.052))*(1-np.exp(-(length-t)/.085))
        phase=2*np.pi*hz*t+.12*np.sin(2*np.pi*5*t)
        tone=sum(np.sin(h*phase)*a for h,a in [(1,.74),(2,.29),(3,.27),(5,.15),(7,.08)])
        twin=np.sin(phase*1.004)+.20*np.sin(3*phase*1.004)
        place(at,vol*env*(.82+.18*np.sin(np.pi*t/length))*(tone*.8+twin*.25),pan)
    def pluck(at,note,vol):
        t=np.arange(RATE)/RATE; p=2*np.pi*440*2**((note-69)/12)*t
        voice=sum(np.sin(p*h)*np.exp(-t*(4+2*h))/h for h in (1,2,3,4,6))
        place(at,vol*(1-np.exp(-t/.004))*voice,-.38)
    def shoe(at,vol,pan):
        t=np.arange(4500)/RATE
        sand=rng.normal(0,1,len(t))
        wood=np.sin(2*np.pi*(176*t+1.4*(1-np.exp(-28*t))))+.37*np.sin(2*np.pi*801*t)
        place(at,vol*(wood*np.exp(-52*t)+.4*sand*np.exp(-180*t))*(1-np.exp(-t/.001)),pan)
    reed(1.12,65,1.12,.13);reed(2.29,64,.75,.095);shoe(2.72,.065,-.38)
    # Keep the handshake's aftermath empty. The first shoe asks a question.
    shoe(5.48,.115,-.42);pluck(6.57,45,.13)
    # Eight two-beat bars: the reed holds across the dancers' accented heel.
    melody=[[(0,65,.94),(.99,64,.40)],[(.13,62,.62),(.83,69,.57)],
            [(0,68,.43),(.52,69,.86)],[(0,72,1.27)],
            [(0,70,.38),(.46,69,.38),(.94,65,.51)],[(.08,64,1.15)],
            [(0,62,.60),(.73,61,.61)],[(0,62,1.37)]]
    for bar,root in enumerate([38,45,41,36,43,40,45,38]):
        at=7+1.5*bar
        pluck(at,root,.24);pluck(at+.85,root+7,.13)
        shoe(at+.37,.13,-.32);shoe(at+1.12,.085,-.17)
        for off,n,dur in melody[bar]:reed(at+off,n,dur,.155)
        if bar in (2,4,7):reed(at+.04,melody[bar][0][1]-4,.69,.052,.04)
    shoe(19.42,.075,.55)
    # The last step belongs to the attendant, after the orchestra has packed up.
    shoe(22.70,.095,-.48)
    return np.rint(28000*mix).clip(-32768,32767).astype('<i2').tobytes()

