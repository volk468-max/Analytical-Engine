"use strict";
const $ = id => document.getElementById(id);
const state = { rows:[], latest:null, asof:null };
const symbols = ["NVDA","AMD","MU","SOXX","QQQ","SPY"];
const percent = n => Number.isFinite(n) ? n.toFixed(1).replace(".",",")+"%" : "—";
const safe = v => String(v).replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function params(){
 return {symbol:$("symbol").value,label:$("label").value,
 threshold:Number($("threshold").value),horizon:Number($("horizon").value),
 model:$("model").value};
}
function subset(p, includeModel=false) {
 return state.rows.filter(r=>r.symbol===p.symbol&&r.label===p.label&&r.threshold===p.threshold&&r.horizon===p.horizon&&(!includeModel||r.model===p.model));
}
function latest(rows,model){return rows.find(r=>r.session===state.latest&&r.model===model);}
function lineChart(rows){
 const dates=[...new Set(rows.map(r=>r.session))].sort();
 if(!dates.length) return '<div class="empty">Пока нет сохранённых прогнозов</div>';
 const W=680,H=260,L=44,R=16,T=15,B=42;
 const x=i=>L+(W-L-R)*(dates.length===1?.5:i/(dates.length-1));
 const y=v=>T+(H-T-B)*(1-v/100);
 const grid=[0,25,50,75,100].map(n=>'<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(n)+'" y2="'+y(n)+'" class="gridline"/><text x="'+(L-9)+'" y="'+(y(n)+4)+'" text-anchor="end" class="axis">'+n+'%</text>').join("");
 const paths=["REGIME","HIST"].map((m,i)=>{
  const vals=dates.map(d=>rows.find(r=>r.session===d&&r.model===m)?.probability);
  const pts=vals.map((v,k)=>v==null?null:[x(k),y(v)]).filter(Boolean);
  const poly=pts.length>1?'<polyline points="'+pts.map(v=>v.join(",")).join(" ")+'" class="curve '+(i?"hist":"regime")+'"/>':"";
  const circles=pts.map(pt=>'<circle cx="'+pt[0]+'" cy="'+pt[1]+'" r="4" class="point '+(i?"hist":"regime")+'"/>').join("");
  return poly+circles;
 }).join("");
 const labels=[0,Math.floor((dates.length-1)/2),dates.length-1].filter((v,i,a)=>a.indexOf(v)===i).map(i=>'<text x="'+x(i)+'" y="'+(H-12)+'" text-anchor="middle" class="axis">'+dates[i].slice(5)+'</text>').join("");
 return '<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="История прогнозов HIST и REGIME">'+grid+paths+labels+'</svg>';
}
function matrix(p) {
 const modelRows=state.rows.filter(r=>r.session===state.latest&&r.symbol===p.symbol&&r.label===p.label&&r.model===p.model);
 let out='<table><thead><tr><th>Сессий</th><th>−5%</th><th>−10%</th><th>−15%</th></tr></thead><tbody>';
 for(const h of [10,20,60]){
  out+='<tr><th>'+h+'</th>';
  for(const t of [5,10,15]){
   const n=modelRows.find(r=>r.horizon===h&&r.threshold===t)?.probability;
   out+='<td class="'+(h===p.horizon&&t===p.threshold?"selected":"")+'">'+percent(n)+'</td>';
  }
  out+='</tr>';
 }
 return out+'</tbody></table><p class="small muted">Вероятность хотя бы одного касания порога в течение горизонта, не доходность на последнюю дату.</p>';
}
function score(rows){
 if(!rows.length)return null;
 const n=rows.length, brier=rows.reduce((s,r)=>s+(r.probability/100-Number(r.outcome))**2,0)/n;
 const frequency=rows.filter(r=>r.outcome).length/n;
 return {n,brier,frequency};
}
function accuracy(rows){
 const ready=rows.filter(r=>r.outcome_status==="MATURED"&&typeof r.outcome==="boolean");
 const h=score(ready.filter(r=>r.model==="HIST"));
 const g=score(ready.filter(r=>r.model==="REGIME"));
 const baseline=ready.filter(r=>r.model==="HIST"&&r.baseline!=null);
 const b=baseline.length?baseline.reduce((s,r)=>s+(r.baseline-Number(r.outcome))**2,0)/baseline.length:null;
 if(!h&&!g)return '<div class="empty"><strong>Оценивать точность пока рано.</strong><p>Нет завершённых прогнозных горизонтов с подтверждёнными исходами. Это ожидаемо для новой системы.</p></div>';
 return '<table><thead><tr><th>Метрика</th><th>HIST</th><th>REGIME</th></tr></thead><tbody>'+
 '<tr><td>Проверено прогнозов</td><td>'+(h?.n??0)+'</td><td>'+(g?.n??0)+'</td></tr>'+
 '<tr><td>Brier ↓</td><td>'+(h?h.brier.toFixed(3):"—")+'</td><td>'+(g?g.brier.toFixed(3):"—")+'</td></tr>'+
 '<tr><td>Частота события</td><td>'+(h?percent(h.frequency*100):"—")+'</td><td>'+(g?percent(g.frequency*100):"—")+'</td></tr>'+
 '<tr><td>Базовая модель Brier</td><td colspan="2">'+(b==null?"Нет зрелых наблюдений":b.toFixed(3)+" (n="+baseline.length+")")+'</td></tr></tbody></table>'+
 '<p class="small muted">Меньший Brier лучше. Пересекающиеся горизонты зависимы: без независимой проверки и интервалов неопределённости нельзя утверждать, что одна модель превосходит другую.</p>';
}
function comparison(p){
 const rs=state.rows.filter(r=>r.session===state.latest&&r.label===p.label&&r.horizon===p.horizon&&r.threshold===p.threshold&&r.model===p.model);
 return '<div class="bars">'+symbols.map(t=>{
  const n=rs.find(r=>r.symbol===t)?.probability;
  return '<div class="barrow"><strong>'+t+'</strong><div class="track"><div class="fill" style="width:'+(Number.isFinite(n)?Math.max(0,Math.min(100,n)):0)+'%"></div></div><span>'+percent(n)+'</span></div>';
 }).join("")+'</div>';
}
function historyTable(rows){
 const days=[...new Set(rows.map(r=>r.session))].sort().reverse();
 if(!days.length)return '<div class="empty">Данных нет</div>';
 return '<div class="scroll"><table><thead><tr><th>Сессия</th><th>HIST</th><th>REGIME</th><th>Исход</th></tr></thead><tbody>'+days.slice(0,40).map(day=>{
  const a=rows.find(r=>r.session===day&&r.model==="HIST"),b=rows.find(r=>r.session===day&&r.model==="REGIME");
  const status=a?.outcome_status==="MATURED"?(a.outcome?"Событие":"Не было"):"Ожидается";
  return '<tr><td>'+safe(day)+'</td><td>'+percent(a?.probability)+'</td><td>'+percent(b?.probability)+'</td><td>'+status+'</td></tr>';
 }).join("")+'</tbody></table></div>';
}
function render(){
 const p=params(), rows=subset(p), a=latest(rows,"HIST"),b=latest(rows,"REGIME");
 $("hist").textContent=percent(a?.probability);
 $("regime").textContent=percent(b?.probability);
 $("delta").textContent=a&&b?(b.probability-a.probability>0?"+":"")+(b.probability-a.probability).toFixed(1).replace(".",",")+" п.п.":"—";
 $("sessions").textContent=new Set(state.rows.map(r=>r.session)).size;
 $("recordCount").textContent=state.rows.length+" числовых прогнозов в окне 120 дней";
 $("historyChart").innerHTML=lineChart(rows);
 $("matrixModel").textContent=p.model;
 $("matrix").innerHTML=matrix(p);
 $("accuracy").innerHTML=accuracy(rows);
 $("compare").innerHTML=comparison(p);
 $("historyTable").innerHTML=historyTable(rows);
 $("status").textContent=state.latest?"Сессия "+state.latest:"Нет данных";
 $("asof").textContent=state.asof?"Получено "+new Date(state.asof).toLocaleString("ru-RU"):"";
}
async function refresh(){
 $("status").textContent="Загрузка…";
 try{
  const res=await fetch("/api/data",{credentials:"same-origin",cache:"no-store"});
  if(res.status===401){$("login").hidden=false;$("dashboard").hidden=true;$("status").textContent="Требуется вход";return;}
  if(!res.ok)throw new Error("Сервер временно недоступен");
  const data=await res.json();
  if(!Array.isArray(data.rows))throw new Error("Некорректный ответ");
  state.rows=data.rows;state.latest=data.latest_session;state.asof=data.asof;
  $("login").hidden=true;$("dashboard").hidden=false;render();
 }catch(e){$("status").textContent="Ошибка обновления";$("asof").textContent=e.message;}
}
$("loginForm").addEventListener("submit",async e=>{
 e.preventDefault();$("loginError").textContent="";
 try{
  const res=await fetch("/api/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:$("password").value})});
  $("password").value="";
  if(!res.ok)throw new Error("Неверный пароль или ошибка входа");
  await refresh();
setInterval(()=>{if(!$("dashboard").hidden)refresh();},5*60*1000);
 }catch(err){$("loginError").textContent=err.message;}
});
for(const id of ["symbol","threshold","horizon","label","model"])$(id).addEventListener("change",render);
$("refresh").addEventListener("click",refresh);
refresh();
