import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { journal } from './native-journal.mjs';
const own=path.dirname(fileURLToPath(import.meta.url));
const repo=path.resolve(own,'../../../..').replaceAll('\\','/');
const deps='C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
export function configuration(phase) {
  if(phase!==process.env.D16_PHASE) throw Error('d16_phase');
  const record=journal('server'); globalThis.__d16ServerRecord=record;
  record('config_evaluation_enter');
  const root=path.join(own,phase);
  const normalize=value=>String(value||'').replaceAll('\\','/').replace(/^\/@(?:fs|id)\//,'').replace(/^([a-z]):/i,(_,d)=>d.toUpperCase()+':');
  const check=(id,importer)=>{
    let value=normalize(id).split(/[?#]/)[0];
    if(value.startsWith('.')&&importer) value=normalize(path.resolve(path.dirname(importer),value));
    if(value.startsWith(repo+'/apps/')||value.startsWith(repo+'/src/')||value.startsWith(repo+'/tests/independent/')) {
      record('scope_violation'); throw Error('d16_forbidden_product_or_old_target_request');
    }
  };
  const classify=id=>{
    const value=normalize(id).split(/[?#]/)[0];
    if(value===normalize(path.join(root,'initialization.test.ts'))) return 1;
    if(value===`${deps}/jsdom/lib/api.js`||value==='jsdom') return 2;
    if(value===`${deps}/react/index.js`||value==='react') return 3;
    if(value===normalize(path.join(own,'setup.mjs'))) return 4;
    return 0;
  };
  const pre={name:'d16-stage-and-scope',enforce:'pre',
    configResolved(){record('config_resolved');},
    configureServer(){record('server_configured');},
    resolveId(source,importer){check(source,importer);const ordinal=classify(source);if(ordinal) record('resolve_hook_seen',{ordinal});return null;},
    load(id){check(id);const ordinal=classify(id);if(ordinal) record('load_hook_seen',{ordinal});return null;},
    transform(code,id){check(id);const ordinal=classify(id);if(ordinal) record('transform_pre_seen',{ordinal});return null;}
  };
  const post={name:'d16-transform-post',enforce:'post',transform(code,id){const ordinal=classify(id);if(ordinal) record('transform_post_seen',{ordinal});return null;}};
  const config={root,cacheDir:path.join(root,'cache'),plugins:[pre,post],esbuild:{jsx:'automatic'},
    resolve:{alias:[
      {find:/^vitest$/,replacement:`${deps}/vitest/dist/index.js`},
      {find:'react-router',replacement:`${deps}/react-router`},
      {find:'react-dom',replacement:`${deps}/react-dom`},
      {find:'react',replacement:`${deps}/react`},
      {find:'zod',replacement:`${deps}/zod`},
      {find:'jsdom',replacement:`${deps}/jsdom/lib/api.js`}
    ]},test:{include:['initialization.test.ts'],setupFiles:[path.join(own,'setup.mjs')],sequence:{setupFiles:'list'},
      environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,isolate:true,bail:1,testTimeout:10000,hookTimeout:10000,
      reporters:[path.join(own,'reporter.mjs')]}};
  record('config_object_ready');return config;
}
