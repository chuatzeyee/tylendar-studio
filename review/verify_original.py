"""Read-only verification of the original project against the copy-time snapshot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parent / 'Tylendar'
IGNORED = {'.git', '.gradle', '.kotlin', '.ruff_cache', '__pycache__', 'build', '.DS_Store', 'local.properties', 'config.h'}
expected = json.loads((ROOT / 'review/original-source-sha256.json').read_text())
current = {
    str(p.relative_to(ORIGINAL)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in ORIGINAL.rglob('*')
    if p.is_file() and not any(part in IGNORED for part in p.relative_to(ORIGINAL).parts)
}
changed = [name for name in sorted(expected.keys() | current.keys()) if expected.get(name) != current.get(name)]
if changed:
    raise SystemExit('Original source changed: ' + ', '.join(changed))
print(f'PASS: all {len(expected)} original source and asset files are byte-for-byte unchanged; no source or assets were added or removed.')
