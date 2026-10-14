import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/MarisModulesR6/R6-20261013-002100/workspace/node_modules';
export default {
 root:own,cacheDir:path.join(own,'evidence/r8-r1/cache/public'),
 esbuild:{jsx:'automatic'},
 resolve:{alias:[{find:/^vitest$/,replacement:deps+'/vitest/dist/index.js'},...['react-router','react-dom','react','zod','@testing-library/react','@testing-library/user-event'].map(find=>({find,replacement:deps+'/'+find}))]},
 test:{include:['r8-r1-remaining.test.ts'],
 setupFiles:[path.join(own,'r8-r1-public-setup.mjs')],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,isolate:true,bail:1,testTimeout:20000,hookTimeout:5000,
 reporters:[path.join(own,'r8-r1-public-reporter.mjs')]}
};
