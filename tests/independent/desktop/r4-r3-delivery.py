"""Audit the stopped R3 delivery; never import or execute a test target."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import mmap
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'tests/independent/desktop/evidence/r4-r3'
EXT = Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
ROLE = 'docs/coordination/agents/tester.md'
MATRIX = 'docs/testing/phase-4-modular-agent-host-test-matrix.md'
OLD = 'docs/testing/phase-4-c12-windows-shell-report.md'
MANUAL = 'docs/testing/phase-4-c12-manual-checklist.md'
REPORT = 'docs/testing/phase-4-c12-r4-r3-persistent-import-windows-report.md'
ALLOWED = {ROLE, MATRIX, OLD, MANUAL}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name):
    return json.loads((OWN / name).read_text(encoding='utf-8-sig'))


def save(name, data):
    (OWN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def entries(path):
    return [line.split('\t') for line in path.read_text(encoding='utf-8-sig').splitlines()]


def verify_manifest(path, base):
    items = entries(path)
    assert len(items) == len({item[0] for item in items}), str(path)
    for item in items:
        assert sha((base / item[0]).read_bytes()) == item[-1], item[0]
    return len(items)


def journal(name):
    raw = (OWN / name).read_bytes()
    assert raw.endswith(b'\n'), name
    items = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    assert [item['seq'] for item in items] == list(range(1, len(items) + 1)), name
    return items


start = load('start-audit.json')
manifest = ROOT / 'docs/coordination/snapshots/p4-c12-r4-r3-start.sha256'
assert sha(manifest.read_bytes()) == start['manifest_sha256']
matched, changed, missing, bad = [], [], [], []
for name, digest in entries(manifest):
    path = ROOT / name
    if not path.is_file():
        missing.append(name)
    elif sha(path.read_bytes()) == digest:
        matched.append(name)
    elif name in ALLOWED:
        changed.append(name)
    else:
        bad.append(name)
assert len(matched) == 540 and set(changed) == ALLOWED and not bad and not missing

artifacts = {name: sha((EXT / name).read_bytes()) for name in start['artifacts']}
assert artifacts == start['artifacts']
with (EXT / 'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as stream:
    with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mapping:
        sentinel = mapping.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')
        assert sentinel >= 0
        index = sentinel + 32
        fuses = {'version': mapping[index], 'wire': list(mapping[index + 2:index + 2 + mapping[index + 1]])}
assert fuses == start['fuses']
counts = {}
for kind, name, base in [
    ('source', 'workspace-source.sha256', EXT),
    ('out', 'out-manifest-v4.tsv', EXT / 'apps/desktop/out/Maris-win32-x64'),
    ('resources', 'python-resources-v4.tsv', EXT / 'apps/desktop/out/Maris-win32-x64/resources'),
]:
    file = EXT.parent / 'evidence/static' / name
    assert sha(file.read_bytes()) == start[kind]['manifest_sha256']
    counts[kind] = verify_manifest(file, base)
assert counts == {'source': 389, 'out': 140, 'resources': 67}
metadata = load('static-preflight.json')['versions']
assert len(metadata) == 7
assert all(sha((Path(item['physicalRoot']) / 'package.json').read_bytes()) == item['packageJsonSha256'] for item in metadata.values())
assert verify_manifest(OWN / 'cold-source.sha256', ROOT / 'tests/independent/desktop') == 15
assert verify_manifest(OWN / 'cold-trace-first.sha256', ROOT) == 5

baseline = load('baseline.json')
matrix_bytes = (ROOT / MATRIX).read_bytes()
cases = [[cell.strip() for cell in line.strip().strip('|').split('|')]
         for line in matrix_bytes.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-', line)]
assert len(cases) == len({row[0] for row in cases}) == 120 and all(len(row) == 12 for row in cases)
assert [row[:11] for row in cases] == [row[:11] for row in baseline['cases']]
assert [row[11] for row in cases] == [row[11] for row in baseline['cases']]
a, z = matrix_bytes.index(b'### 5.2'), matrix_bytes.index(b'### 5.3')
assert sha(matrix_bytes[:a]) == baseline['outside_b_prefix'] and sha(matrix_bytes[z:]) == baseline['outside_b_suffix']
prefixes, append_segments = {}, {}
for name, old in baseline['append_files'].items():
    data = (ROOT / name).read_bytes()
    assert sha(data[:old['bytes']]) == old['sha256'], name
    append_segments[name] = data[old['bytes']:].decode('utf-8')
    prefixes[name] = {'prefixPreserved': True, 'originalBytes': old['bytes'], 'appendedBytes': len(data) - old['bytes']}
report = (ROOT / REPORT).read_text(encoding='utf-8')
ids = re.findall(r'^### (P4B-[A-Z]+-\d+) — ', report, re.M)
assert len(ids) == len(set(ids)) == 24 and set(ids) == {row[0] for row in cases if row[1] == 'B'}
assert all(row[9] in report for row in cases if row[1] == 'B')
states = {phase: dict(Counter(row[11] for row in cases if row[1] == phase)) for phase in 'ABCD'}
assert states == {'A': {'passed': 64}, 'B': {'blocked': 19, 'failed': 1, 'not_run': 4}, 'C': {'not_run': 20}, 'D': {'not_run': 12}}

p_events = journal('injection/worker.journal.jsonl')
p_mapping = journal('injection/resolver.journal.jsonl')
p_process, p_result = load('injection/process.json'), load('injection/result.json')
assert len(p_events) == 13 and len(p_mapping) == 1
assert all(event['pid'] == p_process['workerPid'] and event['parentPid'] == p_process['rootPid'] for event in p_events)
calls = [event for event in p_events if event['stage'] == 'p_call_terminal']
assert [event['callSeq'] for event in calls] == [1, 2, 3]
assert all(event['rejected'] and event['safeModuleCode'] and not event['virtualRawError'] for event in calls)
call3 = next(event for event in p_events if event['stage'] == 'p_call_enter' and event['callSeq'] == 3)
assert call3['seq'] > max(event['seq'] for event in calls[:2])
fixture = [event for event in p_events if event['stage'] == 'fixture_evaluation_enter']
assert len(fixture) == 1 and fixture[0]['count'] == 1
assert p_mapping[0]['relativeRequest'] and p_mapping[0]['importerBound'] and not p_mapping[0]['unsupportedQuery']
assert p_mapping[0]['targetOrdinal'] == p_mapping[0]['fixtureOrdinal'] == 1
assert p_result['numTotalTests'] == p_result['numPassedTests'] == 1 and p_result['numFailedTests'] == 0
assert not p_result['moduleErrorCount'] and not p_result['unhandledErrorCount']
assert p_process['rootExitCode'] == 0 and not p_process['timedOut'] and p_process['mainImportRequests'] == 0
assert not p_process['forcedRootTermination'] and not p_process['forcedWorkerTermination']

a_events = journal('cold-trace/worker.journal.jsonl')
a_process = load('cold-trace/process.json')
assert [event['stage'] for event in a_events] == ['worker_start', 'journal_ready']
assert all(event['pid'] == a_process['workerPid'] and event['parentPid'] == a_process['rootPid'] for event in a_events)
assert a_process['timedOut'] and a_process['forcedRootTermination'] and a_process['lastWorkerStage'] == 'journal_ready'
assert a_process['mainImportRequests'] == a_process['injectionLoaderCalls'] == a_process['fixtureEvaluations'] == 0
assert not (OWN / 'cold-trace/result.json').exists() and not (OWN / 'cold-trace/resolver.journal.jsonl').exists()
assert not (OWN / 'cold-public').exists()
for process in [p_process, a_process]:
    assert process['rootExited'] and process['workerExited'] and process['workerParentVerified'] and process['streamsComplete']
    assert process['durationMs'] <= process['processDeadlineMs'] == 15000
    assert process['totalCliInvocationsThisPhase'] == 1 and process['correctionBudgetUsed'] == 0
    assert process['electronStarts'] == process['servicesStarted'] == process['packages'] == 0
assert load('pre-main-no-retry-ruling.json')['correctionPermittedOnThisEvidence'] is False
cleanup = load('temp-cleanup.json')
assert cleanup['pathBoundaryVerified'] and cleanup['noReparseVerified'] and cleanup['absentAfter'] and not (OWN / 'cache').exists()
resources = load('resource-observation.json')
assert len(resources['phases']) == 2 and all(item['rootGone'] and item['workerGone'] and item['workerExit'] is None for item in resources['phases'])
assert resources['enumerationVerified'] is False and resources['safeErrorKind'] == 'CimException'

old_r2_preserved, old_r2_changed = [], []
for name, digest in entries(ROOT / 'tests/independent/desktop/evidence/r4-r2/delivery.sha256'):
    if sha((ROOT / name).read_bytes()) == digest:
        old_r2_preserved.append(name)
    else:
        old_r2_changed.append(name)
assert len(old_r2_preserved) == 33 and set(old_r2_changed) == ALLOWED
role = (ROOT / ROLE).read_text(encoding='utf-8')
assert '- 状态：`blocked`' in role and '- 运行状态：`finished`' in role

staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, capture_output=True, text=True, check=True)
assert not staged.stdout.splitlines()
diff = subprocess.run(['git', 'diff', '--check', '--', ROLE, MATRIX, OLD, MANUAL, REPORT,
                       'tests/independent/desktop/r4-r3-*', 'tests/independent/desktop/evidence/r4-r3'],
                      cwd=ROOT, capture_output=True, text=True)
(OWN / 'diff-check.log').write_text(diff.stdout + diff.stderr, encoding='utf-8')
assert diff.returncode == 0

new_sources = [file for file in (ROOT / 'tests/independent/desktop').glob('r4-r3-*') if file.is_file()]
new_evidence = [file for file in OWN.rglob('*') if file.is_file() and file.name != 'delivery.sha256']
full_scan = new_sources + [ROOT / REPORT] + new_evidence
segments = {file.relative_to(ROOT).as_posix(): file.read_text(encoding='utf-8-sig') for file in full_scan}
segments.update(append_segments)
segments[MATRIX + ':B-only'] = matrix_bytes[a:z].decode('utf-8')
segments[ROLE + ':R3-only'] = role[:role.index('### 2026-10-03 03:43')]
whitespace_issues = [{'path': name, 'lineInScannedSegment': index}
                     for name, text in segments.items() for index, line in enumerate(text.splitlines(), 1)
                     if line.rstrip(' \t') != line]
save('whitespace-check.json', {'fullNewFiles': len(full_scan), 'scannedSegments': len(segments),
                             'issues': whitespace_issues, 'scope': 'new R3 files in full; append segments, B only and R3 role prefix; old files read-only'})
assert not whitespace_issues, whitespace_issues

audit = {'entries': 544, 'unchanged': len(matched), 'authorizedChanged': sorted(changed),
         'unauthorizedMismatch': bad, 'missing': missing, 'stagedPaths': [], 'manifestSha256': sha(manifest.read_bytes()),
         'artifacts': artifacts, 'fuses': fuses, 'packageInputsMatched': counts,
         'oldIndependentFilesUnchanged': sum(name.startswith('tests/independent/desktop/') for name in matched),
         'oldD15DiagnosticFilesUnchanged': sum(name.startswith('docs/coordination/diagnostics/p4-d15') for name in matched),
         'oldR2DeliveryUnchanged': len(old_r2_preserved), 'oldR2AuthorizedSharedChanges': sorted(old_r2_changed),
         'frozenColdSourceFilesMatched': 15, 'fixedDependencyMetadataMatched': len(metadata)}
save('end-audit.json', audit)
verification = {'matrixUniqueIds': 120, 'columns': 12, 'firstElevenColumnsPreserved': True,
                'allStatusesPreserved': True, 'matrixStates': states, 'outsideBBytesPreserved': True,
                'appendFiles': prefixes, 'reportFullCaseMappings': 24, 'P': '1 passed', 'A': 'blocked_pre_body_timeout', 'B': 'not_run',
                'vitestCliStarts': 2, 'workerStarts': 2, 'mainRequests': 0, 'uiAssertionsExecuted': 0,
                'targetRetries': 0, 'preMainCorrectionWorkers': 0, 'ordinaryStaticCorrections': 1,
                'productStarts': 0, 'auxiliaryStarts': 0, 'chunkInjections': 0, 'gitWrites': 0,
                'diffCheckExitCode': diff.returncode, 'gitWarning': bool(diff.stderr.strip() or staged.stderr.strip()),
                'newFileWhitespaceCheckPassed': True,
                'resourceScope': 'four owned CLI/registered worker PIDs gone; worker exit codes and full descendant enumeration unverified'}
save('delivery-verification.json', verification)
files = new_sources + [ROOT / name for name in [REPORT, ROLE, MATRIX, OLD, MANUAL]]
files += [file for file in OWN.rglob('*') if file.is_file() and file.name != 'delivery.sha256']
files = sorted(set(files))
lines = [file.relative_to(ROOT).as_posix() + '\t' + sha(file.read_bytes()) for file in files]
(OWN / 'delivery.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8')
assert verify_manifest(OWN / 'delivery.sha256', ROOT) == len(files)
print(json.dumps({'audit': audit, 'verification': verification, 'deliveryFiles': len(files),
                  'deliverySha256': sha((OWN / 'delivery.sha256').read_bytes())}, ensure_ascii=False, indent=2))
