"""Read-only closeout of preserved evidence; does not execute acceptance targets."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path('D:/CodeX_gap/wife-system')
OWN = ROOT / 'tests/independent/desktop'
EV = OWN / 'evidence/r11-r1-windows'
PREVIOUS = OWN / 'evidence/r11-origin-settings'


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load('readonly_manifest_helpers', OWN / 'r11-origin-settings-audit.py')
old = load('readonly_profile_helpers', OWN / 'r10-settings-end-audit.py')
sha = base.sha


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def journal(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def source(manifest, count, digest=None):
    rows = manifest.read_text(encoding='utf-8').splitlines()
    seen = set()
    changed = []
    for row in rows:
        rel, expected = row.split('\t')
        assert rel not in seen, 'duplicate_source'
        seen.add(rel)
        path = (OWN / rel).resolve()
        assert path.is_relative_to(ROOT), 'source_boundary'
        if not path.is_file() or sha(path) != expected:
            changed.append(rel)
    return {'entries': len(rows), 'changes': changed, 'sha256': sha(manifest),
            'passed': len(rows) == count and not changed and
            (digest is None or sha(manifest) == digest)}


def zero_resources(result):
    return all(result.get(key) == 0 for key in
               ['remainingOwned', 'remainingListeners', 'remainingWindows'])


def main():
    allowed = ['docs/coordination/agents/tester.md',
               'docs/testing/phase-4-c12-windows-shell-report.md',
               'docs/testing/phase-4-c12-manual-checklist.md',
               'docs/testing/phase-4-modular-agent-host-test-matrix.md']
    now = lambda: datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    result = {'startedAt': now(), 'scope': 'P4-C12-R11-R1-WINDOWS',
              'meaning': 'Evidence integrity only; W4 business remains unverified'}
    result['repository'] = old.verify(
        ROOT, ROOT / 'docs/coordination/snapshots/p4-c12-r11-r1-windows-start.sha256',
        1550, '5fd65684cf41177c7d072f066887995f3820c08dc7f3a7e46434ef29d796e6d8', allowed)
    inputs = read(EV / 'input-audit.json')
    result['fixed'] = {key: base.verify(Path(value['base']), Path(value['manifest']),
                                      value['entries'], value['sha256'])
                       for key, value in inputs['fixed'].items()}
    previous_inputs = read(PREVIOUS / 'fixed-input-audit.json')
    result['actualEntries'] = [
        {'path': value['path'], 'sha256': sha(Path(value['path'])),
         'passed': sha(Path(value['path'])) == value['sha256']}
        for value in previous_inputs['actualToolEntries'] + previous_inputs['singles']]
    overrides = {rel: EV / ('baseline-' + Path(rel).name) for rel in allowed}
    result['R11'] = {}
    for key in ['delivery', 'tools', 'evidence', 'first-materials', 'source-archive']:
        value = inputs[key]
        result['R11'][key] = base.verify(
            Path(value['base']), Path(value['manifest']), value['entries'],
            value['sha256'], overrides if key == 'delivery' else None)
    result['R11']['formalSource'] = source(PREVIOUS / 'independent-source.sha256', 49)
    result['R11']['compatSource'] = source(PREVIOUS / 'compat-source.sha256',
                                           len((PREVIOUS / 'compat-source.sha256').read_text(encoding='utf-8').splitlines()))
    result['oldFirst'] = {
        folder: old.verify(ROOT, OWN / 'evidence' / folder / 'first-materials.sha256', count)
        for folder, count in [('r9-quit', 68), ('r9-r1', 38), ('r9-r2', 89), ('r9-r3', 148)]}
    original_profile = OWN / 'evidence/r9-r1/original-profile.tsv'
    result['oldProfiles'] = {
        label: old.profile(Path(path), original_profile, 63)
        for label, path in [('W1', 'C:/MarisC12/C12-R9-QUIT-20261016-011200'),
                            ('R1', 'C:/MarisC12/C12-R9-R1-20261017-001500'),
                            ('R2', 'C:/MarisC12/C12-R9-R2-20261017-233500')]}
    result['oldProfiles']['R3afterW2'] = old.profile(
        Path('C:/MarisC12/C12-R9-R3-20261018-105500'),
        OWN / 'evidence/r9-r3/new-profile-after-W2.tsv', 65)
    result['newProfile'] = old.profile(
        Path('C:/MarisC12/C12-R11-R1-WINDOWS-20261103-002800'),
        EV / 'new-profile-after-stop.tsv', 68)
    w2_freeze = read(EV / 'windows-w2-freeze.json')
    retention_freeze = read(EV / 'retention-freeze.json')
    result['source'] = {
        'W2': source(EV / 'windows-w2-source.sha256', 14, w2_freeze['sha256']),
        'helper': source(EV / 'helper-source.sha256', 14, retention_freeze['helperSha256']),
        'retention': source(EV / 'retention-source.sha256', 11, retention_freeze['retentionSha256'])}
    result['firstMaterials'] = base.verify(EV, EV / 'first-materials.sha256')
    result['sourceArchive'] = base.verify(EV, EV / 'source-archive.sha256', 30)
    before = old.matrix_rows((EV / 'baseline-phase-4-modular-agent-host-test-matrix.md').read_text(encoding='utf-8'))
    after = old.matrix_rows((ROOT / 'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_text(encoding='utf-8'))
    changed = [key for key, value in after.items() if value != before.get(key)]
    counts = {state: sum(value[-1] == state for key, value in after.items() if key.startswith('P4B-'))
              for state in ['passed', 'failed', 'blocked', 'not_run']}
    result['matrix'] = {
        'entries': len(after), 'columns': 12, 'uniqueSameIds': len(after) == 120 and set(after) == set(before),
        'changedRows': changed, 'expectationsAndRiskUnchanged': all(value[:-1] == before[key][:-1] for key, value in after.items()),
        'ACDUnchanged': all(value == before[key] for key, value in after.items() if not key.startswith('P4B-')),
        'B': counts}
    result['matrix']['passed'] = all([
        result['matrix']['uniqueSameIds'], result['matrix']['expectationsAndRiskUnchanged'],
        result['matrix']['ACDUnchanged'], changed == ['P4B-CMP-06'],
        counts == {'passed': 1, 'failed': 1, 'blocked': 20, 'not_run': 2}])
    result['appendOnly'] = {
        name: (ROOT / 'docs/testing' / name).read_bytes().startswith((EV / ('baseline-' + name)).read_bytes())
        for name in ['phase-4-c12-windows-shell-report.md', 'phase-4-c12-manual-checklist.md']}
    checks = read(EV / 'assertions.json')['checks']
    result['comparisons'] = {
        'reached': len(checks), 'passedCount': sum(check['passed'] for check in checks),
        'unique': len({check['id'] for check in checks}) == len(checks),
        'expectedActualPresent': all('expected' in check and 'actual' in check for check in checks),
        'W4BusinessReached': any(check['id'] == 'W4-RETENTION-CHOICE-INVOKED' for check in checks)}
    result['pairedJournals'] = {}
    for scene, count in [('W2', 18), ('W4', 2)]:
        rows = journal(EV / ('windows-' + scene) / 'journal.jsonl')
        enters = [row['details']['id'] for row in rows if row['event'] == 'assert_enter']
        terminals = [row['details'] for row in rows if row['event'] in ['assert_pass', 'assert_fail']]
        result['pairedJournals'][scene] = {
            'enters': len(enters), 'terminals': len(terminals),
            'passed': len(enters) == count and len(set(enters)) == count and
            len(terminals) == count and set(enters) == {row['id'] for row in terminals} and
            all(row['passed'] for row in terminals)}
    native_rows = journal(EV / 'helper-H2/native-stages.jsonl')
    native_enters = [row['id'] for row in native_rows if row['event'] == 'enter']
    native_ends = [row for row in native_rows if row['event'] == 'terminal']
    result['pairedJournals']['H2operations'] = {
        'enters': len(native_enters), 'terminals': len(native_ends),
        'passed': len(native_enters) == 45 and len(set(native_enters)) == 45 and
        len(native_ends) == 45 and set(native_enters) == {row['id'] for row in native_ends} and
        all(row['category'] == 'success' for row in native_ends)}
    w2 = read(EV / 'windows-W2/result.json')
    h2 = read(EV / 'helper-H2/process.json')
    native = read(EV / 'helper-H2/native-result.json')
    w4 = read(EV / 'windows-W4/result.json')
    stop = read(EV / 'stop-receipt.json')
    result['runs'] = {
        'W2W3': {'passed': w2['passed'] and w2['exit']['code'] == 0 and
                 w2['secondaryExit']['code'] == 0 and not w2['forced'] and
                 w2['closeReceipt']['closePosted'] and zero_resources(w2)},
        'H2': {'passed': h2['passed'] and native['passed'] and len(native['checks']) == 13 and
               h2['exit']['code'] == 0 and not h2['forced'] and h2['released'] and
               h2['profileUnchanged'] and zero_resources(h2)},
        'W4stopEvidence': {'businessAcceptance': 'unverified',
                           'classification': stop['classification'],
                           'passed': not w4['passed'] and w4['forced'] and w4['exit']['code'] == 1 and
                           w4['firstFailure']['stage'] == 'retention_dialog' and
                           stop['firstError']['safeDetail']['code'] == 'owned_dialog_button_ambiguous' and
                           stop['normalCleanupError']['safeDetail']['code'] == 'owned_main_ambiguous' and
                           w4['closeReceipt'] is None and zero_resources(w4)}}
    result['budget'] = {'newProducts': w2['productStarts'] + w4['productStarts'],
                        'newHelpers': h2['helperStarts'], 'seriesProducts': 5, 'seriesHelpers': 4,
                        'laterNotRun': stop['laterNotRun']}
    result['budget']['passed'] = (result['budget']['newProducts'] == 3 and
                                  result['budget']['newHelpers'] == 1 and
                                  stop['seriesProducts'] == 5 and stop['seriesHelpers'] == 4 and
                                  all(not (EV / path).exists() for path in
                                      ['helper-H3', 'windows-W5', 'helper-H4', 'windows-W6', 'windows-W7']))
    result['stagedCount'] = len(subprocess.run(
        ['git', 'diff', '--cached', '--name-only'], cwd=ROOT, capture_output=True,
        text=True, check=True).stdout.splitlines())
    diff = subprocess.run(['git', 'diff', '--check', '--', *allowed,
                           'docs/testing/phase-4-c12-r11-r1-windows-report.md'],
                          cwd=ROOT, capture_output=True, text=True)
    result['sharedDiffCheck'] = {'exitCode': diff.returncode,
                                 'stdoutLines': len(diff.stdout.splitlines()),
                                 'stderrLines': len(diff.stderr.splitlines())}
    groups = ['fixed', 'R11', 'oldFirst', 'oldProfiles', 'source', 'pairedJournals', 'runs']
    singles = ['repository', 'newProfile', 'firstMaterials', 'sourceArchive', 'matrix', 'budget']
    result['passed'] = all([
        *(value['passed'] for key in groups for value in result[key].values()),
        *(result[key]['passed'] for key in singles),
        *(value['passed'] for value in result['actualEntries']),
        *result['appendOnly'].values(), result['comparisons']['reached'] == 33,
        result['comparisons']['passedCount'] == 33, result['comparisons']['unique'],
        result['comparisons']['expectedActualPresent'], not result['comparisons']['W4BusinessReached'],
        result['stagedCount'] == 0, diff.returncode == 0])
    result['finishedAt'] = now()
    with (EV / 'end-audit.json').open('x', encoding='utf-8', newline='\n') as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
        file.write('\n')
    print(json.dumps({'passed': result['passed'], 'repository': result['repository'],
                      'matrix': result['matrix'], 'firstMaterials': result['firstMaterials'],
                      'budget': result['budget'], 'stagedCount': result['stagedCount']}, ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
