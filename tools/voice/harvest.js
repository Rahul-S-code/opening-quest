// Collects every fixed sentence Grandpa Rook can say, as the page splits them, and writes lines.json.
const {chromium}=require('playwright');const fs=require('fs');
const page=process.argv[2]||'/mnt/project-files/opening-quest/src/opening-quest.html';
(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+page);await p.waitForTimeout(1200);
const out=await p.evaluate(()=>{
 const SKIP=new Set(['m','san','r','rsan','glow','show','rshow','icon','tag','color','lvl','name','summary','idea','id','setup','sol','title']);
 const per={};const add=(t,opp,src)=>{if(typeof t!=='string'||!/\s/.test(t))return;t=t.replace(/\{O\}/g,opp);
   for(let s of (t.match(/[^.!?]+[.!?]+['"”]?\s*|[^.!?]+$/g)||[t])){s=s.trim().replace(/\s+/g,' ');if(s.length<2)continue;(per[s]=per[s]||new Set()).add(src);}};
 const walk=(o,opp,src)=>{if(typeof o==='string')return add(o,opp,src);if(Array.isArray(o))return o.forEach(x=>walk(x,opp,src));
   if(o&&typeof o==='object')for(const k in o)if(!SKIP.has(k))walk(o[k],opp,src);};
 for(const id in LESSONS){const L=LESSONS[id],opp=L.color==='w'?'Black':'White';walk(L,opp,id);walk(VOICES[id],opp,id);walk(EXTRA[id],opp,id);
   BRIDGES.forEach(f=>add(f(L.name),opp,id));}
 for(const opp of ['White','Black']){walk(G,opp,'common');walk(PRAISE,opp,'common');walk(QUICK_LINES,opp,'common');walk(CHEER,opp,'common');}
 TRAPS.forEach(t=>walk(t,t.color==='w'?'Black':'White','traps'));
 return Object.entries(per).map(([s,src])=>({s,src:[...src]}));});
fs.writeFileSync('lines.json',JSON.stringify(out));
const chars=out.reduce((a,x)=>a+x.s.length,0);
console.log('sentences',out.length,'chars',chars);
const italian=out.filter(x=>x.src.includes('italian'));console.log('italian only:',italian.length,italian.reduce((a,x)=>a+x.s.length,0));
await b.close();})();
