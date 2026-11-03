"""Copy only the authorized synthetic W1 profile; forbid reparse points at every depth."""
from pathlib import Path
import json, os, stat, hashlib, shutil, datetime
ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'tests/independent/desktop/evidence/r11-r1-windows'
SOURCE=Path('C:/MarisC12/C12-R9-QUIT-20261016-011200')
DEST=Path('C:/MarisC12/C12-R11-R1-WINDOWS-20261103-002800')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p,base):
    assert p.resolve().is_relative_to(base.resolve()) and not p.is_symlink()
    assert not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
def inventory(base):
    files=[]
    for p in [base,base/'profile-main',base/'continuity.json']:
        check(p,base)
    for p in sorted((base/'profile-main').rglob('*')):
        check(p,base)
        if p.is_file(): files.append([p.relative_to(base).as_posix(),p.stat().st_size,sha(p)])
    p=base/'continuity.json';files.append(['continuity.json',p.stat().st_size,sha(p)])
    return sorted(files)
def main():
    assert '2026-11-03T00:05:00+08:00' in (ROOT/'docs/coordination/control.md').read_text(encoding='utf8')
    assert json.loads((E/'repository-gate.json').read_text(encoding='utf8'))['passed']
    assert json.loads((E/'observe-v3.json').read_text(encoding='utf-8'))['stages'][0]['relatedCount']==0
    assert (SOURCE/'r9-owned-marker.txt').read_text(encoding='utf8')=='P4-C12-R9-QUIT 20261016-011200'
    assert json.loads((ROOT/'tests/independent/desktop/evidence/r9-quit/windows-W1/result.json').read_text(encoding='utf8'))['passed']
    for parent in [SOURCE.parent,SOURCE,DEST.parent]: check(parent,parent)
    assert not DEST.exists()
    manifest=ROOT/'tests/independent/desktop/evidence/r9-r1/original-profile.tsv'
    assert sha(manifest)=='575f132e0bc44a949391c9ab7c31747e4e21e58fdb8a344dc29a00e6639ce7ee'
    expected=[[row[0],int(row[1]),row[2]] for row in [v.split('\t') for v in manifest.read_text(encoding='utf8').splitlines()]]
    original=inventory(SOURCE)
    assert original==expected==inventory(Path('C:/MarisC12/C12-R9-R1-20261017-001500'))==inventory(Path('C:/MarisC12/C12-R9-R2-20261017-233500'))
    DEST.mkdir()
    (DEST/'r11-r1-owned-marker.txt').write_text('P4-C12-R11-R1-WINDOWS 20261103-002800',encoding='utf8')
    shutil.copytree(SOURCE/'profile-main',DEST/'profile-main',copy_function=shutil.copyfile)
    shutil.copyfile(SOURCE/'continuity.json',DEST/'continuity.json')
    copied=inventory(DEST);assert original==copied and inventory(SOURCE)==original
    for name in ['output','os-env/appdata','os-env/localappdata','os-env/temp']:(DEST/name).mkdir(parents=True)
    manifest=''.join(f'{p}\t{n}\t{h}\n' for p,n,h in original)
    (E/'original-profile.tsv').write_text(manifest,encoding='utf8',newline='\n')
    (E/'profile-copy.json').write_text(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'sourceRoot':str(SOURCE),'copyRoot':str(DEST),'files':len(original),'manifestSha256':hashlib.sha256(manifest.encode()).hexdigest(),'allBytesAndHashesEqual':True,'sourceAfterCopyUnchanged':True,'allPathsNoReparse':True,'mode':'ordinary full byte copy after W1 close; no original writes'},indent=2)+'\n',encoding='utf8')
    print(json.dumps({'profileCopyPassed':True,'files':len(original)}))
if __name__=='__main__':main()
