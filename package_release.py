"""Package the novice-friendly release; requires only Python's standard library."""
from pathlib import Path
import hashlib
import zipfile

root = Path(__file__).resolve().parent
release = root / 'release'
exe = release / 'Domex-Windows10-Patch.exe'
zip_path = release / 'Domex-Windows10-Patch-v1.0.0.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for src, name in [
        (exe, exe.name),
        (root / 'START-HERE.txt', 'START-HERE.txt'),
        (root / 'README.md', 'README.md'),
        (root / 'LICENSE', 'LICENSE'),
        (root / 'THIRD-PARTY-NOTICE.md', 'THIRD-PARTY-NOTICE.md'),
    ]:
        # A fixed timestamp and explicit attributes avoid local mtime noise.
        info = zipfile.ZipInfo(name, date_time=(2026, 11, 9, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, src.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
files = [exe, zip_path]
(release / 'SHA256SUMS.txt').write_text(
    ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files),
    encoding='ascii',
)
for p in files:
    print(f'{p.name}: {p.stat().st_size:,} bytes')
