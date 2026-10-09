"""Read-only acceptance-evidence audit; writes only new R6 delivery records."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import mmap
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
DESKTOP = ROOT / 'tests/independent/desktop'
OWN = DESKTOP / 'evidence/r6-env'
EXT = Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
ROLE = 'docs/coordination/agents/tester.md'
MATRIX = 'docs/testing/phase-4-modular-agent-host-test-matrix.md'
REPORT = 'docs/testing/phase-4-c12-r6-env-windows-report.md'
SHARED = {ROLE, MATRIX, 'docs/testing/phase-4-c12-windows-shell-report.md',
          'docs/testing/phase-4-c12-manual-checklist.md'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name):
    return json.loads((OWN / name).read_text(encoding='utf-8-sig'))


def save(name, value):
    (OWN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def audit_manifest(file, base, allowed=()):
    rows = [line.split('\t') for line in file.read_text(encoding='utf-8-sig').splitlines()]
    assert len(rows) == len({row[0] for row in rows})
    unchanged, changed = [], []
    for row in rows:
        name, digest = row[0], row[-1]
        path = base / name
        assert path.is_file(), name
        if sha(path.read_bytes()) == digest:
            unchanged.append(name)
        else:
            assert name in allowed, name
            changed.append(name)
    return {'entries': len(rows), 'matched': len(unchanged), 'authorizedChanges': sorted(changed),
            'manifestSha256': sha(file.read_bytes())}


def journal(phase, name):
    raw = (OWN / phase / name).read_bytes()
    assert raw.endswith(b'\n')
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
    assert [row['seq'] for row in rows] == list(range(1, len(rows) + 1))
    return rows


start = load('start-audit.json')
baseline = load('baseline.json')
manifest = ROOT / 'docs/coordination/snapshots/p4-c12-r6-env-start.sha256'
assert sha(manifest.read_bytes()) == start['start']['sha256']
audit = {'start': audit_manifest(manifest, ROOT, SHARED)}
assert audit['start']['entries'] == 679 and audit['start']['matched'] == 675
assert set(audit['start']['authorizedChanges']) == SHARED
for key, filename, base, count in [
    ('source', 'workspace-source.sha256', EXT, 389),
    ('out', 'out-manifest-v4.tsv', EXT / 'apps/desktop/out/Maris-win32-x64', 140),
    ('resources', 'python-resources-v4.tsv', EXT / 'apps/desktop/out/Maris-win32-x64/resources', 67),
]:
    file = EXT.parent / 'evidence/static' / filename
    assert sha(file.read_bytes()) == start[key]['sha256']
    audit[key] = audit_manifest(file, base)
    assert audit[key]['matched'] == count
audit['artifacts'] = {name: sha((EXT / name).read_bytes()) for name in start['artifacts']}
assert audit['artifacts'] == start['artifacts']
with (EXT / 'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as stream:
    with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        sentinel = data.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')
        assert sentinel >= 0
        at = sentinel + 32
        audit['fuses'] = {'version': data[at], 'wire': list(data[at + 2:at + 2 + data[at + 1]])}
assert audit['fuses'] == {'version': 1, 'wire': [48, 49, 48, 48, 49, 49, 48, 49, 49]}
preflight = load('static-preflight.json')
for item in preflight['versions'].values():
    assert sha((Path(item['physicalRoot']) / 'package.json').read_bytes()) == item['packageJsonSha256']
native = preflight['nativeJsdom']
assert sha(Path(native['apiRealPath']).read_bytes()) == native['apiSha256']
assert sha(Path(native['packageRealPath']).read_bytes()) == native['packageSha256']
audit['dependencyMetadataMatched'] = len(preflight['versions'])
for label, file, base, count in [
    ('oldR5Delivery', DESKTOP / 'evidence/r5-public/delivery.sha256', ROOT, 37),
    ('oldR5Source', DESKTOP / 'evidence/r5-public/cold-source.sha256', DESKTOP, 10),
    ('oldR5First', DESKTOP / 'evidence/r5-public/cold-first.sha256', ROOT, 6),
    ('coldSource', OWN / 'cold-source.sha256', DESKTOP, 9),
    ('recoverySource', OWN / 'recovery-source.sha256', DESKTOP, 5),
    ('coldFirst', OWN / 'cold-first.sha256', ROOT, 9),
    ('recoveryFirst', OWN / 'recovery-first.sha256', ROOT, 7),
]:
    audit[label] = audit_manifest(file, base, SHARED if label == 'oldR5Delivery' else ())
    assert audit[label]['matched'] == count, (label, audit[label])
assert set(audit['oldR5Delivery']['authorizedChanges']) == SHARED

matrix = (ROOT / MATRIX).read_bytes()
cases = [[cell.strip() for cell in line.strip().strip('|').split('|')]
         for line in matrix.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-', line)]
assert len(cases) == len({row[0] for row in cases}) == 120 and all(len(row) == 12 for row in cases)
assert cases == baseline['cases']
a, z = matrix.index(b'### 5.2'), matrix.index(b'### 5.3')
assert sha(matrix[:a]) == baseline['outside_b_prefix'] and sha(matrix[z:]) == baseline['outside_b_suffix']
prefixes = {}
append_text = {}
for name, previous in baseline['append_files'].items():
    data = (ROOT / name).read_bytes()
    assert sha(data[:previous['bytes']]) == previous['sha256']
    prefixes[name] = {'originalBytes': previous['bytes'], 'appendedBytes': len(data) - previous['bytes'], 'prefixPreserved': True}
    append_text[name] = data[previous['bytes']:].decode('utf-8')
report = (ROOT / REPORT).read_text(encoding='utf-8')
ids = re.findall(r'^\| (P4B-[A-Z]+-\d+) \|', report, re.M)
assert len(ids) == len(set(ids)) == 24 and set(ids) == {row[0] for row in cases if row[1] == 'B'}
audit['matrix'] = {'uniqueIds': 120, 'columns': 12, 'originalRowsAndStatesPreserved': True, 'outsideBPreserved': True,
                   'states': {phase: dict(Counter(row[11] for row in cases if row[1] == phase)) for phase in 'ABCD'}}
audit['appendFiles'] = prefixes
audit['incrementalCaseRows'] = 24

execution = {}
for phase, passed, failed, main in [('cold', 1, 0, 1), ('recovery', 0, 1, 0)]:
    events = journal(phase, 'worker.journal.jsonl')
    controls = journal(phase, 'controller.journal.jsonl')
    configs = journal(phase, 'config.journal.jsonl')
    process = load(f'{phase}/process.json')
    runner = load(f'{phase}/result.json')
    assert all(row['pid'] == process['workerPid'] and row['parentPid'] == process['rootPid'] for row in events)
    assert all(row['pid'] == process['rootPid'] for row in configs)
    assert process['rootExited'] and process['workerExited'] and process['workerParentVerified'] and process['streamsComplete']
    assert not any(process[key] for key in ['timedOut', 'forcedRootTermination', 'forcedWorkerTermination',
                   'workerObservationUnverified', 'cleanupObservationUnverified', 'evidenceReadUnverified', 'journalTruncated'])
    assert runner['numPassedTests'] == passed and runner['numFailedTests'] == failed and runner['numTotalTests'] == 1
    assert runner['moduleErrorCount'] == runner['unhandledErrorCount'] == 0
    assert process['mainImportRequests'] == main and process['correctionBudgetUsed'] == 0
    assert process['initializationDurationMs'] <= 60000 and controls[-1]['elapsedMs'] <= 75000
    assert next(row for row in events if row['stage'] == 'native_jsdom_identity')['identityMatched']
    assert next(row for row in events if row['stage'] == 'native_jsdom_resolved')['referencesValid']
    if phase == 'cold':
        assertions = [row for row in events if row['stage'] == 'public_assertion']
        assert len(assertions) == 4 and all(row['passed'] and row['sampleOrdinal'] == 1 for row in assertions)
        assert next(row for row in events if row['stage'] == 'fault_source')['faultSourceValid']
        assert next(row for row in events if row['stage'] == 'public_target_result')['publicTargetResult']
        safety = next(row for row in events if row['stage'] == 'safety_assertions')
        assert safety['boundariesSafe'] and safety['domSafe'] and safety['consoleSafe']
    else:
        assert [row['ordinal'] for row in events if row['stage'] == 'recovery_scenario_enter'] == [1]
        assert [row['ordinal'] for row in events if row['stage'] == 'recovery_scenario_failed'] == [1]
        assert not any(row['stage'] == 'recovery_scenario_passed' for row in events)
        assert runner['nodes'][0]['errors'] == [{'kind': 'AssertionError', 'timeout': False}]
    cleanup = next(row for row in events if row['stage'] == 'cleanup_finished')
    assert cleanup['rescueUnsubscribe'] == 0 and cleanup['cleanupMs'] <= 2000
    execution[phase] = {'passed': passed, 'failed': failed, 'mainImports': main,
                        'initializationMs': process['initializationDurationMs'], 'controllerTotalMs': controls[-1]['elapsedMs'],
                        'rootExitCode': process['rootExitCode'], 'workerExitCode': 'unverified'}
audit['execution'] = execution
resources = load('resource-postcheck.json')
assert all(item['observation'] == 'explicitly_absent' for item in resources['observations'])
assert load('cache-cleanup.json')['filesRemoved'] == 2 and not (OWN / 'cache').exists()
role = (ROOT / ROLE).read_text(encoding='utf-8')
assert '- 状态：`blocked`' in role and '- 运行状态：`finished`' in role

staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, capture_output=True, text=True, check=True)
assert not staged.stdout.splitlines()
diff = subprocess.run(['git', 'diff', '--check', '--', *sorted(SHARED), REPORT,
                       'tests/independent/desktop/r6-env-*', 'tests/independent/desktop/evidence/r6-env'],
                      cwd=ROOT, capture_output=True, text=True)
save('format-check.json', {'gitDiffCheckExit': diff.returncode, 'gitWarningPresent': bool(diff.stderr.strip()), 'stagedPaths': []})
assert diff.returncode == 0
audit['stagedPaths'] = []
save('end-audit.json', audit)

# Neither the digest list nor its verification record hashes itself.
sources = [file for file in DESKTOP.glob('r6-env-*') if file.is_file()]
files = sorted(set(sources + [ROOT / name for name in [REPORT, *sorted(SHARED)]] +
                   [file for file in OWN.rglob('*') if file.is_file() and file.name not in ['delivery.sha256', 'delivery-verification.json']]))
for file in sources + [ROOT / REPORT]:
    assert all(line == line.rstrip(' \t') for line in file.read_text(encoding='utf-8').splitlines()), file.name
for segment in append_text.values():
    assert all(line == line.rstrip(' \t') for line in segment.splitlines())
delivery = OWN / 'delivery.sha256'
delivery.write_text(''.join(file.relative_to(ROOT).as_posix() + '\t' + sha(file.read_bytes()) + '\n' for file in files), encoding='utf-8', newline='\n')
verified = audit_manifest(delivery, ROOT)
save('delivery-verification.json', {'files': verified['matched'], 'sha256': sha(delivery.read_bytes()),
     'encoding': 'UTF-8 without BOM; sorted repo relative paths; TAB; LF',
     'excludedSelfReferences': ['delivery.sha256', 'delivery-verification.json'],
     'inputAudit': 'end-audit.json', 'targetReruns': 0, 'gitWrites': 0,
     'status': 'blocked / finished', 'requiresCoordinatorReview': True})
print(json.dumps({'input': audit['start'], 'matrix': audit['matrix'], 'execution': execution,
                  'delivery': load('delivery-verification.json')}, ensure_ascii=False, indent=2))
