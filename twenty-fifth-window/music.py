"""A shop-window waltz in three: music box, cello, and a little sleigh."""
import numpy as np
RATE, BEAT = 48000, 32000
# The treble lingers over the bar line while the parcels keep three steady beats.
BARS = [(50, (66,69,74)), (47,(73,69,66)), (43,(71,74,78)), (45,(76,73,69)),
        (50,(74,78,81)), (42,(78,76,73)), (43,(71,67,64)), (45,(69,73,76))]
def tune():
    for bar, (_, notes) in enumerate(BARS):
        for off, key in zip((0,1.5,2.25),notes):
            yield 3*bar+off,key

def score():
    samples = 24*BEAT
    mix = np.zeros((samples,2))
    def add(beat, wave, pan):
        pos = round(beat*BEAT)%samples
        sides = wave[:,None]*np.sqrt([1-pan,pan])
        head = min(len(wave),samples-pos)
        mix[pos:pos+head] += sides[:head]
        mix[:len(wave)-head] += sides[head:]
    for beat,key in tune():
        # A struck tooth rings twice: steel above, a wooden body underneath.
        t=np.arange(2*RATE)/RATE
        phase=2*np.pi*440*2**((key-69)/12)*t
        strike=(np.sin(phase)+.38*np.sin(2.007*phase)*np.exp(-3*t)+.20*np.sin(3.96*phase))
        tone=strike*(1-np.exp(-240*t))*np.exp(-3.4*t)*np.minimum(1,(2-t)*16)
        add(beat,.40*tone,.64)
        add(beat+.37,.065*tone,.25)
    for bar,(root,notes) in enumerate(BARS):
        # A low bowed downbeat and two short offbeats rock the tree.
        for step, key in enumerate((root,root+7,root+12)):
            t=np.arange(BEAT)/RATE
            phase=2*np.pi*440*2**((key-69)/12)*t
            env=np.sin(np.pi*np.arange(BEAT)/BEAT)**1.2*np.exp(-step*2*t)
            add(bar*3+step,.30*env*(np.sin(phase)+.22*np.sin(2*phase)),.32)
        # Sleigh bells shake on the pickup, then scatter into five metal partials.
        t=np.arange(RATE//3)/RATE
        bells=sum(np.sin(2*np.pi*f*t) for f in (2311,3109,3779,4583,5701))
        add(bar*3+2.5,.042*bells*np.exp(-19*t)*(1-np.exp(-330*t)),.8)
    return np.round(26300*mix/np.abs(mix).max()).astype('<i2')

