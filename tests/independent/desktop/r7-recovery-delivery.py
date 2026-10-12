"""Read-only input/evidence audit; only new R7 delivery records are written."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import mmap
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
DESKTOP = ROOT / 'tests/independent/desktop'
OWN = DESKTOP / 'evidence/r7-recovery'
EXT = Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
ROLE = 'docs/coordination/agents/tester.md'
MATRIX = 'docs/testing/phase-4-modular-agent-host-test-matrix.md'
REPORT = 'docs/testing/phase-4-c12-r7-recovery-windows-report.md'
SHARED = {ROLE, MATRIX, 'docs/testing/phase-4-c12-windows-shell-report.md',
          'docs/testing/phase-4-c12-manual-checklist.md'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name):
    return json.loads((OWN / name).read_text(encoding='utf-8-sig'))


def save(name, value):
    (OWN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8', newline='\n')


def audit_manifest(file, base, allowed=()):
    rows = [line.split('\t') for line in file.read_text(encoding='utf-8-sig').splitlines() if line]
    assert len(rows) == len({r[0] for r in rows})
    changed = []
    for row in rows:
        target = base / row[0]
        assert target.is_file(), row[0]
        if sha(target.read_bytes()) != row[-1]:
            assert row[0] in allowed, row[0]
            changed.append(row[0])
    return {'entries': len(rows), 'matched': len(rows) - len(changed),
            'authorizedChanges': sorted(changed), 'sha256': sha(file.read_bytes())}


start = load('start-audit.json')
baseline = load('baseline.json')
manifest = ROOT / 'docs/coordination/snapshots/p4-c12-r7-recovery-start.sha256'
assert sha(manifest.read_bytes()) == start['start']['sha256']
audit = {'start': audit_manifest(manifest, ROOT, SHARED)}
assert audit['start']['entries'] == 743 and audit['start']['matched'] == 739
assert set(audit['start']['authorizedChanges']) == SHARED

for label, filename, base, count in [
    ('source', 'workspace-source.sha256', EXT, 389),
    ('out', 'out-manifest-v4.tsv', EXT / 'apps/desktop/out/Maris-win32-x64', 140),
    ('resources', 'python-resources-v4.tsv', EXT / 'apps/desktop/out/Maris-win32-x64/resources', 67),
]:
    file = EXT.parent / 'evidence/static' / filename
    assert sha(file.read_bytes()) == start[label]['sha256']
    audit[label] = audit_manifest(file, base)
    assert audit[label]['matched'] == count
audit['artifacts'] = {name: sha((EXT / name).read_bytes()) for name in start['artifacts']}
assert audit['artifacts'] == start['artifacts']
with (EXT / 'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as stream:
    with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        at = data.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')
        assert at >= 0
        at += 32
        audit['fuses'] = {'version': data[at], 'wire': list(data[at+2:at+2+data[at+1]])}
assert audit['fuses'] == {'version': 1, 'wire': [48, 49, 48, 48, 49, 49, 48, 49, 49]}
for item in start['versions'].values():
    assert sha((Path(item['physicalRoot']) / 'package.json').read_bytes()) == item['packageJsonSha256']
assert sha(Path(start['nativeJsdom']['apiRealPath']).read_bytes()) == start['nativeJsdom']['apiSha256']
audit['dependencyMetadataMatched'] = 7

r6 = DESKTOP / 'evidence/r6-env'
for label, file, base, count in [
    ('r6Delivery', r6/'delivery.sha256', ROOT, 59),
    ('r6ColdSource', r6/'cold-source.sha256', DESKTOP, 9),
    ('r6RecoverySource', r6/'recovery-source.sha256', DESKTOP, 5),
    ('r6ColdFirst', r6/'cold-first.sha256', ROOT, 9),
    ('r6RecoveryFirst', r6/'recovery-first.sha256', ROOT, 7),
    ('recoverySource', OWN/'recovery-source.sha256', DESKTOP, 7),
    ('recoveryFirst', OWN/'recovery-first.sha256', ROOT, None),
    ('compatSource', OWN/'compat-source.sha256', DESKTOP, 4),
    ('compatFirst', OWN/'compat-first.sha256', ROOT, None),
    ('publicSource', OWN/'public-source.sha256', DESKTOP, 5),
    ('publicFirst', OWN/'public-first.sha256', ROOT, None),
    ('windowsSource', OWN/'windows-source.sha256', DESKTOP, 3),
    ('windowsFirst', OWN/'windows-first.sha256', ROOT, 2),
]:
    audit[label] = audit_manifest(file, base, SHARED if label == 'r6Delivery' else ())
    if count is not None:
        assert audit[label]['matched'] == count, label
    if label in start:
        assert audit[label]['sha256'] == start[label]['sha256'], label
assert set(audit['r6Delivery']['authorizedChanges']) == SHARED

matrix = (ROOT / MATRIX).read_bytes()
cases = [[cell.strip() for cell in line.strip().strip('|').split('|')]
         for line in matrix.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-', line)]
assert len(cases) == len({row[0] for row in cases}) == 120
assert all(len(row) == 12 for row in cases) and cases == baseline['cases']
a, z = matrix.index(b'### 5.2'), matrix.index(b'### 5.3')
assert sha(matrix[:a]) == baseline['outside_b_prefix']
assert sha(matrix[z:]) == baseline['outside_b_suffix']
audit['matrix'] = {'uniqueIds': 120, 'columns': 12, 'originalRowsAndStatesPreserved': True,
                   'outsideBPreserved': True,
                   'states': {phase: dict(Counter(row[11] for row in cases if row[1] == phase)) for phase in 'ABCD'}}
audit['appendFiles'] = {}
for name, previous in baseline['append_files'].items():
    data = (ROOT / name).read_bytes()
    assert sha(data[:previous['bytes']]) == previous['sha256']
    audit['appendFiles'][name] = {'originalBytes': previous['bytes'],
                                 'appendedBytes': len(data) - previous['bytes'], 'prefixPreserved': True}
report = (ROOT / REPORT).read_text(encoding='utf-8')
case_ids = re.findall(r'^\| (P4B-[A-Z]+-\d+) \|', report, re.M)
assert len(case_ids) == len(set(case_ids)) == 24
assert set(case_ids) == {row[0] for row in cases if row[1] == 'B'}
audit['incrementalCaseRows'] = 24

recovery = load('recovery/result.json')
process = load('recovery/process.json')
events = [json.loads(line) for line in (OWN/'recovery/worker.journal.jsonl').read_text(encoding='utf-8').splitlines()]
assert [e['seq'] for e in events] == list(range(1, len(events)+1))
assert recovery['numTotalTests'] == recovery['numPassedTests'] == 1 and recovery['numFailedTests'] == 0
assert recovery['groupsEntered'] == recovery['groupsPassed'] == [1, 2, 3, 4, 5]
assert recovery['firstFormalFailure'] is None and not recovery['cleanupFailures'] and not recovery['operationFailures']
assert recovery['assertionRecords'] == {'entered': 212, 'terminal': 212, 'complete': True}
gate = [e for e in events if e['stage'] in ['assert_pass', 'assert_fail'] and e.get('kind') == 'gate']
assert len(gate) == 208 and all(e['stage'] == 'assert_pass' for e in gate)
legacy = recovery['legacyComparisons']
assert [(e['id'],e['expected'],e['actual']) for e in legacy] == [('legacy_initial_exact_1',1,2),('legacy_first_retry_total_2',2,3)]
assert process['rootExited'] and process['workerExited'] and process['rootExitCode'] == 0
assert not process['timedOut'] and not process['forcedRootTermination'] and not process['forcedWorkerTermination']
assert process['initializationDurationMs'] <= 60000 and process['controllerBodyDurationMs'] <= 10000 and process['durationMs'] <= 75000
assert process['mainImportRequests'] == 0
audit['recovery'] = {'passedNodes': 1, 'groupsPassed': 5, 'formalComparisonsPassed': 208,
                     'legacy': [{k:e[k] for k in ['id','expected','actual']} for e in legacy],
                     'assertionPairs': 212, 'rootExitCode': process['rootExitCode'],
                     'workerNativeExitCode': process['workerNativeExitCode'], 'workerExitCause': 'unverified'}
for label, count in [('compat',10),('public',8)]:
    result, proc = load(label+'/result.json'), load(label+'/process.json')
    assert result['total'] == result['passed'] == count
    assert result['failed'] == result['moduleErrors'] == result['unhandled'] == 0
    assert proc['rootExited'] and proc['rootExitCode'] == 0 and not proc['forced'] and not proc['timedOut']
    assert all(w['exited'] and w['identityVerified'] and not w['forced'] for w in proc['workers'])
    audit[label] = {'total':count,'passed':count,'files':len({n['file'] for n in result['nodes']}),
                    'rootExitCode':proc['rootExitCode'],'workers':proc['workers']}

win = load('windows-W1/result.json')
win_events = [json.loads(line) for line in (OWN/'windows-W1/journal.jsonl').read_text(encoding='utf-8').splitlines()]
assert [e['seq'] for e in win_events] == list(range(1,len(win_events)+1))
assert win['firstFailure']['id'] == 'W1-DAILY-PAGE' and not win['passed']
assert win['cleanupError'] is None and win['remainingOwned'] == win['remainingListeners'] == 0
assert win['forced'] and not win['normalClose'] and not win['timeout'] and win['durationMs'] <= 120000
assert len([e for e in win_events if e['stage']=='assert_pass']) == 13
failed = [e for e in win_events if e['stage']=='assert_fail']
assert len(failed) == 1 and failed[0]['expected'] is True and failed[0]['actual'] == 'unknown'
assert all(e['observation'] in ['explicitly_absent','pid_reused_original_absent'] for e in load('resource-postcheck.json')['observations'])
audit['windows'] = {'productStarts':1,'helperStarts':0,'chunkInjectionCount':0,'passedScenario':False,
                    'passedComparisons':13,'failedObservations':1,'firstFailure':win['firstFailure'],
                    'actual':'unknown','forcedCleanup':True,'rootExitCode':win['rootExit']['code'],
                    'remainingOwned':0,'remainingListeners':0,'durationMs':win['durationMs']}
audit['limitations'] = {'namedFilePatternDeviation':['r7-recovery.config.mjs','r7-recovery.test.tsx'],
                        'oldR6FailurePreserved':True,'w1TerminalDomSample':'missing',
                        'w1JournalFailureStageLabel':'overwritten_by_detail_runtime_result_preserves_firstFailure',
                        'publicStaticParser':'Node_check_TS_rejected_outer_shell_continued_first_Vitest_8_passed',
                        'publicProcessScopeLabel':'three_public_files_once_is_incorrect_one_actual_file',
                        'targetReruns':0,'historicalDescendantExitCodes':'unknown',
                        'virtualProfile':'retained_outside_repo'}
role = (ROOT/ROLE).read_text(encoding='utf-8')
assert '- 状态：`blocked`' in role and '- 运行状态：`finished`' in role
staged = subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True)
assert not staged.stdout.strip()
diff = subprocess.run(['git','diff','--check','--',*sorted(SHARED),REPORT,
                       'tests/independent/desktop/r7-recovery*','tests/independent/desktop/evidence/r7-recovery'],
                      cwd=ROOT,capture_output=True,text=True)
save('format-check.json',{'exitCode':diff.returncode,'warningsPresent':bool(diff.stderr.strip()),'stagedPaths':[]})
assert diff.returncode == 0
audit['stagedPaths'] = []
save('end-audit.json',audit)

sources = [f for f in DESKTOP.glob('r7-recovery*') if f.is_file()]
files = set(sources + [ROOT / n for n in [REPORT,*sorted(SHARED)]] +
            [f for f in OWN.rglob('*') if f.is_file() and f.name not in ['delivery.sha256','delivery-verification.json']])
names = sorted(f.relative_to(ROOT).as_posix() for f in files)
assert len(names) == len(set(names))
delivery = OWN/'delivery.sha256'
delivery.write_text(''.join(f'{n}\t{sha((ROOT/n).read_bytes())}\n' for n in names),encoding='utf-8',newline='\n')
verified = audit_manifest(delivery,ROOT)
save('delivery-verification.json',{'files':verified['matched'],'sha256':sha(delivery.read_bytes()),
      'encoding':'UTF-8 no BOM; full POSIX relative path string sort; TAB; LF',
      'excludedSelfReferences':['delivery.sha256','delivery-verification.json'],
      'inputAudit':'end-audit.json','targetReruns':0,'gitWrites':0,
      'status':'blocked / finished','requiresCoordinatorReview':True})
print(json.dumps({'start':audit['start'],'matrix':audit['matrix'],'windows':audit['windows'],
                  'delivery':load('delivery-verification.json')},ensure_ascii=False,indent=2))
