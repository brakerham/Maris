import path from 'node:path';import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
export default {root:'C:/MarisRouteR4/R4-20261002-164600/workspace/apps/desktop',cacheDir:path.join(own,'evidence/r3/compat-cache'),test:{include:['tests/unit/registry.test.ts'],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,bail:1,reporters:['default','json'],outputFile:{json:path.join(own,'evidence/r3/executor-compat/result.json')}}};
