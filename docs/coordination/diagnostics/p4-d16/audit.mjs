import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));const repo=path.resolve(own,'../../../..');
const external='C:/MarisLazyR5/R5-20261002-222300';const deps=`${external}/workspace/node_modules`;
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const check=(file,root,allowed=[])=>{
 const bytes=fs.readFileSync(file);const content=bytes.toString('utf8');const lines=content.replace(/^\uFEFF/,'').trim().split(/\r?\n/);
 const result={total:lines.length,matched:0,authorizedChanged:[],failures:[],manifestSha256:hash(file)};
 for(const line of lines){const cells=line.split('\t');const rel=cells[0].replaceAll('\\','/');const target=path.resolve(root,rel);
   if(![2,3].includes(cells.length)||!target.startsWith(path.resolve(root)+path.sep)||!fs.existsSync(target)){result.failures.push(rel);continue;}
   if(hash(target)===cells.at(-1))result.matched++;else if(allowed.includes(rel))result.authorizedChanged.push(rel);else result.failures.push(rel);}
 return result;
};
const mode=process.argv[2];if(!/^(baseline|e[123]-audit|end-audit)$/.test(mode||''))throw Error('d16_audit_mode');
const input=check(path.join(repo,'docs/coordination/snapshots/p4-d16-start.sha256'),repo,['docs/coordination/agents/technical-adviser.md']);
const r3=path.join(repo,'tests/independent/desktop');
const delivery=check(path.join(r3,'evidence/r4-r3/delivery.sha256'),repo);
const frozen=check(path.join(r3,'evidence/r4-r3/cold-source.sha256'),r3);
const oldD15=check(path.join(repo,'docs/coordination/diagnostics/p4-d15-r1/delivery.sha256'),repo,['docs/coordination/agents/technical-adviser.md']);
const source=check(`${external}/evidence/static/workspace-source.sha256`,`${external}/workspace`);
const out=check(`${external}/evidence/static/out-manifest-v4.tsv`,`${external}/workspace/apps/desktop/out/Maris-win32-x64`);
const expected={'vitest':'5.0.2','vite':'7.3.6','react':'19.3.0','react-dom':'19.3.0','react-router':'8.4.0','jsdom':'30.1.1','typescript':'6.0.3'};
const packages=Object.entries(expected).map(([name,version])=>{const file=`${deps}/${name}/package.json`;const actual=JSON.parse(fs.readFileSync(file,'utf8'));return{name,version:actual.version,expectedMatched:actual.version===version,sha256:hash(file)};});
const physical=Object.fromEntries(['react','react-dom','react-router'].map(name=>[name,fs.realpathSync(`${deps}/${name}`)]));
const reactResolutions=['react-dom','react-router'].map(name=>({importer:name,sameReact:fs.realpathSync(createRequire(`${deps}/${name}/package.json`).resolve('react'))===fs.realpathSync(`${deps}/react/index.js`)}));
const nodeSha256=hash(`${external}/tools/node/node.exe`);
const baselineFile=path.join(own,'baseline.json');let baselineSame=true;
if(mode!=='baseline'){const base=JSON.parse(fs.readFileSync(baselineFile,'utf8'));baselineSame=JSON.stringify(packages)===JSON.stringify(base.packages)&&nodeSha256===base.nodeSha256;}
const git=spawnSync('git',['diff','--cached','--name-only'],{cwd:repo,encoding:'utf8',windowsHide:true});
const passed=[input,delivery,frozen,oldD15,source,out].every(x=>!x.failures.length)&&packages.every(x=>x.expectedMatched)&&reactResolutions.every(x=>x.sameReact)&&process.version==='v24.21.0'&&baselineSame&&git.status===0&&!git.stdout.trim();
const result={passed,input,r3Delivery:delivery,r3Frozen:frozen,oldD15,externalSource:source,externalOut:out,packages,nodeVersion:process.version,nodeSha256,
  physicalRootsBound:Object.values(physical).every(p=>p.replaceAll('\\','/').startsWith(deps+'/')),reactResolutions,baselineSame,stagedCount:git.stdout.trim()?git.stdout.trim().split(/\r?\n/).length:0,gitReadWarning:Boolean(git.stderr.trim())};
fs.writeFileSync(path.join(own,`${mode}.json`),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed,inputMatched:input.matched,authorized:input.authorizedChanged,r3DeliveryMatched:delivery.matched,r3FrozenMatched:frozen.matched,oldD15Matched:oldD15.matched,sourceMatched:source.matched,outMatched:out.matched,nodeVersion:process.version,baselineSame}));if(!passed)process.exitCode=1;
