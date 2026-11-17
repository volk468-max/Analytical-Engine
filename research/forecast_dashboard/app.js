"use strict";
const $ = id => document.getElementById(id);
const state = { rows:[], latest:null, asof:null };
const symbols = ["NVDA","AMD","MU","SOXX","QQQ","SPY"];
const percent = n => Number.isFinite(n) ? n.toFixed(1).replace(".",",")+"%" : "—";
const safe = v => String(v).replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function params(){
 return {symbol:$("symbol").value,label:$("label").value,
 threshold:Number($("threshold").value),horizon:Number($("horizon").value),
 model:$("model").value, alternative:$("showAlternative").checked};
}
function subset(p) {
 return state.rows.filter(r=>r.symbol===p.symbol&&r.label===p.label&&r.threshold===p.threshold&&r.horizon===p.horizon);
}
function latest(rows,model){return rows.find(r=>r.model===model);}
function lineChart(rows,p){
 const visible=rows.filter(r=>r.model===p.model||(p.alternative&&r.model!==p.model));
 const dates=[...new Set(visible.map(r=>r.session))].sort();
 if(!dates.length) return '<div class="empty">Для выбранного сценария пока нет прогнозов</div>';
 const W=680,H=260,L=44,R=16,T=15,B=42;
 const x=i=>L+(W-L-R)*(dates.length===1?.5:i/(dates.length-1));
 const y=v=>T+(H-T-B)*(1-v/100);
 const grid=[0,25,50,75,100].map(n=>'<line x1="'+L+'" x2="'+(W-R)+'" y1="'+y(n)+'" y2="'+y(n)+'" class="gridline"/><text x="'+(L-9)+'" y="'+(y(n)+4)+'" text-anchor="end" class="axis">'+n+'%</text>').join("");
 const models=p.alternative?[p.model,p.model==="HIST"?"REGIME":"HIST"]:[p.model];
 const paths=models.map((m,i)=>{
  const vals=dates.map(d=>visible.find(r=>r.session===d&&r.model===m)?.probability);
  const pts=vals.map((v,k)=>v==null?null:[x(k),y(v)]).filter(Boolean);
  const poly=pts.length>1?'<polyline points="'+pts.map(v=>v.join(",")).join(" ")+'" class="curve '+(i?"hist":"regime")+'"/>':"";
  const circles=pts.map(pt=>'<circle cx="'+pt[0]+'" cy="'+pt[1]+'" r="4" class="point '+(i?"hist":"regime")+'"/>').join("");
  return poly+circles;
 }).join("");
 const labels=[0,Math.floor((dates.length-1)/2),dates.length-1].filter((v,i,a)=>a.indexOf(v)===i).map(i=>'<text x="'+x(i)+'" y="'+(H-12)+'" text-anchor="middle" class="axis">'+dates[i].slice(5)+'</text>').join("");
 return '<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="История выбранного прогноза">'+grid+paths+labels+'</svg>';
}
function matrix(p,date) {
 const modelRows=state.rows.filter(r=>r.session===date&&r.symbol===p.symbol&&r.label===p.label&&r.model===p.model);
 let out='<table><thead><tr><th>Сессий</th><th>−5%</th><th>−10%</th><th>−15%</th></tr></thead><tbody>';
 for(const h of [10,20,60]){
  out+='<tr><th>'+h+'</th>';
  for(const t of [5,10,15]){
   const n=modelRows.find(r=>r.horizon===h&&r.threshold===t)?.probability;
   out+='<td class="'+(h===p.horizon&&t===p.threshold?"selected":"")+'">'+percent(n)+'</td>';
  }
  out+='</tr>';
 }
 return out+'</tbody></table><p class="small muted">Событие — хотя бы одно достижение порога за весь период, а не падение цены ровно в последний день.</p>';
}
function score(rows){
 if(!rows.length)return null;
 const n=rows.length, brier=rows.reduce((s,r)=>s+(r.probability/100-Number(r.outcome))**2,0)/n;
 const frequency=rows.filter(r=>r.outcome).length/n;
 return {n,brier,frequency};
}
function accuracy(rows){
 // Score HIST and REGIME on exactly the same completed event dates.
 const byDay=new Map();
 for(const r of rows){
  if(r.outcome_status!=="MATURED"||typeof r.outcome!=="boolean")continue;
  if(!byDay.has(r.session))byDay.set(r.session,{});
  byDay.get(r.session)[r.model]=r;
 }
 const pairs=[...byDay.values()].filter(v=>v.HIST&&v.REGIME&&v.HIST.outcome===v.REGIME.outcome);
 const h=score(pairs.map(v=>v.HIST)),g=score(pairs.map(v=>v.REGIME));
 const baseline=pairs.map(v=>v.HIST).filter(r=>r.baseline!=null);
 const b=baseline.length?baseline.reduce((s,r)=>s+(Number(r.baseline)-Number(r.outcome))**2,0)/baseline.length:null;
 if(!pairs.length)return '<div class="empty"><strong>Подтверждённой точности пока нет.</strong><p>Для этого сценария ещё нет парных завершённых прогнозов с проверенным исходом. Вероятности остаются исследовательскими оценками.</p></div>';
 return '<table><thead><tr><th>Метрика</th><th>HIST</th><th>REGIME</th></tr></thead><tbody>'+
 '<tr><td>Парных завершённых событий</td><td>'+h.n+'</td><td>'+g.n+'</td></tr>'+
 '<tr><td>Brier ↓</td><td>'+h.brier.toFixed(3)+'</td><td>'+g.brier.toFixed(3)+'</td></tr>'+
 '<tr><td>Частота события</td><td>'+percent(h.frequency*100)+'</td><td>'+percent(g.frequency*100)+'</td></tr>'+
 '<tr><td>Базовая модель Brier</td><td colspan="2">'+(b==null?"Нет сопоставимых наблюдений":b.toFixed(3)+" (n="+baseline.length+")")+'</td></tr></tbody></table>'+
 '<p class="small muted">Сравнение только на совпадающих событиях. Пересекающиеся горизонты зависимы; без достаточной выборки, доверительных интервалов и проверки калибровки нельзя делать вывод о превосходстве модели или использовать её как торговый сигнал.</p>';
}
function comparison(p,date){
 const rs=state.rows.filter(r=>r.session===date&&r.label===p.label&&r.horizon===p.horizon&&r.threshold===p.threshold&&r.model===p.model);
 return '<div class="bars">'+symbols.map(t=>{
  const n=rs.find(r=>r.symbol===t)?.probability;
  return '<div class="barrow"><strong>'+t+'</strong><div class="track"><div class="fill" style="width:'+(Number.isFinite(n)?Math.max(0,Math.min(100,n)):0)+'%"></div></div><span>'+percent(n)+'</span></div>';
 }).join("")+'</div><p class="small muted">Сравнение вероятности одинакового процентного падения. Различия волатильности не нормализованы; это не рейтинг покупок или продаж.</p>';
}
function historyTable(rows,p){
 const dates=[...new Set(rows.map(r=>r.session))].sort().reverse();
 if(!dates.length)return '<div class="empty">Данных нет</div>';
 const alt=p.model==="HIST"?"REGIME":"HIST";
 return '<div class="scroll"><table><thead><tr><th>Сессия</th><th>'+p.model+'</th>'+(p.alternative?'<th>'+alt+'</th>':"")+'<th>Исход</th></tr></thead><tbody>'+dates.slice(0,40).map(day=>{
  const a=rows.find(r=>r.session===day&&r.model===p.model),b=rows.find(r=>r.session===day&&r.model===alt);
  const status=a?.outcome_status==="MATURED"?(a.outcome?"Событие":"Не было"):"Ожидается";
  return '<tr><td>'+safe(day)+'</td><td>'+percent(a?.probability)+'</td>'+(p.alternative?'<td>'+percent(b?.probability)+'</td>':"")+'<td>'+status+'</td></tr>';
 }).join("")+'</tbody></table></div>';
}
function render(){
 const p=params(),rows=subset(p),selected=latest(rows,p.model);
 const date=selected?.session??null;
 const series=rows.filter(r=>r.model===p.model);
 const prior=series.find(r=>r.session!==date);
 const comparable=selected&&prior&&selected.model_id===prior.model_id;
 const versionChange=selected&&series.some(r=>r.model_id!==selected.model_id);
 $("forecast").textContent=percent(selected?.probability);
 $("modelName").textContent=p.model;
 $("dayChange").textContent=comparable?(selected.probability-prior.probability>0?"+":"")+(selected.probability-prior.probability).toFixed(1).replace(".",",")+" п.п.":"—";
 $("previousDate").textContent=prior?(comparable?"По сравнению с "+prior.session:"Сменилась версия модели: прямое сравнение некорректно"):"Нет предыдущего выпуска для сравнения";
 $("sessionDate").textContent=date?date.slice(8,10)+"."+date.slice(5,7)+"."+date.slice(0,4):"—";
 $("issuedAt").textContent=selected?.issued_at?"Выпущен "+new Date(selected.issued_at).toLocaleString("ru-RU",{timeZone:"Europe/Moscow",day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"})+" МСК":"Нет выпуска";
 const matured=series.filter(r=>r.outcome_status==="MATURED"&&typeof r.outcome==="boolean").length;
 $("matureCount").textContent=matured;
 $("recordCount").textContent="Из "+series.length+" выпусков для выбранного сценария";
 $("scenario").textContent="Вероятность хотя бы одного падения на "+p.threshold+"% или более за "+p.horizon+" торговых сессий · "+(p.label==="LOW_INTRADAY"?"внутридневной минимум":"цена закрытия");
 $("freshness").textContent=!date?"Нет данных по выбранному сценарию":date!==state.latest?"Внимание: последний выпуск этого сценария ("+date+") старше последней сессии в базе ("+state.latest+"). Проверить полноту данных.":"Последняя доступная торговая сессия: "+date+". Прогноз относится к будущему периоду от этой даты, а не к текущей цене в момент просмотра.";
 $("historyChart").innerHTML=lineChart(rows,p);
 $("legend").innerHTML='<span><i class="dot a"></i>'+p.model+'</span>'+(p.alternative?'<span><i class="dot b"></i>'+(p.model==="HIST"?"REGIME":"HIST")+'</span>':"");
 $("matrixModel").textContent=p.model;
 $("matrix").innerHTML=matrix(p,date);
 $("accuracy").innerHTML=accuracy(rows);
 $("compare").innerHTML=comparison(p,date);
 $("historyTable").innerHTML=historyTable(rows,p);
 $("status").textContent=state.latest?"Данные по "+state.latest:"Нет данных";
 $("asof").textContent=state.asof?"Проверено "+new Date(state.asof).toLocaleString("ru-RU"):"";
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
 }catch(err){$("loginError").textContent=err.message;}
});
for(const id of ["symbol","threshold","horizon","label","model","showAlternative"])$(id).addEventListener("change",render);
$("refresh").addEventListener("click",refresh);
refresh();
setInterval(()=>{if(!$("dashboard").hidden)refresh();},5*60*1000);
