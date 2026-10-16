"""Read-only fixed-input verification; writes only the new R9 audit receipt."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / 'tests/independent/desktop/evidence/r9-quit'
START = json.loads((EVIDENCE / 'start-audit.json').read_text(encoding='utf8'))
BASELINE = json.loads((EVIDENCE / 'baseline.json').read_text(encoding='utf8'))
SHARED = {
    'docs/coordination/agents/tester.md',
    'docs/testing/phase-4-modular-agent-host-test-matrix.md',
    'docs/testing/phase-4-c12-windows-shell-report.md',
    'docs/testing/phase-4-c12-manual-checklist.md',
}
COORDINATOR = {
    'README.md', 'docs/project-coordination.md', 'docs/coordination/control.md',
    'docs/coordination/overview.md', 'docs/coordination/agents/brainstorm.md',
}


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def verify(name, source, allowed):
    manifest, base = Path(source['manifest']), Path(source['base'])
    assert digest(manifest) == source['sha256'], (name, 'manifest_changed')
    rows = [line.split('\t') for line in manifest.read_text(encoding='utf8').splitlines() if line]
    assert len(rows) == source['entries'], (name, 'entry_count')
    matches, changes, paths = 0, [], []
    for row in rows:
        rel, expected = row[0], row[-1]
        paths.append(rel)
        target = base / rel
        assert target.is_file() and not target.is_symlink(), (name, rel, 'missing_or_symlink')
        actual = digest(target)
        if actual == expected:
            matches += 1
        else:
            assert rel in allowed, (name, rel, 'unapproved_change')
            changes.append({'path': rel, 'sha256': actual})
    assert len(set(paths)) == len(paths), (name, 'duplicate_path')
    inventory_count = None
    if name in {'dependencies', 'out', 'resources', 'dist'}:
        inventory = {item.relative_to(base).as_posix() for item in base.rglob('*') if item.is_file()}
        # The frozen Python resources manifest intentionally excludes the asar,
        # which is independently bound by the full package and artifact hashes.
        if name == 'resources':
            inventory.discard('app.asar')
        assert inventory == set(paths), (name, 'path_inventory_diff',
                                         sorted(inventory - set(paths)), sorted(set(paths) - inventory))
        inventory_count = len(inventory)
    result = {'entries': len(rows), 'matched': matches, 'authorizedChanges': changes,
              'manifestSha256': source['sha256'], 'exactInventoryCount': inventory_count}
    print(json.dumps({'checked': name, 'entries': len(rows), 'matched': matches,
                      'changes': [v['path'] for v in changes]}), flush=True)
    return result


def main():
    report = {'at': datetime.datetime.now().astimezone().isoformat(), 'inputs': {}}
    for name, allowed in [
        ('start', SHARED), ('r7Source', SHARED | COORDINATOR),
        ('buildSource', set()), ('out', set()), ('resources', set()),
        ('dist', set()), ('dependencies', set()), ('executorEvidence', set()),
        ('r8r1Delivery', SHARED),
    ]:
        report['inputs'][name] = verify(name, START[name], allowed)
    workspace = Path(START['buildSource']['base'])
    for rel, expected in START['artifacts'].items():
        assert digest(workspace / rel) == expected, ('artifact', rel)
    report['artifacts'] = START['artifacts']
    own = ROOT / 'tests/independent/desktop'
    frozen = {}
    for manifest in sorted(EVIDENCE.glob('*-source.sha256')):
        rows = [row.split('\t') for row in manifest.read_text().splitlines()]
        for rel, expected in rows:
            assert digest(own / rel) == expected, ('new_first_source', rel)
        frozen[manifest.name] = {'entries': len(rows), 'sha256': digest(manifest)}
    first = EVIDENCE / 'first-materials.sha256'
    rows = [row.split('\t') for row in first.read_text().splitlines()]
    for rel, expected in rows:
        assert digest(ROOT / rel) == expected, ('first_material_changed', rel)
    report['newFrozenSources'] = frozen
    report['firstMaterials'] = {'entries': len(rows), 'sha256': digest(first)}
    for rel, original in BASELINE['append_files'].items():
        data = (ROOT / rel).read_bytes()
        assert hashlib.sha256(data[:original['bytes']]).hexdigest() == original['sha256'], ('append_prefix', rel)
    matrix = (ROOT / 'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_bytes()
    prefix = matrix[:matrix.index(b'### 5.2')]
    suffix = matrix[matrix.index(b'### 5.3'):]
    assert hashlib.sha256(prefix).hexdigest() == BASELINE['outside_b_prefix']
    assert hashlib.sha256(suffix).hexdigest() == BASELINE['outside_b_suffix']
    cases = [[cell.strip() for cell in line.strip().strip('|').split('|')]
             for line in matrix.decode('utf8').splitlines() if re.match(r'^\| P4[ABCD]-[A-Z]+-\d{2} \|', line)]
    assert len(cases) == len({row[0] for row in cases}) == 120
    before = {row[0]: row for row in BASELINE['cases']}
    for row in cases:
        assert len(row) == 12 and row[:-1] == before[row[0]][:-1], ('matrix_contract', row[0])
        if row[1] != 'B':
            assert row == before[row[0]], ('matrix_non_b', row[0])
    report['matrix'] = {'total': len(cases), 'columns': 12, 'originalExpectationsPreserved': True,
                        'nonBBytesPreserved': True, 'B': dict(collections.Counter(row[-1] for row in cases if row[1] == 'B'))}
    report['appendOnlyPrefixesPreserved'] = True
    staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, capture_output=True, check=True)
    assert not staged.stdout.strip(), 'staged_not_empty'
    diff = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True)
    assert diff.returncode == 0, 'diff_check_failed'
    report['gitReadOnly'] = {'stagedCount': 0, 'diffCheckExit': 0,
                             'warningBytes': len(staged.stderr) + len(diff.stderr), 'writeOperations': 0}
    report['passed'] = True
    target = EVIDENCE / 'end-audit.json'
    assert not target.exists(), 'audit_receipt_exists'
    target.write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps({'auditPassed': True, 'B': report['matrix']['B']}), flush=True)


if __name__ == '__main__':
    main()
