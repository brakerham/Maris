import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/MarisRouteR4/R4-20261002-164600/workspace/node_modules';
const phase=process.env.C12_R3_PHASE;
const files={'original-path':['r2-remaining.test.ts'],'path-independent':['r3-path.test.ts'],'ui04-independent':['r3-ui04.test.ts'],'storage-build-independent':['r3-storage-build.test.ts'],'remaining-independent':['r3-remaining.test.tsx']};
if(!Object.hasOwn(files,phase??''))throw Error('r3_phase_required');
export default {root:own,cacheDir:path.join(own,'evidence/r3/cache'),esbuild:{jsx:'automatic'},resolve:{alias:[
 {find:/^vitest$/,replacement:`${deps}/vitest/dist/index.js`},
 {find:'zod',replacement:`${deps}/zod`},{find:'react-dom',replacement:`${deps}/react-dom`},
 {find:'react-router',replacement:`${deps}/react-router`},{find:'react',replacement:`${deps}/react`},
 {find:'jsdom',replacement:`${deps}/jsdom/lib/api.js`},
 {find:'electron',replacement:`${deps}/electron/index.js`}
]},test:{include:files[phase],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,bail:1,testTimeout:5000,reporters:['default','json'],outputFile:{json:path.join(own,`evidence/r3/${phase}/result.json`)}}};
