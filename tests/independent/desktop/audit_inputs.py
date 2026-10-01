"""C12 read-only input verification; writes only its own evidence directory."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parent
MANIFEST = ROOT / "docs/coordination/snapshots/p4-c12-windows-shell-start.sha256"
EXPECTED_MANIFEST = "dfcd5a21fc34e36155e90d9fb1862ea878a664d438cf422e0ad8f537e68bc081"
AUTHORIZED = {
    "docs/testing/phase-4-modular-agent-host-test-matrix.md",
    "docs/coordination/agents/tester.md",
}
CLEAN = Path("C:/MarisE5Final/E5-PKG-FINAL-20260929-1732/workspace")
ARTIFACTS = {
    "apps/desktop/out/Maris-win32-x64/Maris.exe": "f5cf7ad3b4d89a02cca925152ec8d7b5554ccba6ebff025bf04eb24195405641",
    "apps/desktop/out/Maris-win32-x64/resources/app.asar": "bcdf6f889a5be95d7270fb249db8eff45b1421a5fdd7879d2342cb333d7f1274",
    "pnpm-lock.yaml": "5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a",
}


def digest(file):
    with file.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    raw = MANIFEST.read_bytes()
    entries = [line.split("\t") for line in raw.decode("utf-8").splitlines()]
    assert digest(MANIFEST) == EXPECTED_MANIFEST
    assert len(entries) == 277 and len({p for p, _ in entries}) == 277
    unchanged, changed, mismatch, missing = [], [], [], []
    for name, expected in entries:
        file = ROOT / name
        if not file.is_file():
            missing.append(name)
        elif digest(file) == expected:
            unchanged.append(name)
        elif name in AUTHORIZED:
            changed.append(name)
        else:
            mismatch.append(name)
    artifacts = [{"path": str(CLEAN / name), "expected": expected,
                  "actual": digest(CLEAN / name)} for name, expected in ARTIFACTS.items()]
    staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    result = {"manifest_sha256": digest(MANIFEST), "entries": len(entries),
              "unchanged": len(unchanged), "authorized_changed": changed,
              "unauthorized_mismatch": mismatch, "missing": missing,
              "artifacts": artifacts, "staged_paths": staged.stdout.splitlines(),
              "git_warning": staged.stderr.strip(), "product_launches": 0,
              "external_profile_created": False}
    (OWN / "evidence/final-input-audit.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["entries", "unchanged", "authorized_changed",
          "unauthorized_mismatch", "missing", "staged_paths"]}, ensure_ascii=False))
    assert not missing and not mismatch and not result["staged_paths"]
    assert all(item["expected"] == item["actual"] for item in artifacts)


if __name__ == "__main__":
    main()
