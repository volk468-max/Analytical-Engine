"use strict";
const fs=require("node:fs"),path=require("node:path");
const root=path.resolve(__dirname,"../../reports/october-risk-failure-audit-v2");
const read=name=>JSON.parse(fs.readFileSync(path.join(root,name),"utf8"));
const A=require("./audit.cjs"),tests=require("./test.cjs")(A,read("inputs.json"));
if(tests.some(x=>!x.passed))throw Error("audit checks failed; no reports written");
const outputs=require("./build.cjs")(A,read("inputs.json"),read("saved-research-signals.json"),read("sources.json"),tests);
for(const [name,content]of Object.entries(outputs)){
 if(path.basename(name)!==name)throw Error("invalid output path");
 fs.writeFileSync(path.join(root,name),content,"utf8");
}
console.log(JSON.stringify({status:"PARTIAL_DATA_ONLY",passed:tests.length,failed:0,files:Object.keys(outputs),requested_end:"2026-11-02",actual_end:"2026-10-22"},null,2));
