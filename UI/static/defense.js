const $=id=>document.getElementById(id),$$=s=>document.querySelectorAll(s);
const rand=(a,b)=>Math.random()*(b-a)+a,ri=(a,b)=>Math.floor(rand(a,b+1)),pick=a=>a[ri(0,a.length-1)];
const p2=n=>String(n).padStart(2,'0');
const fmt$=n=>'$'+Math.abs(n).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});

/* ===== STATE ===== */
let S={balance:0,available:0,hold:0,income:0,spend:0,qber:0.0,channel:'SECURE',threats:0,esc:0,locked:false,chartData:[],txLog:[],atkTotal:0,atkBlocked:0,txSecured:0};
for(let i=0;i<50;i++)S.chartData.push(0);
let feedId=null,activeTab='account';

/* ===== TABS ===== */
function switchTab(t){activeTab=t;$$('.tabs span').forEach(s=>s.classList.toggle('on',s.dataset.tab===t));$$('.view').forEach(v=>v.classList.toggle('active',v.id==='view-'+t));if(t==='security')renderEsc();}
$$('.tabs span').forEach(s=>s.addEventListener('click',()=>switchTab(s.dataset.tab)));

/* ===== CLOCK ===== */
function clk(){$('clk').textContent=`${p2(new Date().getHours())}:${p2(new Date().getMinutes())}:${p2(new Date().getSeconds())}`;}
clk();setInterval(clk,1000);

/* ===== API ===== */
const KMS = '';
async function api(method, path, body) {
  try {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(KMS + path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      return { _error: err.detail || err.message || res.statusText, status: 'ERROR' };
    }
    return await res.json();
  } catch (e) {
    return { _error: e.message, status: 'OFFLINE' };
  }
}

async function loadData() {
  const [dAccounts, dStatus, dTx] = await Promise.all([
    api('GET', '/accounts'),
    api('GET', '/link_status'),
    api('GET', '/transactions')
  ]);

  if (!dStatus._error) {
    S.qber = dStatus.qber || 0;
    S.channel = dStatus.status === 'RED' ? 'COMPROMISED' : 'SECURE';
    S.threats = dStatus.attacks_detected || 0;
    S.esc = dStatus.escalation_level || 0;
    S.locked = S.esc >= 4;
    
    S.chartData.push(S.qber * 100);
    if (S.chartData.length > 50) S.chartData.shift();
  }

  if (!dAccounts._error && dAccounts.accounts) {
    let totalBal = 0;
    dAccounts.accounts.forEach(a => totalBal += a.balance);
    S.balance = totalBal;
    S.available = totalBal;
  }

  if (!dTx._error && dTx.transactions) {
    S.txLog = dTx.transactions.map(t => ({
      ts: new Date(t.timestamp*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}),
      desc: t.note || 'TRANSFER',
      dir: 'db',
      amt: t.amount,
      qber: t.qber
    }));
    S.txSecured = S.txLog.length;
  }

  render();
}

/* ===== RENDER ===== */
function render(){
  $('balance').textContent=fmt$(S.balance);
  $('available').textContent=fmt$(S.available);
  $('hold').textContent=fmt$(S.hold);
  $('statIncome').textContent='+'+fmt$(S.income);
  $('statSpend').textContent=fmt$(S.spend);
  $('statBlocked').textContent=S.atkBlocked;
  $('lockBal').textContent=fmt$(S.balance);
  const qS=S.qber>0.10?'threat':'secure',cs=S.channel==='SECURE'?'secure':'threat',es=S.esc>=3?'critical':S.esc>=1?'threat':'normal';
  setText('val-qber',(S.qber*100).toFixed(2)+'%');setText('val-channel',S.channel);
  setDS('card-qber',qS);setDS('card-channel',cs);
  setText('val-qber2',(S.qber*100).toFixed(2)+'%');setText('val-channel2',S.channel);setText('val-threats2',S.threats);setText('val-esc2','L'+S.esc);
  setDS('card-qber2',qS);setDS('card-channel2',cs);setDS('card-threats2',S.threats>0?'threat':'secure');setDS('card-esc2',es);
  setText('txCount',S.txLog.length+' records');setText('atkTotal',S.threats);setText('sbBlocked',S.atkBlocked);
  $('shieldPct').textContent=(99.4-S.qber*10).toFixed(1)+'%';
  const tl=$('threatlvl');
  if(S.locked||S.esc>=3){tl.dataset.lvl='critical';tl.innerHTML='<span class="dot"></span>CRITICAL';}
  else if(S.channel!=='SECURE'){tl.dataset.lvl='warn';tl.innerHTML='<span class="dot"></span>THREAT';}
  else{tl.dataset.lvl='secure';tl.innerHTML='<span class="dot"></span>SECURE';}
  $('lockout').classList.toggle('open',S.locked);
  if(activeTab==='security')renderEsc();
  drawChart();
  renderTxTable();
}
function setText(id,v){const e=$(id);if(e)e.textContent=v;}
function setDS(id,v){const e=$(id);if(e)e.dataset.state=v;}

/* ===== CHART ===== */
function drawChart(){const d=S.chartData,w=600,h=160,maxQ=35;const pts=d.map((v,i)=>[i/(d.length-1)*w,h-(Math.min(v,maxQ)/maxQ)*h]);const pl=pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');const e1=$('chartLine'),e2=$('chartArea');if(e1)e1.setAttribute('points',pl);if(e2)e2.setAttribute('d',`M${pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' L')} L${w},${h} L0,${h} Z`);}

/* ===== ESC LADDER ===== */
function renderEsc(){$$('#esclad .escstep').forEach(s=>{const lv=+s.dataset.lv;s.classList.toggle('on',lv<=S.esc&&S.esc>0);s.classList.toggle('crit',lv>=3&&lv<=S.esc);});}

/* ===== TRANSACTIONS ===== */
function renderTxTable(){const tb=$('txTable');if(!tb)return;tb.innerHTML=S.txLog.slice(0,10).map(t=>`<tr><td>${t.ts}</td><td><b>${t.desc}</b></td><td>${t.dir==='cr'?'CREDIT':'DEBIT'}</td><td style="color:${t.dir==='cr'?'var(--green)':'var(--red)'}">${t.dir==='cr'?'+':'-'}${fmt$(t.amt)}</td><td style="color:var(--amber)">ML-KEM</td><td><span class="chip ${t.qber>0.10?'critical':'secure'}"><i></i>${t.qber>0.10?'COMPROMISED':'SECURED'}</span></td></tr>`).join('');}

/* ===== ALERTS ===== */
let aSeq=0;
function pushAlert(msg,sev){
  const id=++aSeq,t=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const titles={critical:'CRITICAL ALERT',warning:'THREAT DETECTED',info:'SYSTEM NOTICE'};
  const el=document.createElement('div');el.className='alert-toast';el.dataset.sev=sev;el.id='a'+id;
  el.innerHTML=`<span class="alert-toast__ic"></span><div class="alert-toast__body"><div class="alert-toast__title">${titles[sev]||'NOTICE'}</div><div class="alert-toast__msg">${msg}</div></div><time class="alert-toast__time">${t}</time><button class="alert-toast__x" onclick="dismissAlert(${id})">×</button>`;
  $('alerts').insertBefore(el,$('alerts').firstChild);
  setTimeout(()=>dismissAlert(id),8000);
}
function dismissAlert(id){const el=$('a'+id);if(el){el.classList.add('out');setTimeout(()=>el.remove(),300);}}

/* ===== BUTTONS ===== */
$('simBtn').addEventListener('click',() => api('POST', '/trigger_attack'));
$('resetBtn').addEventListener('click',() => api('POST', '/reset').then(loadData));
$('simBtn2').addEventListener('click',()=>{api('POST', '/trigger_attack');switchTab('account');});
$('resetBtn2').addEventListener('click',() => api('POST', '/reset').then(loadData));
$('ackBtn').addEventListener('click',() => api('POST', '/reset').then(loadData));

/* ===== HERO CANVAS ===== */
const cv=$('hero'),ctx=cv.getContext('2d');let HW,HH,hcx,hcy;
function hresize(){const r=cv.getBoundingClientRect();cv.width=HW=r.width;cv.height=HH=r.height;hcx=HW/2;hcy=HH/2;}
hresize();addEventListener('resize',hresize);
let projectiles=[],rings=[];
function spawnProj(){const ang=rand(0,Math.PI*2),dist=Math.max(HW,HH);projectiles.push({x:hcx+Math.cos(ang)*dist,y:hcy+Math.sin(ang)*dist,vx:-Math.cos(ang)*4,vy:-Math.sin(ang)*4,life:1});}
function drawHero(){
  ctx.fillStyle='rgba(10,10,16,0.3)';ctx.fillRect(0,0,HW,HH);
  const qState=S.locked?'critical':S.channel!=='SECURE'?'warn':'secure';
  const cMain=qState==='critical'?'#FF3B3B':qState==='warn'?'#FFD23F':'#33FF66';
  
  if(Math.random()< (qState==='secure'?0.05:0.2)) spawnProj();
  projectiles.forEach((p,i)=>{
    p.x+=p.vx;p.y+=p.vy;
    const d=Math.hypot(p.x-hcx,p.y-hcy);
    if(d<40){
      rings.push({r:40,a:1,c:qState==='secure'?'#FFB000':cMain});
      projectiles.splice(i,1);
      if(qState!=='secure'&&Math.random()<0.3) {
        ctx.fillStyle='#FF3B3B';ctx.fillRect(0,0,HW,HH);
      }
    }else{
      ctx.fillStyle=qState==='secure'?'#FFB000':cMain;
      ctx.fillRect(p.x,p.y,2,2);
    }
  });
  
  rings.forEach((r,i)=>{
    ctx.beginPath();ctx.arc(hcx,hcy,r.r,0,Math.PI*2);
    ctx.strokeStyle=r.c;ctx.globalAlpha=r.a;
    ctx.lineWidth=2;ctx.stroke();
    r.r+=2;r.a-=0.05;
    if(r.a<=0)rings.splice(i,1);
  });
  ctx.globalAlpha=1;
  
  ctx.beginPath();ctx.arc(hcx,hcy,30,0,Math.PI*2);
  ctx.fillStyle=cMain;ctx.fill();
  ctx.shadowBlur=10;ctx.shadowColor=cMain;
  ctx.beginPath();ctx.arc(hcx,hcy,34,0,Math.PI*2);
  ctx.strokeStyle=cMain;ctx.lineWidth=1;ctx.stroke();
  ctx.shadowBlur=0;
  
  requestAnimationFrame(drawHero);
}

/* ===== BOOT ===== */
const blns=['INITIALIZING KERNEL...','LOADING QUANTUM MODULES...','ESTABLISHING BB84 LINK...','VERIFYING CHANNEL INTEGRITY...','CALIBRATING SHIELD...','LINK SECURE.'];
let bootIdx=0;
function doBoot(){
  if(bootIdx<blns.length){
    $('bootLines').textContent+=blns[bootIdx]+'\n';
    $('bootBar').style.width=((bootIdx+1)/blns.length)*100+'%';
    bootIdx++;
    setTimeout(doBoot,ri(200,600));
  }else{
    setTimeout(()=>{
      $('boot').classList.add('done');
      
      // Connect WebSocket
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${proto}://${location.host}/ws/events`);
      ws.onmessage = (e) => {
        try {
          const ev = JSON.parse(e.data);
          if (ev.event === 'attack') {
            pushAlert('⚠️ Channel interception! QBER: ' + ((ev.qber||0)*100).toFixed(1) + '%', 'critical');
          } else if (ev.event === 'lockdown') {
            pushAlert('🔒 EMERGENCY: All services suspended', 'critical');
          } else if (ev.event === 'escalation') {
            pushAlert('Security Escalation: Level ' + ev.level, 'warning');
          }
          loadData();
        } catch(err){}
      };
      
      setInterval(loadData, 2000);
      loadData();
      drawHero();
    },800);
  }
}
window.onload=doBoot;
