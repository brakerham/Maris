import { openSync, writeSync, fsyncSync, closeSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../..');
const target = `${root.replaceAll('\\', '/')}/apps/desktop/src/modules/daily-finance/DailyFinancePage`;
const importerTarget = `${root.replaceAll('\\', '/')}/apps/desktop/src/renderer/module-routes.tsx`;
export const fixture = path.join(own, 'r4-r3-failing-page.tsx');
const normalize = value => {
  if (typeof value !== 'string') return '';
  let slashes = value.replaceAll('\\', '/');
  // Strip just one known Vite transport wrapper, never decode arbitrary URLs.
  if (slashes.startsWith('/@id/') || slashes.startsWith('/@fs/')) slashes = slashes.slice(5);
  return slashes.replace(/^([a-z]):/i, (_, drive) => drive.toUpperCase() + ':');
};
// Only exact canonical absolute IDs, or the one relative request from the
// exact production importer. No wildcard, query, cache busting or directory alias.
export function classify(source, importer) {
  const normalized = normalize(source), caller = normalize(importer);
  const clean = normalized.split(/[?#]/, 1)[0];
  const absolute = clean === normalize(target) || clean === normalize(target) + '.tsx';
  const relative = clean === '../modules/daily-finance/DailyFinancePage' && caller === normalize(importerTarget);
  if (!absolute && !relative) return null;
  return {targetOrdinal: 1, fixtureOrdinal: 1, absoluteRequest: absolute, relativeRequest: relative,
    knownExtension: clean.endsWith('.tsx'), importerBound: caller === normalize(importerTarget),
    unsupportedQuery: normalized !== clean};
}
export function persistentImportResolver(phase) {
  let seq = 0; const started = performance.now();
  const journal = path.join(own, `evidence/r4-r3/${phase}/resolver.journal.jsonl`);
  return {name: 'c12-r3-exact-persistent-import', enforce: 'pre',
    resolveId(source, importer) {
      const match = classify(source, importer);
      if (!match) return null;
      const fd = openSync(journal, 'a');
      try {
        const bytes = Buffer.from(JSON.stringify({seq: ++seq, elapsedMs: performance.now() - started,
          stage: 'target_module_mapping', pid: process.pid, parentPid: process.ppid, ...match}) + '\n');
        for (let offset = 0; offset < bytes.length;) offset += writeSync(fd, bytes, offset, bytes.length - offset);
        fsyncSync(fd);
      } finally { closeSync(fd); }
      if (match.unsupportedQuery) throw Error('c12_r3_unsupported_target_query');
      return fixture;
    }
  };
}
