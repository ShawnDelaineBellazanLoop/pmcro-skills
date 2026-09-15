#!/usr/bin/env python3
"""Create a deterministic ZIP archive for one skill directory."""
import argparse, pathlib, zipfile
from common import safe_root, safe_output, sha256, excluded, now_utc

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-path', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    root = safe_root(args.skill_path)
    files = sorted((p for p in root.rglob('*') if p.is_file() and not excluded(p, args.exclude)),
                   key=lambda p: p.relative_to(root).as_posix().lower())
    if args.dry_run:
        print(f'{len(files)} files selected; archive would be {pathlib.Path(args.output).resolve()}')
        return 0
    output = safe_output(args.output, args.force)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
        manifest = '\n'.join(f'{p.relative_to(root).as_posix()}  {sha256(p)}' for p in files) + '\n'
        info = zipfile.ZipInfo('MANIFEST.sha256', (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, manifest.encode('utf-8'))
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or any(n.startswith('/') or '..' in pathlib.PurePosixPath(n).parts for n in names):
            raise RuntimeError('archive integrity validation failed')
    print(f'Wrote {len(files)} files to {output} ({sha256(output)})')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
