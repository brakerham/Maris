import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const own = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(own, '../../../..');
const document = path.join(repo, 'docs/phase-4-d15-r1-bootstrap-advice.md');
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const checkManifest = (manifest, root) => {
  let total = 0, matched = 0;
  const failures = [];
  for (const row of fs.readFileSync(manifest, 'utf8').trim().split(/\r?\n/)) {
    total++;
    const [relative, expected] = row.split('\t');
    const file = path.resolve(root, relative);
    if (file.startsWith(path.resolve(root) + path.sep) && fs.existsSync(file) && hash(file) === expected) matched++;
    else failures.push(relative);
  }
  return { total, matched, failures, manifestSha256: hash(manifest) };
};
if (process.argv[2] === 'prepare') {
  const text = fs.readFileSync(document, 'utf8');
  const links = [...text.matchAll(/\[[^\]\n]+\]\(([^)]+)\)/g)].map(item => item[1]);
  const failures = [];
  for (const link of links) {
    const [file, anchor] = link.split('#');
    const target = path.resolve(path.dirname(document), file);
    if (!fs.existsSync(target)) {
      if (target !== path.join(own, 'delivery.sha256')) failures.push(link);
    } else if (anchor?.startsWith('L') && Number(anchor.slice(1)) > fs.readFileSync(target, 'utf8').split(/\r?\n/).length) failures.push(link);
  }
  let width = null;
  const badTables = [];
  text.split(/\r?\n/).forEach((row, i) => {
    if (!row.startsWith('|')) { width = null; return; }
    const count = row.split('|').length - 2;
    if (width === null) width = count;
    else if (count !== width) badTables.push(i + 1);
  });
  const events = fs.readFileSync(path.join(own, 'attempt-1/results/worker.journal.jsonl'), 'utf8').trim().split(/\r?\n/).map(JSON.parse);
  const first = JSON.parse(fs.readFileSync(path.join(own, 'attempt-0/baseline.json'), 'utf8'));
  const end = JSON.parse(fs.readFileSync(path.join(own, 'attempt-1/end-audit.json'), 'utf8'));
  const extraMetadataMatched = JSON.stringify(first.extraPackages) === JSON.stringify(end.extraPackages);
  const index = stage => events.findIndex(event => event.stage === stage);
  const sequenceValid = events.every((event, i) => event.seq === i + 1 && event.pid === 38832 && event.parentPid === 35256);
  const phasesOrdered = index('actual_import_resolved') < index('main_import_enter') && index('main_import_enter') < index('main_import_resolved') && index('main_import_resolved') < index('act_return');
  const firstReceipt = checkManifest(path.join(own, 'attempt-0/delivery.sha256'), path.join(own, 'attempt-0'));
  const currentFrozen = checkManifest(path.join(own, 'attempt-1/probe-source.sha256'), path.join(own, 'attempt-1'));
  const passed = !failures.length && !badTables.length && !text.includes('\uFFFD') && sequenceValid && phasesOrdered && extraMetadataMatched && !firstReceipt.failures.length && !currentFrozen.failures.length;
  const value = { passed, documentLines: text.split(/\r?\n/).length, localLinks: links.length, missingLinks: failures,
    badTableRows: badTables, replacementCharacters: text.includes('\uFFFD'), sequenceValid, phasesOrdered,
    extraMetadataMatched, firstReceipt, currentFrozen, documentSha256: hash(document),
    deliveryLinkDeferredUntilSeal: true, targetExecuted: false };
  fs.writeFileSync(path.join(own, 'document-check.json'), JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(value));
  if (!passed) process.exitCode = 1;
} else if (process.argv[2] === 'seal') {
  const result = checkManifest(path.join(own, 'delivery.sha256'), repo);
  console.log(JSON.stringify({ delivery: result, reportLinkedManifestExists: true }));
  if (result.failures.length) process.exitCode = 1;
} else throw new Error('d15_r1_verification_mode');
