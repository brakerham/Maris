import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const ts = require('C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/typescript/lib/typescript.js');
const files = ['observations.ts', 'p1.test.ts', 'p2.test.ts', 'p3.test.tsx'];
const results = files.map(file => {
  const result = ts.transpileModule(fs.readFileSync(path.join(own, file), 'utf8'), {
    fileName: file, reportDiagnostics: true,
    compilerOptions: { target: ts.ScriptTarget.ESNext, module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX }
  });
  return { file, syntacticErrors: (result.diagnostics || []).filter(d => d.category === ts.DiagnosticCategory.Error).map(d => ({ code: d.code })) };
});
const receipt = { kind: 'syntax_only_no_target_execution', typescriptVersion: ts.version, results };
fs.writeFileSync(path.join(own, 'syntax-check.json'), JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify(receipt));
if (results.some(r => r.syntacticErrors.length)) process.exitCode = 1;
