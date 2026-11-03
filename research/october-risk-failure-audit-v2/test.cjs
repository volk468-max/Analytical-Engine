"use strict";
function runTests(A){
 const checks=[];function test(name,fn){try{fn();checks.push({name,passed:true});}catch(e){checks.push({name,passed:false,error:String(e)});}}
 function ok(x,msg="assertion failed"){if(!x)throw Error(msg);}
 function near(x,y,t=1e-7){ok(Math.abs(x-y)<t,"not close: "+x+" / "+y);}
 function fixture(closes,flags){let d=new Date("2026-09-01T00:00:00Z"),bars=[],market=[];for(let i=0;i<closes.length;i++){while([0,6].includes(d.getUTCDay()))d.setUTCDate(d.getUTCDate()+1);const date=d.toISOString().slice(0,10),available_at=new Date(+d+86400000).toISOString();bars.push({symbol:"AMD",date,open:closes[i],high:closes[i]+1,low:closes[i]-1,close:closes[i],ma20:closes[i]-1,available_at});market.push({date,available_at,sector_flag:flags[i]});d.setUTCDate(d.getUTCDate()+1);}return {bars,market};}
 test("initial buy includes fee and adverse slippage",()=>{let f=fixture([100,100],[false,false]),r=A.simulate(f.bars,f.market,[],0);near(r.trades[0].price,100.05);near(r.trades[0].shares,100000/(100.05*1.0005));});
 test("signal cannot fill same session",()=>{let f=fixture([100,100,90],[false,true,true]),r=A.simulate(f.bars,f.market,[],.1);ok(r.trades[1].signal_date<r.trades[1].fill_date);ok(r.trades[1].fill_date===f.bars[2].date);});
 test("persistent warning causes one sale",()=>{let f=fixture([100,100,90,80,70],[false,true,true,true,true]),r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.sales===1);});
 test("adverse sell slippage and fee",()=>{let f=fixture([100,100,90],[false,true,true]),r=A.simulate(f.bars,f.market,[],.1),t=r.trades[1];near(t.price,90*.9995);near(t.fee,t.shares*t.price*.0005);});
 test("additional session delay changes fill date",()=>{let f=fixture([100,100,90,80],[false,true,true,true]),r=A.simulate(f.bars,f.market,[],.1,2);ok(r.trades[1].fill_date===f.bars[3].date);});
 test("end-of-history order remains unfilled",()=>{let f=fixture([100,100],[false,true]),r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.sales===0&&r.summary.unfilled_order==="SELL");});
 test("gap executes one order at actual next open",()=>{let f=fixture([100,100,50],[false,true,true]),r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.sales===1);near(r.trades[1].price,49.975);});
 test("three clear closes plus trend required for restoration",()=>{let f=fixture([100,100,80,80,80,80,80],[false,true,true,false,false,false,false]),r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.rebuys===1);ok(r.trades[2].signal_date===f.bars[5].date);});
 test("clear signals without above-MA20 do not restore",()=>{let f=fixture([100,100,80,80,80,80,80],[false,true,true,false,false,false,false]);f.bars.forEach(r=>r.ma20=101);let r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.rebuys===0);});
 test("expensive restoration caps shares to available cash",()=>{let f=fixture([100,100,80,120,120,120,120],[false,true,true,false,false,false,false]),r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.rebuys===1&&r.summary.shares_deficit>0);ok(Math.abs(r.summary.cash)<1e-7);});
 test("cash-limited incomplete restoration blocks next cycle under frozen rule",()=>{let f=fixture([100,100,80,120,120,120,120,120,80],[false,true,true,false,false,false,false,true,true]),r=A.simulate(f.bars,f.market,[],.1);ok(r.summary.sales===1&&r.summary.shares_deficit>0);});
 test("no short position or borrowing",()=>{let f=fixture([100,100,80,120,120,120,120],[false,true,true,false,false,false,false]),r=A.simulate(f.bars,f.market,[],.1);ok(r.daily.every(d=>d.shares>=0&&d.cash>=-1e-7&&d.shares_fraction<=1+1e-9));});
 test("dividend belongs to pre-open shares on sale ex-day",()=>{let f=fixture([100,100,90],[false,true,true]),r=A.simulate(f.bars,f.market,[{date:f.bars[2].date,kind:"dividends",amount:1}],.1);near(r.summary.dividend_receivable,r.trades[0].shares);});
 test("NAV reconciles cash stock and dividend receivable",()=>{let f=fixture([100,100,90,110],[false,true,true,true]),r=A.simulate(f.bars,f.market,[],.1);r.daily.forEach(d=>near(d.equity,d.cash+d.stock_value+d.dividend_receivable));});
 test("future suffix does not change executed prefix",()=>{let f=fixture([100,100,90,110,200],[false,true,true,true,false]),p=A.simulate(f.bars.slice(0,4),f.market,[],.1),r=A.simulate(f.bars,f.market,[],.1);ok(JSON.stringify(p.daily)===JSON.stringify(r.daily.slice(0,4)));});
 test("prior support excludes current and later bars",()=>{let f=fixture([100,90,20],[false,false,false]),r=A.enrich(f.bars);near(r[1].prior_support,99);near(r[2].prior_support,89);});
 test("conditional main AUTO-support self-inclusion masks breach",()=>{const prior=[{low:99,high:102,close:100}],current={low:89,high:92,close:90};near(Math.min(...prior.map(x=>x.low)),99);ok(90<99);ok(!(90<Math.min(...[...prior,current].map(x=>x.low))));});
 test("nested declines form one event until recovery",()=>{let f=fixture([100,94,96,85,100,95],[false,false,false,false,false,false]),e=A.events(f.bars);ok(e.length===2&&e[0].status==="RECOVERED");near(e[0].depth_pct,15);});
 test("unfinished event has no fabricated recovery",()=>{let f=fixture([100,90,80],[false,false,false]),e=A.events(f.bars);ok(e.length===1&&e[0].status==="ONGOING_CENSORED"&&e[0].recovery_date===null);});
 test("short outcome horizon is not a false warning",()=>{let f=fixture([100,110,120],[false,false,false]),r=A.outcomes(f.bars,[{date:f.bars[0].date}],10);ok(!r[0].complete&&r[0].false_warning===null);});
 test("target is low hit within horizon not terminal return",()=>{let f=fixture([100,94,110],[false,false,false]),r=A.outcomes(f.bars,[{date:f.bars[0].date}],2);ok(r[0].down5_hit&&r[0].terminal_return_pct>0);});
 test("duplicate sessions rejected",()=>{let f=fixture([100],[false]),threw=false;try{A.group([...f.bars,...f.bars]);}catch{threw=true;}ok(threw);});
 test("zero-delay execution rejected",()=>{let f=fixture([100],[false]),threw=false;try{A.simulate(f.bars,f.market,[],.1,0);}catch{threw=true;}ok(threw);});
 return checks;
}
if(typeof module!=="undefined"){
 module.exports=runTests;
 if(require.main===module){const r=runTests(require("./audit.cjs"));console.log(JSON.stringify(r,null,2));if(r.some(x=>!x.passed))process.exitCode=1;}
}
