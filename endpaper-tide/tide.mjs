// Endpaper Tide. A travelling comb draws a feather through floating ink.
// Original JavaScript artwork, MIT, Copyright (c) 2026 Rari-One.
// Run with Node.js: node tide.mjs frames.bin
import fs from 'node:fs';

const width = 112, height = 40, frames = 240;
const tau = Math.PI * 2;
const paper = [230, 213, 173];
const ink = [[19,44,60],[62,113,111],[208,146,101],[190,70,52],
             [231,199,145],[36,65,76],[214,179,103],[108,139,123]];

function pigment(x, y, phase) {
  // Pull the bath sideways with a slow tide before it reaches the comb.
  const swell = Math.sin(tau*(y*.63-phase))*.09;
  const drift = x + swell + .035*Math.sin(tau*(2*y+phase));
  // Neighbouring teeth draw in opposite directions, leaving nested chevrons.
  const tooth = drift*2.65;
  const groove = Math.asin(.97*Math.sin(tau*tooth))/Math.PI;
  const wake = y + .71*groove + .08*Math.cos(tau*(drift*1.6-phase));
  // Small eddies bend the stripes around the eye of each peacock feather.
  const vein = 1.75*wake + .19*Math.sin(tau*(1.5*drift+.5*wake+phase));
  const band = ((vein%1)+1)%1;
  const edges = [.11,.28,.33,.43,.49,.73,.80,1];
  return ink[edges.findIndex(edge=>band<edge)];
}
function sheet(n) {
  const phase=n/frames, page=Buffer.alloc(width*height*5);
  function cell(x,y,ch,c) {
    const offset=5*(y*width+x);
    page.writeUInt16LE(ch.codePointAt(0),offset);
    for(let k=0;k<3;k++) page[offset+2+k]=c[k];
  }
  function lettering(x,y,word,c) {
    Array.from(word).forEach((ch,i)=>cell(x+i,y,ch,c));
  }
  for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
    // The deckle stays still. The ink swims all the way to its broken edge.
    const edge=.7*Math.sin(x*1.21)+.35*Math.cos(x*.89);
    const inside=x>2 && x<width-3 && y>1.5+edge && y<height-4+edge;
    if (!inside) { cell(x,y,'█',paper); continue; }
    // Mix four subcell samples to soften the tight inner curls of the comb.
    const samples=[];
    for (const dy of [.25,.75]) for (const dx of [.25,.75]) {
      samples.push(pigment((x+dx)/width,(y+dy)/height,phase));
    }
    const tone=[0,1,2].map(k=>Math.round(samples.reduce((sum,c)=>sum+c[k],0)/4));
    cell(x,y,'█',tone);
  }
  // A quiet colophon follows the paper, outside the bath.
  lettering(4,height-2,'ENDPAPER TIDE',[217,186,133]);
  lettering(width-21,height-2,'COMBED BY WATER',[217,186,133]);
  return page;
}
if (!process.argv[2]) throw Error('Supply an output path for the frame stream');
const fd=fs.openSync(process.argv[2],'w');
try { for(let n=0;n<frames;n++) fs.writeFileSync(fd,sheet(n)); }
finally { fs.closeSync(fd); }


