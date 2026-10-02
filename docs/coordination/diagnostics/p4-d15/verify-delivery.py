"""Read-only input/document verification; writes only D15 verification records."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

OWN = Path(__file__).resolve().parent
REPO = OWN.parents[3]
EXTERNAL = Path('C:/MarisLazyR5/R5-20261002-222300')
DOCUMENT = REPO / 'docs/phase-4-d15-lazy-propagation-advice.md'
ROLE = REPO / 'docs/coordination/agents/technical-adviser.md'


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def save(name: str, value: object) -> None:
    (OWN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check_manifest(manifest: Path, root: Path, authorized: set[str] | None = None) -> dict:
    authorized = authorized or set()
    result = {'total': 0, 'matched': 0, 'authorizedChanged': [], 'unauthorizedChanged': [], 'missing': [], 'invalid': []}
    expected_paths = []
    for number, line in enumerate(manifest.read_text(encoding='utf-8-sig').splitlines(), 1):
        result['total'] += 1
        parts = line.split('\t')
        if len(parts) not in (2, 3) or not re.fullmatch('[0-9a-f]{64}', parts[-1]):
            result['invalid'].append(number)
            continue
        relative, expected = parts[0], parts[-1]
        target = root / relative
        expected_paths.append(relative.replace('\\', '/'))
        if not target.is_file():
            result['missing'].append(relative)
        elif digest(target) == expected:
            result['matched'] += 1
        else:
            key = 'authorizedChanged' if relative in authorized else 'unauthorizedChanged'
            result[key].append(relative)
    result['manifestSha256'] = digest(manifest)
    return result


def audit() -> None:
    baseline = json.loads((OWN / 'baseline.json').read_text(encoding='utf-8-sig'))
    inputs = check_manifest(REPO / 'docs/coordination/snapshots/p4-d15-start.sha256', REPO,
                            {'docs/coordination/agents/technical-adviser.md'})
    frozen = check_manifest(OWN / 'probe-source.sha256', OWN)
    packages = []
    for package in baseline['packages']:
        target = EXTERNAL / 'workspace/node_modules' / package['package'] / 'package.json'
        packages.append({'package': package['package'], 'version': package['version'],
                         'originalShaMatched': digest(target) == package['packageSha256']})
    node_matched = digest(EXTERNAL / 'tools/node/node.exe') == baseline['nodeSha256']
    external_source = check_manifest(EXTERNAL / 'evidence/static/workspace-source.sha256', EXTERNAL / 'workspace')
    external_out = check_manifest(EXTERNAL / 'evidence/static/out-manifest-v4.tsv',
                                  EXTERNAL / 'workspace/apps/desktop/out/Maris-win32-x64')
    staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=REPO,
                            capture_output=True, text=True, check=False)
    clean = lambda item: not item['unauthorizedChanged'] and not item['missing'] and not item['invalid']
    passed = all(clean(item) for item in (inputs, frozen, external_source, external_out))
    passed = passed and node_matched and all(item['originalShaMatched'] for item in packages)
    passed = passed and staged.returncode == 0 and not staged.stdout.strip()
    record = {'passed': passed, 'repositoryInputs': inputs, 'frozenProbeSource': frozen,
              'externalBuildSource': external_source, 'externalOut': external_out,
              'externalPackages': packages, 'nodeOriginalShaMatched': node_matched,
              'stagedCount': len(staged.stdout.splitlines()), 'gitReadExit': staged.returncode,
              'gitReadWarningPresent': bool(staged.stderr.strip()),
              'scope': 'original fixed inputs and fixed external manifests; no full dependency graph acceptance'}
    save('end-audit.json', record)
    print(json.dumps({'passed': passed, 'repoMatched': inputs['matched'],
                      'authorizedChanged': inputs['authorizedChanged'], 'frozenMatched': frozen['matched'],
                      'externalSourceMatched': external_source['matched'], 'externalOutMatched': external_out['matched'],
                      'stagedCount': record['stagedCount']}))
    if not passed:
        raise SystemExit(1)


def check_document() -> None:
    data = DOCUMENT.read_bytes()
    text = data.decode('utf-8')
    links = re.findall(r'\[[^\]\n]+\]\(([^)]+)\)', text)
    missing = []
    bad_lines = []
    local_count = 0
    for link in links:
        if link.startswith(('https://', 'http://')):
            continue
        local_count += 1
        file, _, anchor = link.partition('#')
        target = (DOCUMENT.parent / file).resolve()
        if not target.exists():
            missing.append(file)
        elif anchor.startswith('L'):
            line_number = int(anchor[1:])
            if line_number < 1 or line_number > len(target.read_text(encoding='utf-8-sig').splitlines()):
                bad_lines.append(link)
    rows = []
    expected = None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith('|'):
            width = len(line.split('|')) - 2
            if expected is None:
                expected = width
            elif width != expected:
                rows.append(number)
        else:
            expected = None
    trailing = [number for number, line in enumerate(text.splitlines(), 1) if line.rstrip() != line]
    secret_markers = []
    for target in [DOCUMENT, *OWN.rglob('*')]:
        if not target.is_file():
            continue
        if target != DOCUMENT and 'temp' in target.relative_to(OWN).parts:
            continue
        if target.suffix in {'.md', '.json', '.log', '.ts', '.tsx', '.mjs', '.ps1', '.py', '.sha256'}:
            value = target.read_text(encoding='utf-8-sig')
            if re.search(r'sk-[A-Za-z0-9]{20,}|C:[/\\]Users[/\\][^\s"\']+', value):
                secret_markers.append(target.name)
    record = {'lines': len(text.splitlines()), 'headings': len(re.findall(r'^#+ ', text, re.M)),
              'markdownLocalLinks': local_count, 'missingLocalLinks': missing, 'invalidLineAnchors': bad_lines,
              'tableWidthErrors': rows, 'trailingWhitespaceLines': trailing,
              'utf8Bom': data.startswith(b'\xef\xbb\xbf'), 'endsWithNewline': data.endswith(b'\n'),
              'fenceCount': len(re.findall(r'^```', text, re.M)), 'sensitivePatternFiles': secret_markers}
    save('document-check.json', record)
    print(json.dumps(record, ensure_ascii=False))
    if missing or bad_lines or rows or trailing or secret_markers or record['utf8Bom'] or not record['endsWithNewline']:
        raise SystemExit(1)


def manifest() -> None:
    files = [DOCUMENT, ROLE] + [target for target in OWN.rglob('*') if target.is_file()
                                and 'temp' not in target.relative_to(OWN).parts and target.name != 'delivery.sha256']
    lines = [f'{target.relative_to(REPO).as_posix()}\t{digest(target)}' for target in sorted(files, key=lambda p: p.as_posix())]
    (OWN / 'delivery.sha256').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'deliveryFiles': len(lines), 'deliveryManifestSha256': digest(OWN / 'delivery.sha256')}))


{'audit': audit, 'check': check_document, 'manifest': manifest}[sys.argv[1]]()
