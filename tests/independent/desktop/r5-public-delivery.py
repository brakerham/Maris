"""Audit the stopped R5-PUBLIC delivery; never import or execute a test target."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import mmap
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'tests/independent/desktop/evidence/r5-public'
EXT = Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
ROLE = 'docs/coordination/agents/tester.md'
MATRIX = 'docs/testing/phase-4-modular-agent-host-test-matrix.md'
OLD = 'docs/testing/phase-4-c12-windows-shell-report.md'
MANUAL = 'docs/testing/phase-4-c12-manual-checklist.md'
REPORT = 'docs/testing/phase-4-c12-r5-public-windows-report.md'
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
manifest = ROOT / 'docs/coordination/snapshots/p4-c12-r5-public-start.sha256'
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
assert len(matched) == 634 and set(changed) == ALLOWED and not bad and not missing

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
assert verify_manifest(OWN / 'cold-source.sha256', ROOT / 'tests/independent/desktop') == 10
assert verify_manifest(OWN / 'cold-first.sha256', ROOT) == 6

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

events = journal('cold/worker.journal.jsonl')
controls = journal('cold/controller.journal.jsonl')
configs = journal('cold/config.journal.jsonl')
process = load('cold/process.json')
assert [event['stage'] for event in events] == ['worker_start', 'journal_ready', 'test_module_enter', 'jsdom_import_enter']
assert all(event['pid'] == process['workerPid'] and event['parentPid'] == process['rootPid'] for event in events)
assert len(configs) == 4 and all(event['pid'] == process['rootPid'] for event in configs)
assert process['timedOut'] and process['limitStage'] == 'initialization' and process['mainImportRequests'] == process['fixtureEvaluations'] == 0
assert process['rootExited'] and process['workerExited'] and process['workerParentVerified'] and process['streamsComplete']
assert not process['workerObservationUnverified'] and not process['cleanupObservationUnverified'] and not process['evidenceReadUnverified'] and not process['journalTruncated']
assert process['totalCliInvocationsThisPhase'] == 1 and process['correctionBudgetUsed'] == 0
assert not (OWN / 'cold/result.json').exists() and not (OWN / 'cold/resolver.journal.jsonl').exists()
assert process['controllerBodyAtMs'] is None and process['controllerCleanupAtMs'] is None
root_at = next(event['elapsedMs'] for event in controls if event['stage'] == 'root_started')
stop_at = next(event['elapsedMs'] for event in controls if event['stage'] == 'deadline_termination_enter')
exit_at = next(event['elapsedMs'] for event in controls if event['stage'] == 'exit_checked')
assert stop_at-root_at <= 15000 and exit_at-stop_at <= 2000 and controls[-1]['elapsedMs'] <= 30000
assert load('no-retry-ruling.json')['identifiedPureToolConfigurationError'] is False
summary = load('public-summary.json')
assert summary['faultSourceValid'] == summary['publicTargetResult'] == 'not_evaluated'
assert set(summary['fourAssertions'].values()) == {'not_run'}
cleanup = load('temp-cleanup.json')
assert cleanup['pathBoundaryVerified'] and cleanup['noReparseVerified'] and cleanup['absentAfter'] and not (OWN / 'cache').exists()
assert not cleanup['existed'] and cleanup['deletedFiles'] == 0
resources = load('resource-observation.json')
assert len(resources['createdProcesses']) == 2 and all(item['gone'] is True and item['safeFailure'] is None for item in resources['createdProcesses'])
assert resources['workerExitCode'] is None and resources['fullHistoricalDescendantsVerified'] is False

old_r2_preserved, old_r2_changed = [], []
for name, digest in entries(ROOT / 'tests/independent/desktop/evidence/r4-r3/delivery.sha256'):
    if sha((ROOT / name).read_bytes()) == digest:
        old_r2_preserved.append(name)
    else:
        old_r2_changed.append(name)
assert len(old_r2_preserved) == 48 and set(old_r2_changed) == ALLOWED
assert verify_manifest(ROOT / 'docs/coordination/diagnostics/p4-d16/delivery.sha256', ROOT) == 39
assert verify_manifest(ROOT / 'tests/independent/desktop/evidence/r4-r3/cold-source.sha256', ROOT / 'tests/independent/desktop') == 15
role = (ROOT / ROLE).read_text(encoding='utf-8')
assert '- 状态：`blocked`' in role and '- 运行状态：`finished`' in role

staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, capture_output=True, text=True, check=True)
assert not staged.stdout.splitlines()
diff = subprocess.run(['git', 'diff', '--check', '--', ROLE, MATRIX, OLD, MANUAL, REPORT,
                       'tests/independent/desktop/r5-public-*', 'tests/independent/desktop/evidence/r5-public'],
                      cwd=ROOT, capture_output=True, text=True)
(OWN / 'diff-check.log').write_text(diff.stdout + diff.stderr, encoding='utf-8')
assert diff.returncode == 0

new_sources = [file for file in (ROOT / 'tests/independent/desktop').glob('r5-public-*') if file.is_file()]
new_evidence = [file for file in OWN.rglob('*') if file.is_file() and file.name != 'delivery.sha256']
full_scan = new_sources + [ROOT / REPORT] + new_evidence
segments = {file.relative_to(ROOT).as_posix(): file.read_text(encoding='utf-8-sig') for file in full_scan}
segments.update(append_segments)
segments[MATRIX + ':B-only'] = matrix_bytes[a:z].decode('utf-8')
segments[ROLE + ':R5-only'] = role[:role.index('### 2026-10-03 15:36')]
whitespace_issues = [{'path': name, 'lineInScannedSegment': index}
                     for name, text in segments.items() for index, line in enumerate(text.splitlines(), 1)
                     if line.rstrip(' \t') != line]
save('whitespace-check.json', {'fullNewFiles': len(full_scan), 'scannedSegments': len(segments),
                             'issues': whitespace_issues, 'scope': 'new R5-PUBLIC files in full; append segments, B only and R5 role prefix; old files read-only'})
assert not whitespace_issues, whitespace_issues

audit = {'entries': 638, 'unchanged': len(matched), 'authorizedChanged': sorted(changed),
         'unauthorizedMismatch': bad, 'missing': missing, 'stagedPaths': [], 'manifestSha256': sha(manifest.read_bytes()),
         'artifacts': artifacts, 'fuses': fuses, 'packageInputsMatched': counts,
         'oldIndependentFilesUnchanged': sum(name.startswith('tests/independent/desktop/') for name in matched),
         'oldD15DiagnosticFilesUnchanged': sum(name.startswith('docs/coordination/diagnostics/p4-d15') for name in matched),
         'priorPDeliveryUnchanged': len(old_r2_preserved), 'priorPAuthorizedSharedChanges': sorted(old_r2_changed),
         'frozenColdSourceFilesMatched': 10, 'fixedDependencyMetadataMatched': len(metadata)}
save('end-audit.json', audit)
verification = {'matrixUniqueIds': 120, 'columns': 12, 'firstElevenColumnsPreserved': True,
                'allStatusesPreserved': True, 'matrixStates': states, 'outsideBBytesPreserved': True,
                'appendFiles': prefixes, 'reportFullCaseMappings': 24, 'B': 'initialization_blocked',
                'faultSourceValid': 'not_evaluated', 'publicTargetResult': 'not_evaluated',
                'vitestCliStarts': 1, 'workerStarts': 1, 'mainRequests': 0, 'uiAssertionsExecuted': 0,
                'targetRetries': 0, 'preMainCorrectionWorkers': 0, 'ordinaryStaticCorrections': 1,
                'initializationMsBeforeTermination': stop_at-root_at, 'ownedShutdownMs': exit_at-stop_at,
                'controllerTotalMsIncludingReport': controls[-1]['elapsedMs'],
                'priorPFrozenSourceMatched': 15, 'oldD16DeliveryMatched': 39,
                'productStarts': 0, 'auxiliaryStarts': 0, 'chunkInjections': 0, 'gitWrites': 0,
                'diffCheckExitCode': diff.returncode, 'gitWarning': bool(diff.stderr.strip() or staged.stderr.strip()),
                'newFileWhitespaceCheckPassed': True,
                'resourceScope': 'created CLI and registered worker gone; worker exit code and full historical descendants unverified'}
save('delivery-verification.json', verification)
files = new_sources + [ROOT / name for name in [REPORT, ROLE, MATRIX, OLD, MANUAL]]
files += [file for file in OWN.rglob('*') if file.is_file() and file.name != 'delivery.sha256']
files = sorted(set(files))
lines = [file.relative_to(ROOT).as_posix() + '\t' + sha(file.read_bytes()) for file in files]
(OWN / 'delivery.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8')
assert verify_manifest(OWN / 'delivery.sha256', ROOT) == len(files)
print(json.dumps({'audit': audit, 'verification': verification, 'deliveryFiles': len(files),
                  'deliverySha256': sha((OWN / 'delivery.sha256').read_bytes())}, ensure_ascii=False, indent=2))
