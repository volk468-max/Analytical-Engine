"use strict";
// Independent stage-one audit. Pure functions; no network, production imports or orders.
const Audit=(()=>{
const STOCKS=["AMD","NVDA","MU","TSM","AVGO","AMAT","AMZN","META","PLTR","LRCX","NBIS"];
const SEMIS=["AMD","NVDA","MU","TSM","AVGO","AMAT","LRCX"];
const START="2021-01-01", END="2026-11-02";
const avg=a=>a.reduce((s,v)=>s+v,0)/a.length;
function group(rows){let out={};for(const r of rows){(out[r.symbol]??=[]).push({...r});}for(const a of Object.values(out)){a.sort((x,y)=>x.date.localeCompare(y.date));if(new Set(a.map(r=>r.date)).size!==a.length)throw Error("duplicate sessions");}return out;}
function enrich(a){return a.map((r,i)=>{let prior=a.slice(Math.max(0,i-60),i),win=a.slice(Math.max(0,i-19),i+1);return {...r,ret5:i>=5?r.close/a[i-5].close-1:null,ma20:win.length===20?avg(win.map(x=>x.close)):null,prior_peak60:prior.length?Math.max(...prior.map(x=>x.close)):null,prior_support:prior.length?Math.min(...prior.map(x=>x.low)):null};});}
function market(input){
 const g=group(input.prices);for(const s in g)g[s]=enrich(g[s]);
 const lookup=Object.fromEntries(Object.entries(g).map(([s,a])=>[s,Object.fromEntries(a.map(r=>[r.date,r]))]));
 const vs=input.vix.filter(r=>r.date<=input.data_end).sort((a,b)=>a.date.localeCompare(b.date));
 const vm=Object.fromEntries(vs.map((r,i)=>[r.date,{...r,change5:i>=5?r.close/vs[i-5].close-1:null}]));
 const ds=g.QQQ.map(r=>r.date);
 const rates=input.rates.map(r=>{const k=ds.findIndex(d=>d>=r.date);const pub=ds[k+2];return {...r,available_at:k>=0&&pub?new Date(Date.parse(pub+"T00:00:00Z")+86400000).toISOString():null};});
 const all=ds.map(date=>{
  const q=lookup.QQQ[date],candidate=vm[date],ss=SEMIS.map(s=>lookup[s]?.[date]);
  const complete=ss.every(x=>x&&x.ret5!==null),neg=complete?ss.filter(x=>x.ret5<0).length:null;
  const sectorRet=complete?avg(ss.map(x=>x.ret5)):null;
  const available_at=new Date(Date.parse(date+"T00:00:00Z")+86400000).toISOString();
  const v=candidate&&candidate.available_at<=available_at?candidate:null;
  const known=rates.filter(r=>r.available_at&&r.available_at<=available_at&&r.date<=date).at(-1);
  return {date,available_at,publication_status:"ASSUMED_TIMES_NOT_VERIFIED",qqq_close:q.close,qqq_ret5:q.ret5,qqq_ma20:q.ma20,
   sox_close:lookup.SOX?.[date]?.close??null,sector_negative_7:neg,sector_ret5:sectorRet,
   sector_flag:complete&&q.ret5!==null?neg>=4&&sectorRet<q.ret5:null,
   broad_flag:q.ma20!==null&&q.ret5!==null?q.close<q.ma20&&q.ret5<0:null,
   vix:v?.close??null,vix_change5:v?.change5??null,
   vix_level_flag:v?v.close>=25:null,vix_change_flag:v&&v.change5!==null?v.change5>=0.20:null,
   dgs10_observation_date:known?.date??null,dgs10_known:known?.yield_pct??null,
   dgs10_availability:"ASSUMED_TWO_QQQ_SESSION_LAG_NOT_ORIGINAL_VINTAGE",
   sp500:null,nasdaq_index:null,russell2000:null,soxx:null,smh:null,dgs2:null,dxy:null,ig_spread:null,hy_spread:null,whole_market_breadth:null,
   confirmed_trade_signal:false};
 });
 return {g,lookup,all,rows:all.filter(r=>r.date>=START&&r.date<=END)};
}
function events(a,start=START,window=60){
 const first=a.findIndex(r=>r.date>=start);if(first<0)return [];
 let seed=a.slice(Math.max(0,first-window),first),peak=seed.length?seed.reduce((p,r)=>r.close>=p.close?r:p):a[first],event=null,out=[];
 for(let i=first;i<a.length;i++){const r=a[i];if(r.date>END)break;
  if(r.close>=peak.close){if(event){event.recovery_date=r.date;event.status="RECOVERED";if(event.depth_pct>=5)out.push(event);event=null;}peak=r;continue;}
  if(!event)event={symbol:r.symbol,peak_date:peak.date,peak_close:peak.close,start_date:r.date,trough_date:r.date,trough_close:r.close,depth_pct:0,status:"ONGOING_CENSORED",recovery_date:null,left_censored:peak.date<start};
  if(r.close<event.trough_close){event.trough_close=r.close;event.trough_date=r.date;}
  event.depth_pct=100*(1-event.trough_close/peak.close);
  for(const n of [5,10,15])if(!event["hit_"+n]&&r.close<=peak.close*(1-n/100))event["hit_"+n]=r.date;
 }
 if(event&&event.depth_pct>=5)out.push(event);return out;
}
function warnings(m){
 const flags=["sector_flag","broad_flag","vix_level_flag","vix_change_flag"],out=[];
 for(let i=0;i<m.all.length;i++){const r=m.all[i];if(r.date<START||r.date>END)continue;
  for(const flag of flags){if(r[flag]===true&&(i===0||m.all[i-1][flag]!==true)){
   out.push({date:r.date,available_at:r.available_at,type:"RETROSPECTIVE_FIXED_DIAGNOSTIC",flag,
     production:false,publication_verified:false,confirmed_trade_signal:false,definition_version:"audit-v2-protocol"});
  }}
 }return out;
}
function outcomes(a,ws,h=10){
 return ws.map(w=>{const i=a.findIndex(r=>r.date===w.date),f=a.slice(i+1,i+1+h),full=i>=0&&f.length===h;
  const hit=i>=0?f.find(r=>r.low<=a[i].close*.95):null;
  return {symbol:a[0]?.symbol,...w,horizon:h,observed_sessions:f.length,complete:full,
   down5_hit:full?!!hit:null,down5_observed:!!hit,hit_date:hit?.date??null,
   false_warning:full?!hit:null,terminal_return_pct:full?100*(f.at(-1).close/a[i].close-1):null,
   classification:full?"MATURED":"RIGHT_CENSORED_NOT_COUNTED_AS_FALSE"};
 });
}
function simulate(a,marketRows,actions,fraction,delay=1){
 if(!Number.isFinite(fraction)||fraction<0||fraction>1||!Number.isInteger(delay)||delay<1)throw Error("invalid execution policy");
 const bars=a.filter(r=>r.date>=START&&r.date<=END),mm=Object.fromEntries(marketRows.map(r=>[r.date,r]));
 if(!bars.length)return {daily:[],trades:[],summary:{status:"NO_DATA"}};
 const fee=.0005,slip=.0005,capital=100000,init=bars[0].open*(1+slip),original=capital/(init*(1+fee));
 let shares=original,cash=0,receivable=0,pending=null,clear=0,totalFees=capital-original*init,totalSlip=original*bars[0].open*slip,peak=capital,dd=0;
 const trades=[{symbol:bars[0].symbol,kind:"INITIAL_BUY",signal_date:null,fill_date:bars[0].date,shares:original,price:init,fee:totalFees,slippage:totalSlip,cash_after:0,shares_after:shares}];
 const daily=[];let cycles=0;
 for(let i=0;i<bars.length;i++){
  const r=bars[i],market=mm[r.date];if(!market)throw Error("missing market session");
  // Entitlement is based on pre-open shares; ex-day execution does not change it.
  receivable+=shares*actions.filter(x=>x.kind==="dividends"&&x.date===r.date).reduce((s,x)=>s+x.amount,0);
  if(pending&&i===pending.due){
   if(!(pending.available_at<r.date+"T13:30:00Z"))throw Error("execution before availability");
   const sell=pending.side==="SELL",price=r.open*(sell?1-slip:1+slip);
   const qty=sell?Math.min(pending.qty,shares):Math.min(pending.qty,Math.max(0,original-shares),cash/(price*(1+fee)));
   if(qty>1e-10){const cost=qty*price,fees=cost*fee;
    shares+=sell?-qty:qty;cash+=sell?cost-fees:-cost-fees;totalFees+=fees;totalSlip+=qty*r.open*slip;
    trades.push({symbol:r.symbol,kind:pending.side,signal_date:pending.signal_date,signal_available_at:pending.available_at,fill_date:r.date,shares:qty,price,fee:fees,slippage:qty*r.open*slip,cash_after:cash,shares_after:shares});
   }pending=null;
  }
  if(shares< -1e-7||shares>original+1e-7||cash< -1e-7)throw Error("financing invariant");
  clear=market.sector_flag===false?clear+1:0;
  const prev=i?mm[bars[i-1].date]:marketRows.filter(x=>x.date<r.date).at(-1);
  if(!pending&&fraction>0){
   if(market.sector_flag===true&&prev?.sector_flag!==true&&Math.abs(shares-original)<1e-7){
    pending={side:"SELL",qty:original*fraction,due:i+delay,signal_date:r.date,available_at:market.available_at};cycles++;
   }else if(clear>=3&&r.ma20!==null&&r.close>r.ma20&&shares<original-1e-7&&cash>1e-7){
    pending={side:"BUY",qty:original-shares,due:i+delay,signal_date:r.date,available_at:market.available_at};
   }
  }
  const equity=cash+shares*r.close+receivable;peak=Math.max(peak,equity);dd=Math.max(dd,1-equity/peak);
  daily.push({symbol:r.symbol,date:r.date,fraction,delay,shares,cash,dividend_receivable:receivable,equity,stock_value:shares*r.close,drawdown_pct:100*(equity/peak-1),shares_fraction:shares/original,sector_flag:market.sector_flag,pending:pending?.side??null});
 }
 const last=daily.at(-1);
 return {daily,trades,summary:{symbol:bars[0].symbol,fraction,delay,initial_capital:capital,last_valued_date:last.date,initial_date:bars[0].date,requested_end:END,coverage:"TRUNCATED_OCT22_NOT_NOV2",final_equity:last.equity,return_pct:100*(last.equity/capital-1),maximum_drawdown_pct:100*dd,fees:totalFees,slippage:totalSlip,sales:trades.filter(t=>t.kind==="SELL").length,rebuys:trades.filter(t=>t.kind==="BUY").length,shares_deficit:original-shares,shares_deficit_pct:100*(1-shares/original),cash,dividend_receivable:receivable,unfilled_order:pending?.side??null,cycles,restore_status:shares<original-1e-7?"INCOMPLETE_OR_UNAFFORDABLE":"FULL_SHARES",validated_production_signal:false}};
}
function run(input){
 const m=market(input),ws=warnings(m),catalog=STOCKS.flatMap(s=>outcomes(m.g[s],ws)),ev=STOCKS.flatMap(s=>events(m.g[s]));
 const local=STOCKS.flatMap(s=>events(m.g[s],"2026-10-01",20).map(e=>({...e,view:"NESTED_OCTOBER_DIAGNOSTIC_NOT_INDEPENDENT"})));
 const summaries=[],trades=[],daily=[];
 for(const s of STOCKS){let bh=null;for(const [f,d] of [[0,1],[.05,1],[.1,1],[.05,2],[.1,2]]){const z=simulate(m.g[s],m.all,input.actions.filter(x=>x.symbol===s),f,d);if(f===0)bh=z.summary.final_equity;z.summary.excess_vs_buyhold=z.summary.final_equity-bh;summaries.push(z.summary);trades.push(...z.trades.map(t=>({...t,fraction:f,delay:d})));daily.push(...z.daily);}}
 const stock=m.rows.flatMap(r=>STOCKS.map(s=>{const b=m.lookup[s][r.date];return {...b,actual_production_action:null,production_status:"UNKNOWN_NOT_ACCESSED",retrospective_sector_warning:r.sector_flag};}));
 return {market:m.rows,stock,warnings:ws,catalog,events:ev,local,summary:summaries,trades,daily};
}
return {STOCKS,SEMIS,START,END,group,enrich,market,events,warnings,outcomes,simulate,run};
})();
if(typeof module!=="undefined")module.exports=Audit;
