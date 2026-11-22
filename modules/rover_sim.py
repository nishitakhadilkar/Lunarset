"""Interactive rover simulation, rendered as one self-contained HTML component."""
import json

FAC_META = {
    "Landing Zone": dict(type="Landing & unloading pad", w=0, desc="Cleared, level pad where cargo landers touch down and unload. Start point of all rover traverses.", dims="Pad Ø ≈ 40 m (conceptual)"),
    "Lunar Habitat": dict(type="Pressurised crew habitat", w=215, desc="Central habitation dome with four living modules, an airlock, connecting tunnels, external equipment bays and antenna links.", dims="Span ≈ 26 m (conceptual)"),
    "Agricultural Lab": dict(type="Controlled greenhouse", w=175, desc="Pressurised hydroponic greenhouse with growth chambers, lighting, environmental control and an airlock. A controlled-environment concept, not lunar-soil farming.", dims="Dome Ø ≈ 14 m (conceptual)"),
    "Solar Power Station": dict(type="Power generation & storage", w=200, desc="Tilted solar arrays, power-distribution unit, battery storage and structural supports feeding the habitat.", dims="Array ≈ 20 m (conceptual)"),
    "Communication Station": dict(type="Comms & relay mast", w=88, desc="High-gain dish on a lattice mast with relay equipment and its own power unit.", dims="Mast height ≈ 9 m (conceptual)"),
    "Resource Zone": dict(type="Resource investigation zone", w=0, desc="Candidate area for water-resource investigation. Radar/spectral indicators do not confirm accessible water ice.", dims="Zone Ø ≈ 50 m (conceptual)"),
}

def build_html(nav, facilities, terrain_b64, sprites_b64, cell_m=10):
    fac = []
    for name, f in facilities.items():
        m = FAC_META[name]
        fac.append(dict(name=name, pos=list(f["pos"]), key=f["key"], sprite=f["sprite"], **m))
    data = dict(craters=nav["craters"], routes=nav["routes"], fac=fac, cell=cell_m,
                terrain="data:image/jpeg;base64," + terrain_b64,
                sprites={k: "data:image/png;base64," + v for k, v in sprites_b64.items()})
    return HTML.replace("__DATA__", json.dumps(data))

HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<style>
*{box-sizing:border-box}
html,body{margin:0;background:#080D19;color:#E6EBF5;font-family:Inter,Segoe UI,system-ui,sans-serif;height:100%}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:12px;height:100%}
@media(max-width:900px){.wrap{grid-template-columns:1fr;height:auto}}
.stage{position:relative;border:1px solid #2B3B58;border-radius:14px;overflow:hidden;background:#05080f;align-self:start}
canvas{display:block;width:100%;height:auto}
.hud{position:absolute;left:10px;top:10px;display:flex;gap:6px;flex-wrap:wrap}
.chip{background:rgba(8,13,25,.82);border:1px solid #34445D;border-radius:999px;padding:4px 10px;font-size:11px;letter-spacing:.06em;color:#AAB7CC}
.chip b{color:#F4B855}
.tools{position:absolute;right:10px;top:10px;display:flex;gap:6px}
.tools label{background:rgba(8,13,25,.82);border:1px solid #34445D;border-radius:999px;padding:4px 10px;font-size:11px;color:#AAB7CC;cursor:pointer;user-select:none}
.tools input{accent-color:#F4B855;vertical-align:middle;margin-right:4px}
#toast{position:absolute;left:50%;top:14px;transform:translate(-50%,-140%);transition:transform .5s cubic-bezier(.2,.9,.3,1.2);
 background:linear-gradient(135deg,#123a2a,#0f2a44);border:1px solid #56e39f;border-radius:14px;padding:12px 16px;min-width:340px;max-width:92%;
 box-shadow:0 10px 40px rgba(0,0,0,.6);text-align:center;z-index:5}
#toast.show{transform:translate(-50%,30px)}
#toast h4{margin:0 0 2px;color:#7dffb8;font-size:14px;letter-spacing:.08em}
#toast p{margin:0 0 8px;font-size:12px;color:#c9d6ea}
.chips{display:flex;gap:6px;justify-content:center;flex-wrap:wrap}
.btn{background:#D99A32;color:#101827;border:0;border-radius:8px;padding:7px 11px;font-weight:700;font-size:12px;cursor:pointer}
.btn:hover{filter:brightness(1.1)}.btn.ghost{background:#14233B;color:#E6EBF5;border:1px solid #3a4d6e}
.btn.go{background:#35d58a}.btn:disabled{opacity:.4;cursor:not-allowed}
.panel{overflow-y:auto;display:flex;flex-direction:column;gap:10px;max-height:100%;padding-right:2px}
.card{background:#101B30;border:1px solid #2B3B58;border-radius:12px;padding:12px}
.card h3{margin:0 0 8px;font-size:11px;letter-spacing:.14em;color:#F4B855;font-weight:700}
.row{display:flex;justify-content:space-between;font-size:12.5px;padding:3px 0;color:#C7D0E0}
.row b{color:#fff;font-weight:600}
.bar{height:8px;background:#1b2a44;border-radius:6px;overflow:hidden;margin:6px 0}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#4fd8ff,#35d58a)}
.dest{display:flex;justify-content:space-between;align-items:center;width:100%;margin:3px 0;padding:7px 10px;background:#14233B;border:1px solid #2f4366;border-radius:8px;color:#E6EBF5;font-size:12px;cursor:pointer;text-align:left}
.dest:hover{border-color:#F4B855}.dest.sel{border-color:#F4B855;background:#2a2414}.dest.cur{opacity:.45;cursor:default}
.dest small{color:#8fa0bb}.ok{color:#56e39f}
table{width:100%;border-collapse:collapse;font-size:11.5px}th,td{padding:3px 4px;text-align:left;border-bottom:1px solid #1f2d47}th{color:#8fa0bb;font-weight:600}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:10.5px;font-weight:700}
.LOW{background:#12402c;color:#6dffb0}.MODERATE{background:#4a3a10;color:#ffd166}.ELEVATED{background:#4a1c1c;color:#ff8c8c}
#log{font:11px ui-monospace,Menlo,monospace;color:#9fb0cc;max-height:110px;overflow:auto}#log div{padding:1px 0}#log span{color:#4fd8ff}
.note{font-size:10.5px;color:#8392ad;line-height:1.4}
.comp{display:flex;align-items:center;gap:12px}
</style></head><body>
<div class="wrap">
 <div class="stage">
  <canvas id="cv"></canvas>
  <div class="hud"><span class="chip">MET <b id="met">00:00:00</b></span><span class="chip">ROVER <b id="rstate">IDLE</b></span><span class="chip">SCALE <b>1 cell = __CELL__ m</b></span></div>
  <div class="tools"><label><input type="checkbox" id="tHaz" checked>Hazards</label><label><input type="checkbox" id="tNet" checked>Route network</label></div>
  <div id="toast"><h4 id="tt"></h4><p id="tp"></p><div class="chips" id="tc"></div></div>
 </div>
 <div class="panel">
  <div class="card"><h3>ROVER TELEMETRY</h3>
   <div class="comp">
    <svg width="74" height="74" viewBox="-37 -37 74 74"><circle r="34" fill="#0b1426" stroke="#34445D"/><text y="-22" text-anchor="middle" font-size="9" fill="#F4B855">N</text><text y="30" text-anchor="middle" font-size="9" fill="#8392ad">S</text><text x="26" y="3" text-anchor="middle" font-size="9" fill="#8392ad">E</text><text x="-26" y="3" text-anchor="middle" font-size="9" fill="#8392ad">W</text><g id="needle"><polygon points="0,-24 5,4 0,0 -5,4" fill="#4fd8ff"/></g></svg>
    <div style="flex:1"><div class="row"><span>Heading</span><b id="hd">—</b></div><div class="row"><span>Position</span><b id="pos">—</b></div><div class="row"><span>Remaining</span><b id="rem">—</b></div></div>
   </div>
   <div class="bar"><i id="prog"></i></div>
   <div class="row"><span>Sim speed</span><input id="spd" type="range" min="1" max="5" value="2" style="width:150px;accent-color:#F4B855"></div>
   <div style="display:flex;gap:6px;margin-top:6px"><button class="btn go" id="bGo">▶ START ROVER</button><button class="btn ghost" id="bPause">⏸ PAUSE</button><button class="btn ghost" id="bReset">↺</button></div>
   <div class="note" style="margin-top:6px">Tip: click the rover to begin the next stop on the tour, or click any facility to plan a route.</div>
  </div>
  <div class="card"><h3>SELECT DESTINATION</h3><div id="dests"></div></div>
  <div class="card"><h3>ROUTE DETAILS</h3><div id="route"><span class="note">No route planned.</span></div></div>
  <div class="card"><h3>FACILITY INFORMATION</h3><div id="info"><span class="note">Click a facility on the map.</span></div></div>
  <div class="card"><h3>MISSION LOG</h3><div id="log"></div></div>
 </div>
</div>
<script>
const D=__DATA__, S=16, W=1024, H=672, CELL=D.cell;
const cv=document.getElementById('cv'), ctx=cv.getContext('2d'); cv.width=W; cv.height=H;
const $=id=>document.getElementById(id);
const P=v=>(v+.5)*S;
const F={}; D.fac.forEach(f=>F[f.name]=f);
const TOUR=["Lunar Habitat","Agricultural Lab","Solar Power Station","Communication Station","Resource Zone"];
const imgs={}; let pending=1+Object.keys(D.sprites).length;
function ld(k,src){const i=new Image();i.onload=()=>{if(--pending===0)start()};i.src=src;imgs[k]=i}
ld('terrain',D.terrain); Object.entries(D.sprites).forEach(([k,v])=>ld(k,v));

const st={at:"Landing Zone",pos:[...F["Landing Zone"].pos],head:0,moving:false,paused:false,route:null,to:null,s:0,total:0,cum:[],visited:new Set(["Landing Zone"]),sel:null,t0:performance.now(),dash:0,hover:null};
const compassN=b=>["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"][Math.floor(((b+11.25)%360)/22.5)];
const fmt=n=>String(n).padStart(2,'0');
function log(m){const l=$('log'),t=Math.floor((performance.now()-st.t0)/1000);const d=document.createElement('div');d.innerHTML=`<span>${fmt(Math.floor(t/3600))}:${fmt(Math.floor(t/60)%60)}:${fmt(t%60)}</span> ${m}`;l.prepend(d)}
function key(a,b){return D.routes[a+"|"+b]}

function plan(to){ if(st.moving||to===st.at)return; st.to=to; st.route=key(st.at,to); buildCum(); st.s=0; renderAll(); }
function buildCum(){const p=st.route.path;st.cum=[0];for(let i=1;i<p.length;i++)st.cum.push(st.cum[i-1]+Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]));st.total=st.cum[st.cum.length-1]}
function posAt(s){const p=st.route.path,c=st.cum;let i=1;while(i<c.length-1&&c[i]<s)i++;const f=(s-c[i-1])/((c[i]-c[i-1])||1);return[p[i-1][0]+(p[i][0]-p[i-1][0])*f,p[i-1][1]+(p[i][1]-p[i-1][1])*f]}
function startRover(){
  if(st.moving){st.paused=false;return}
  if(!st.route){const nx=TOUR.find(n=>!st.visited.has(n)&&n!==st.at);if(!nx){log("Tour complete — reset to replay.");return}plan(nx)}
  st.moving=true;st.paused=false;hideToast();st.sel=st.to;
  log(`Departing <b>${st.at}</b> → <b>${st.to}</b> · ${st.route.dist} m · bearing ${st.route.bearing}° ${st.route.dir}`);renderAll();
}
function arrive(){
  st.moving=false;st.at=st.to;st.pos=[...F[st.at].pos];st.visited.add(st.at);const r=st.route;st.route=null;st.to=null;st.s=0;
  log(`<b class="ok">Arrived at ${st.at}.</b> Route distance ${r.dist} m.`);
  const rest=D.fac.map(f=>f.name).filter(n=>n!==st.at);
  const left=TOUR.filter(n=>!st.visited.has(n));
  $('tt').textContent="✔ ARRIVED · "+st.at.toUpperCase();
  $('tp').textContent=left.length?`Rover is stationary. Select the next facility (${left.length} remaining on tour):`:"All tour facilities visited. Choose any destination to continue exploring:";
  const tc=$('tc');tc.innerHTML="";
  (left.length?left:rest).forEach(n=>{const b=document.createElement('button');b.className='btn';b.textContent=n+" · "+key(st.at,n).dist+" m";b.onclick=()=>{plan(n);startRover()};tc.appendChild(b)});
  $('toast').classList.add('show');st.sel=st.at;renderAll();
}
function hideToast(){$('toast').classList.remove('show')}

// ---------- drawing ----------
function pill(txt,x,y,col){ctx.font="600 11px Inter,Segoe UI,sans-serif";const w=ctx.measureText(txt).width+14;ctx.fillStyle="rgba(8,13,25,.85)";ctx.strokeStyle=col;ctx.lineWidth=1;
 ctx.beginPath();ctx.roundRect(x-w/2,y-9,w,18,9);ctx.fill();ctx.stroke();ctx.fillStyle="#E6EBF5";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(txt,x,y+.5)}
function drawFac(f,t){
  const x=P(f.pos[0]),y=P(f.pos[1]),sel=st.sel===f.name;let top=y-30,col=sel?"#F4B855":"#4a5d82";
  if(f.sprite){const im=imgs[f.sprite],w=f.w,h=w*im.height/im.width;
    ctx.fillStyle="rgba(0,0,0,.42)";ctx.beginPath();ctx.ellipse(x,y+2,w*.42,w*.11,0,0,7);ctx.fill();
    if(sel){ctx.save();ctx.shadowColor="#F4B855";ctx.shadowBlur=22;ctx.drawImage(im,x-w/2,y-h+h*.1,w,h);ctx.restore()}
    ctx.drawImage(im,x-w/2,y-h+h*.1,w,h);f._box=[x-w/2,y-h,w,h*1.05];top=y+16;
  }else if(f.key==="landing"){
    ctx.save();ctx.translate(x,y);ctx.scale(1,.62);ctx.fillStyle="rgba(180,190,210,.16)";ctx.strokeStyle=sel?"#F4B855":"rgba(230,235,245,.75)";ctx.lineWidth=3;
    ctx.beginPath();ctx.arc(0,0,58,0,7);ctx.fill();ctx.stroke();ctx.setLineDash([10,8]);ctx.beginPath();ctx.arc(0,0,40,0,7);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle="rgba(240,244,255,.85)";ctx.font="700 44px Inter,sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText("H",0,2);ctx.restore();
    f._box=[x-58,y-36,116,72];top=y+44;
  }else{
    ctx.save();ctx.translate(x,y);ctx.scale(1,.7);const pulse=.5+.5*Math.sin(t/500);
    ctx.fillStyle="rgba(79,216,255,"+(.10+.08*pulse)+")";ctx.strokeStyle=sel?"#F4B855":"rgba(79,216,255,.9)";ctx.lineWidth=2;ctx.setLineDash([6,5]);
    ctx.beginPath();ctx.arc(0,0,44,0,7);ctx.fill();ctx.stroke();ctx.setLineDash([]);
    ctx.strokeStyle="rgba(79,216,255,.5)";for(let i=-40;i<=40;i+=14){ctx.beginPath();ctx.moveTo(i-20,-30);ctx.lineTo(i+20,30);ctx.stroke()}
    ctx.restore();ctx.fillStyle="#4fd8ff";ctx.font="700 18px sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText("◎",x,y-2);
    f._box=[x-44,y-32,88,64];top=y+34;
  }
  const vis=st.visited.has(f.name)&&f.name!=="Landing Zone";
  pill((vis?"✔ ":"")+f.name.toUpperCase(),x,top,vis?"#35d58a":col);
}
function drawPath(p,from,to,style){ctx.beginPath();for(let i=0;i<p.length;i++){const x=P(p[i][0]),y=P(p[i][1]);i?ctx.lineTo(x,y):ctx.moveTo(x,y)}
 ctx.lineWidth=style.w;ctx.strokeStyle=style.c;ctx.setLineDash(style.d||[]);ctx.lineDashOffset=style.o||0;ctx.shadowColor=style.c;ctx.shadowBlur=style.g||0;ctx.lineCap="round";ctx.lineJoin="round";ctx.stroke();ctx.shadowBlur=0;ctx.setLineDash([])}
function drawRover(t){
  const x=P(st.pos[0]),y=P(st.pos[1]);ctx.save();ctx.translate(x,y);
  if(!st.moving){const r=22+4*Math.sin(t/260);ctx.strokeStyle="rgba(244,184,85,"+(.55+.3*Math.sin(t/260))+")";ctx.lineWidth=2;ctx.beginPath();ctx.arc(0,0,r,0,7);ctx.stroke()}
  ctx.rotate(st.head*Math.PI/180);ctx.shadowColor="rgba(0,0,0,.6)";ctx.shadowBlur=8;
  ctx.fillStyle="#141a26";[-11,0,11].forEach(o=>{ctx.fillRect(-14,o-4,6,8);ctx.fillRect(8,o-4,6,8)});
  ctx.shadowBlur=0;ctx.fillStyle="#d9dee8";ctx.strokeStyle="#7d8aa3";ctx.lineWidth=1.5;ctx.beginPath();ctx.roundRect(-9,-16,18,32,4);ctx.fill();ctx.stroke();
  ctx.fillStyle="#1d3a73";ctx.fillRect(-7,-4,14,14);ctx.strokeStyle="#4f74c4";ctx.strokeRect(-7,-4,14,14);
  ctx.fillStyle="#F4B855";ctx.beginPath();ctx.arc(0,-11,3.2,0,7);ctx.fill();
  ctx.fillStyle="#9ff";ctx.fillRect(-2,-19,4,3);ctx.restore();
  if(st.moving){ctx.save();ctx.translate(x,y);ctx.rotate(st.head*Math.PI/180);const g=ctx.createLinearGradient(0,-20,0,-90);g.addColorStop(0,"rgba(255,240,180,.28)");g.addColorStop(1,"rgba(255,240,180,0)");
   ctx.fillStyle=g;ctx.beginPath();ctx.moveTo(-5,-20);ctx.lineTo(-34,-90);ctx.lineTo(34,-90);ctx.lineTo(5,-20);ctx.fill();ctx.restore()}
}
function frame(now){
  const dt=Math.min(.05,(now-(frame.l||now))/1000);frame.l=now;st.dash-=dt*18;
  if(st.moving&&!st.paused){st.s+=dt*(.9+$('spd').value*.9);
    if(st.s>=st.total){arrive()}else{
      st.pos=posAt(st.s);const a=posAt(Math.min(st.total,st.s+1.4)),b=st.pos;
      const th=Math.atan2(a[0]-b[0],-(a[1]-b[1]))*180/Math.PI;let d=((th-st.head+540)%360)-180;st.head=(st.head+d*Math.min(1,dt*6)+360)%360;}}
  ctx.clearRect(0,0,W,H);ctx.drawImage(imgs.terrain,0,0,W,H);ctx.fillStyle="rgba(6,10,20,.28)";ctx.fillRect(0,0,W,H);
  // hazards
  if($('tHaz').checked)D.craters.forEach(([cx,cy,r])=>{const x=P(cx),y=P(cy);ctx.strokeStyle="rgba(255,90,90,.75)";ctx.lineWidth=1.6;ctx.setLineDash([5,4]);ctx.beginPath();ctx.arc(x,y,(r+.6)*S,0,7);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle="rgba(255,90,90,.07)";ctx.fill()});
  // route network (all pairs from habitat hub, faint)
  if($('tNet').checked){["Lunar Habitat"].forEach(h=>D.fac.forEach(f=>{if(f.name!==h&&f.name!=="Landing Zone"){drawPath(key(h,f.name).path,0,0,{w:2,c:"rgba(230,235,245,.28)",d:[2,8]})}}));drawPath(key("Landing Zone","Lunar Habitat").path,0,0,{w:2,c:"rgba(230,235,245,.28)",d:[2,8]})}
  if(st.route){const p=st.route.path;drawPath(p,0,0,{w:7,c:"rgba(53,213,138,.18)"});drawPath(p,0,0,{w:3,c:st.moving?"rgba(79,216,255,.5)":"#35d58a",d:[10,8],o:st.dash,g:8});
    if(st.s>0){let i=0;while(i<st.cum.length&&st.cum[i]<st.s)i++;drawPath(p.slice(0,i).concat([st.pos]),0,0,{w:4,c:"#4fd8ff",g:12})}
    st.route.waypoints.forEach((w,i)=>{const x=P(w.to[0]),y=P(w.to[1]);ctx.fillStyle="#080D19";ctx.strokeStyle="#35d58a";ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,7,0,7);ctx.fill();ctx.stroke();ctx.fillStyle="#fff";ctx.font="700 9px Inter,sans-serif";ctx.textAlign="center";ctx.textBaseline="middle";ctx.fillText(i<st.route.waypoints.length-1?("W"+(i+1)):"G",x,y+.5)})}
  const items=[...D.fac].sort((a,b)=>a.pos[1]-b.pos[1]);let drawnRover=false;
  items.forEach(f=>{if(!drawnRover&&st.pos[1]<f.pos[1]-0.5){drawRover(now);drawnRover=true}drawFac(f,now)});if(!drawnRover)drawRover(now);
  // telemetry
  $('met').textContent=(()=>{const t=Math.floor((now-st.t0)/1000);return fmt(Math.floor(t/3600))+":"+fmt(Math.floor(t/60)%60)+":"+fmt(t%60)})();
  $('rstate').textContent=st.moving?(st.paused?"PAUSED":"DRIVING"):"IDLE";
  $('hd').textContent=Math.round(st.head)+"° "+compassN(st.head);$('needle').setAttribute('transform','rotate('+st.head+')');
  $('pos').textContent=`X ${(st.pos[0]*CELL).toFixed(0)} · Y ${(st.pos[1]*CELL).toFixed(0)} m`;
  if(st.route){const fr=st.total?st.s/st.total:0;$('prog').style.width=(fr*100)+"%";$('rem').textContent=Math.max(0,Math.round(st.route.dist*(1-fr)))+" m";
    if(st.moving){const wp=st.route.waypoints;let acc=0,tot=wp.reduce((a,w)=>a+w.dist,0),k=wp.length-1;for(let i=0;i<wp.length;i++){acc+=wp[i].dist/tot;if(fr<=acc){k=i;break}}
      const el=$('leg');if(el)el.innerHTML=`Leg ${k+1}/${wp.length}: <b>${wp[k].bearing}° ${wp[k].dir}</b>`}}
  else{$('prog').style.width="0";$('rem').textContent="—"}
  requestAnimationFrame(frame);
}
// ---------- panels ----------
function renderAll(){
  const d=$('dests');d.innerHTML="";
  D.fac.forEach(f=>{const b=document.createElement('button');const cur=f.name===st.at;const r=cur?null:key(st.at,f.name);
    b.className='dest'+(cur?' cur':'')+(st.to===f.name?' sel':'');
    b.innerHTML=`<span>${st.visited.has(f.name)&&f.name!=="Landing Zone"?'<span class="ok">✔</span> ':''}${f.name}</span><small>${cur?'rover here':r.dist+' m · '+r.dir}</small>`;
    if(!cur)b.onclick=()=>{if(st.moving)return;st.sel=f.name;plan(f.name);hideToast()};d.appendChild(b)});
  const R=$('route');
  if(st.route){const r=st.route;R.innerHTML=`<div class="row"><span>Start</span><b>${st.at}</b></div><div class="row"><span>Destination</span><b>${st.to}</b></div>
   <div class="row"><span>Route distance</span><b>${r.dist} m</b></div><div class="row"><span>Straight-line</span><b>${r.straight} m</b></div>
   <div class="row"><span>Overall bearing</span><b>${r.bearing}° ${r.dir}</b></div><div class="row"><span>Terrain risk</span><span class="tag ${r.risk}">${r.risk}</span></div>
   <div class="row"><span>Status</span><b>${st.moving?'En route':'Planned'}</b></div><div class="row"><span>Current leg</span><span id="leg">—</span></div>
   <table style="margin-top:6px"><tr><th>Leg</th><th>From → To (m)</th><th>Dist</th><th>Dir</th></tr>${r.waypoints.map((w,i)=>`<tr><td>${i+1}</td><td>(${w.frm[0]*CELL},${w.frm[1]*CELL}) → (${w.to[0]*CELL},${w.to[1]*CELL})</td><td>${w.dist} m</td><td>${w.bearing}° ${w.dir}</td></tr>`).join('')}</table>
   <div class="note" style="margin-top:6px">Route found with A* over a slope/roughness/crater-proximity cost grid, craters treated as no-go cells.</div>`;
  }else R.innerHTML='<span class="note">No route planned. Pick a destination above or click a facility on the map.</span>';
  $('bGo').disabled=st.moving&&!st.paused;
  const I=$('info');const f=st.sel&&F[st.sel];
  if(f){const hab=F["Lunar Habitat"],dh=Math.hypot(f.pos[0]-hab.pos[0],f.pos[1]-hab.pos[1])*CELL,bh=(Math.atan2(f.pos[0]-hab.pos[0],-(f.pos[1]-hab.pos[1]))*180/Math.PI+360)%360;
    const lz=F["Landing Zone"],dl=Math.hypot(f.pos[0]-lz.pos[0],f.pos[1]-lz.pos[1])*CELL;
    I.innerHTML=`<div style="font-weight:700;font-size:14px;margin-bottom:2px">${f.name}</div><div class="note" style="margin-bottom:6px">${f.type}</div>
    ${f.sprite?`<img src="${D.sprites[f.sprite]}" style="width:100%;max-height:120px;object-fit:contain;background:#0b1426;border-radius:8px;margin-bottom:6px">`:''}
    <div style="font-size:12px;color:#C7D0E0;margin-bottom:6px">${f.desc}</div>
    <div class="row"><span>Approx. size</span><b>${f.dims}</b></div>
    <div class="row"><span>From habitat</span><b>${f.name==="Lunar Habitat"?'—':dh.toFixed(0)+' m · '+compassN(bh)}</b></div>
    <div class="row"><span>From landing zone</span><b>${f.name==="Landing Zone"?'—':dl.toFixed(0)+' m'}</b></div>
    <div class="row"><span>Layout position</span><b>(${f.pos[0]*CELL}, ${f.pos[1]*CELL}) m</b></div>
    <div class="note" style="margin-top:6px">Conceptual asset. Positions are illustrative; lat/lon, slope, temperature and illumination require real DEM/thermal data.</div>`;
  }
}
// ---------- input ----------
function pick(e){const r=cv.getBoundingClientRect(),x=(e.clientX-r.left)*W/r.width,y=(e.clientY-r.top)*H/r.height;
  if(Math.hypot(x-P(st.pos[0]),y-P(st.pos[1]))<26)return{rover:true};
  for(const f of [...D.fac].reverse()){const b=f._box;if(b&&x>=b[0]&&x<=b[0]+b[2]&&y>=b[1]&&y<=b[1]+b[3])return{f}}return{}}
cv.addEventListener('click',e=>{const h=pick(e);
  if(h.rover){ if(!st.moving){startRover()} else {st.paused=!st.paused} }
  else if(h.f){st.sel=h.f.name;if(!st.moving&&h.f.name!==st.at){plan(h.f.name);hideToast()}else renderAll()}});
cv.addEventListener('mousemove',e=>{const h=pick(e);cv.style.cursor=(h.rover||h.f)?'pointer':'default'});
$('bGo').onclick=startRover;$('bPause').onclick=()=>{if(st.moving)st.paused=!st.paused;$('bPause').textContent=st.paused?"▶ RESUME":"⏸ PAUSE";renderAll()};
$('bReset').onclick=()=>{Object.assign(st,{at:"Landing Zone",pos:[...F["Landing Zone"].pos],head:0,moving:false,paused:false,route:null,to:null,s:0,sel:null});st.visited=new Set(["Landing Zone"]);hideToast();$('log').innerHTML="";log("Mission reset. Rover at Landing Zone.");renderAll()};
function start(){log("Systems nominal. Rover deployed at <b>Landing Zone</b>. Click the rover to begin.");renderAll();requestAnimationFrame(frame)}
</script></body></html>
""".replace("__CELL__", "10")
