import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/MarisQuitR7/R7-20261014-191500/workspace/node_modules';
export default {root:own,cacheDir:'C:/MarisC12/C12-R9-QUIT-20261016-011200/cache/lifecycle',
 resolve:{alias:[{find:/^vitest$/,replacement:deps+'/vitest/dist/index.js'},{find:/^electron$/,replacement:deps+'/electron/index.js'},{find:'zod',replacement:deps+'/zod'}]},
 test:{include:['r9-quit-lifecycle.test.ts'],setupFiles:[path.join(own,'r9-quit-setup.mjs')],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,isolate:true,bail:1,testTimeout:20000,hookTimeout:5000,reporters:[path.join(own,'r9-quit-reporter.mjs')]}};
