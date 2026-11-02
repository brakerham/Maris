import {writeFileSync,readFileSync} from 'node:fs';
export default class Reporter {
 onTestRunEnd(modules,errors){
  const nodes=[];function visit(t){if(t.type==='test')nodes.push({id:t.name.split(' | ')[0],state:t.result?.state??'not_run',durationMs:t.result?.duration??null,errors:(t.result?.errors??[]).map(e=>({name:['Error','CompareError','TypeError','AssertionError'].includes(e.name)?e.name:'other',timeout:/timed out/i.test(e.message??'')}))});for(const c of t.tasks??[])visit(c);}modules.forEach(m=>visit(m.task));
  let events=[],journalError=null;try{events=readFileSync(process.env.R11_OUTPUT+'/journal.jsonl','utf8').trim().split('\n').map(JSON.parse);}catch(e){if(process.env.R11_MODE==='independent')journalError=e.name;}
  const enters=events.filter(e=>e.event==='assert_enter'),ends=events.filter(e=>e.event==='assert_terminal'),terminals=events.filter(e=>e.event==='node_terminal');
  const result={mode:process.env.R11_MODE,nodes,passed:nodes.filter(n=>n.state==='pass').length,failed:nodes.filter(n=>n.state==='fail').length,notRun:nodes.filter(n=>!['pass','fail'].includes(n.state)).length,unhandledErrors:errors.length,moduleErrors:modules.reduce((s,m)=>s+(m.task.result?.errors?.length??0),0),journalError,formalComparisons:ends.length,comparisonsPassed:ends.filter(e=>e.passed).length,paired:enters.length===ends.length&&enters.every(e=>ends.filter(x=>x.id===e.id).length===1),firstFailure:events.find(e=>e.event==='error'||e.event==='assert_terminal'&&!e.passed)??null,nodeTerminals:terminals};
  writeFileSync(process.env.R11_OUTPUT+'/result.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({event:'r10_result',passed:result.passed,failed:result.failed,notRun:result.notRun})+'\n');
 }
}
