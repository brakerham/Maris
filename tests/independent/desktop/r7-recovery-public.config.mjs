import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules';
export default {
 root:own,cacheDir:path.join(own,'evidence/r7-recovery/cache/public'),
 esbuild:{jsx:'automatic'},
 resolve:{alias:[{find:/^vitest$/,replacement:deps+'/vitest/dist/index.js'},...['react-router','react-dom','react','zod','@testing-library/react','@testing-library/user-event'].map(find=>({find,replacement:deps+'/'+find}))]},
 test:{include:['r7-recovery-public.test.ts'],
 setupFiles:[path.join(own,'r7-recovery-public-setup.mjs')],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,isolate:true,bail:1,testTimeout:12000,hookTimeout:12000,
 reporters:[path.join(own,'r7-recovery-public-reporter.mjs')]}
};
