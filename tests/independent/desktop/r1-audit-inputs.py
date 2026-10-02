"""Read-only C12-R1 endpoint audit; never launch a product or modify old evidence."""
import hashlib
import json
import mmap
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parent
MANIFEST = ROOT / "docs/coordination/snapshots/p4-c12-r1-start.sha256"
EXPECTED = "0922a37c45e42fb28be69a2405eac8b6de8b05ea9e22d22309a5a74be767bd15"
AUTHORIZED = {
    "docs/coordination/agents/tester.md",
    "docs/testing/phase-4-c12-windows-shell-report.md",
    "docs/testing/phase-4-c12-manual-checklist.md",
    "docs/testing/phase-4-modular-agent-host-test-matrix.md",
}
CLEAN = Path("C:/MarisOutboxR2/R2-20261001-155509/workspace")
ARTIFACTS = {
    "apps/desktop/out/Maris-win32-x64/Maris.exe": "8eb56f3f63b923471a9239e2a01f29a8111067a6093d8c9d118e62e1ccfb5c2a",
    "apps/desktop/out/Maris-win32-x64/resources/app.asar": "74225ea63dbc7201dc7f7f3299a099ac573f51680ef705536e560a9d9df6b6c7",
    "pnpm-lock.yaml": "5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a",
}


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    assert digest(MANIFEST) == EXPECTED
    entries = [line.split("\t") for line in MANIFEST.read_text(encoding="utf-8").splitlines()]
    assert len(entries) == len({name for name, _ in entries}) == 296
    unchanged, authorized, missing, unauthorized = [], [], [], []
    for name, expected in entries:
        path = ROOT / name
        if not path.is_file():
            missing.append(name)
        elif digest(path) == expected:
            unchanged.append(name)
        elif name in AUTHORIZED:
            authorized.append(name)
        else:
            unauthorized.append(name)
    old = [name for name, _ in entries if name.startswith("tests/independent/desktop/")]
    assert len(old) == 8 and all(name in unchanged for name in old)
    artifacts = [{"path": name, "expected": expected, "actual": digest(CLEAN / name)}
                 for name, expected in ARTIFACTS.items()]
    exe = CLEAN / "apps/desktop/out/Maris-win32-x64/Maris.exe"
    with exe.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as image:
        sentinel = b"dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX"
        offset = image.find(sentinel)
        assert offset >= 0
        wire = offset + len(sentinel)
        version, length = image[wire], image[wire + 1]
        states = list(image[wire + 2:wire + 2 + length])
    assert version == 1 and states[:6] == [48, 49, 48, 48, 49, 49]
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    result = {"manifest_sha256": EXPECTED, "entries": len(entries), "unchanged": len(unchanged),
              "authorized_changed": authorized, "unauthorized_mismatch": unauthorized,
              "missing": missing, "old_independent_files_unchanged": old,
              "artifacts": artifacts, "fuses": {"version": version, "states": states},
              "staged_paths": staged.stdout.splitlines(), "git_warning": staged.stderr.strip(),
              "product_launches": 0, "auxiliary_electron_launches": 0}
    (OWN / "evidence/r1/end-audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["entries", "unchanged", "authorized_changed",
          "unauthorized_mismatch", "missing", "staged_paths", "fuses"]}, ensure_ascii=False))
    assert not unauthorized and not missing and not result["staged_paths"]
    assert all(item["actual"] == item["expected"] for item in artifacts)


if __name__ == "__main__":
    main()
