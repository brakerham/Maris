import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const repo=path.resolve(own,'../../../..');
const report=path.join(repo,'docs/phase-4-d16-harness-and-acceptance-advice.md');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const failures=[]; const requireCheck=(ok,label)=>{if(!ok)failures.push(label);};
const content=fs.readFileSync(report,'utf8');let links=0;
const deferred=new Set(['delivery.sha256','document-check.json']);
for(const match of content.matchAll(/\[[^\]\n]+\]\(([^)\n]+)\)/g)){
 const [relative,anchor]=match[1].split('#');if(/^[a-z]+:\/\//i.test(relative))continue;
 const target=path.resolve(path.dirname(report),relative);links++;
 if(deferred.has(path.basename(target))&&!fs.existsSync(target))continue;
 requireCheck(fs.existsSync(target),`link:${relative}`);
 if(anchor?.startsWith('L')&&fs.existsSync(target))requireCheck(Number(anchor.slice(1))<=fs.readFileSync(target,'utf8').split(/\r?\n/).length,`anchor:${relative}`);
}
requireCheck(!content.includes('\uFFFD'),'report_encoding');
requireCheck(!content.split(/\r?\n/).some(line=>/[ \t]+$/.test(line)),'report_trailing_whitespace');
let width=0,tables=0;
for(const line of content.split(/\r?\n/)){
 if(!line.startsWith('|')){width=0;continue;}
 const cells=line.split('|').length;
 if(!width){width=cells;tables++;}else requireCheck(cells===width,'table_width');
}
const phases=[];
for(const phase of ['e1','e2']){
 const manifest=fs.readFileSync(path.join(own,phase,'source.sha256'),'utf8');let sourceMatched=0;
 for(const line of manifest.trim().split(/\r?\n/)){
  const [relative,digest]=line.split('\t');const equal=hash(path.join(own,relative))===digest;
  requireCheck(equal,`${phase}:source:${relative}`);if(equal)sourceMatched++;
 }
 const receipt=JSON.parse(fs.readFileSync(path.join(own,phase,'results/process.json'),'utf8'));
 requireCheck(receipt.rootExitCode===0&&receipt.rootExited&&receipt.workerExited&&receipt.workerParentVerified,`${phase}:exits`);
 requireCheck(!receipt.scopeViolation&&!receipt.timedOut&&receipt.mainImportRequests===0&&receipt.injectionLoaderCalls===0&&receipt.fixtureEvaluations===0,`${phase}:scope`);
 const journals={};
 for(const kind of ['worker','server','controller']){
  const rows=fs.readFileSync(path.join(own,phase,`results/${kind}.journal.jsonl`),'utf8').trim().split(/\r?\n/).map(JSON.parse);
  requireCheck(rows.every((row,index)=>row.seq===index+1),`${phase}:${kind}:seq`);
  requireCheck(!rows.some(row=>row.stage==='scope_violation'),`${phase}:${kind}:scope`);
  if(kind==='worker'){
   requireCheck(rows.every(row=>row.pid===receipt.workerPid&&row.parentPid===receipt.rootPid),`${phase}:identity`);
   requireCheck(rows.some(row=>row.stage==='body_enter')&&rows.some(row=>row.stage==='body_finished'),`${phase}:body`);
  }
  if(kind==='server')requireCheck(rows.some(row=>row.stage==='run_end'&&row.unhandledCount===0&&row.moduleCount===1),`${phase}:run_end`);
  journals[kind]=rows.length;
 }
 phases.push({phase,sourceMatched,journals,durationMs:receipt.durationMs});
}
const audit=JSON.parse(fs.readFileSync(path.join(own,'end-audit.json'),'utf8'));
requireCheck(audit.passed&&audit.input.matched===595&&audit.baselineSame,'end_audit');
const cleanup=JSON.parse(fs.readFileSync(path.join(own,'cache-cleanup.json'),'utf8'));
requireCheck(cleanup.targets.every(item=>item.absentAfter&&!fs.existsSync(path.join(own,item.relativePath))),'cache_cleanup');
const result={passed:failures.length===0,localLinks:links,tables,phases,failures,deferredUntilSeal:[...deferred],scope:'static_only_no_target_execution'};
fs.writeFileSync(path.join(own,'document-check.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result));if(failures.length)process.exitCode=1;
