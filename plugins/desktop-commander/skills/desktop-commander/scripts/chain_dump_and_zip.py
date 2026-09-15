#!/usr/bin/env python3
"""Generate skills_dump.txt, verify it, then archive the dump."""
import argparse, pathlib, subprocess, sys, zipfile
from common import safe_root, safe_output, sha256

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-root', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    root = safe_root(args.skills_root)
    out = pathlib.Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    dump = out / 'skills_dump.txt'
    archive = out / 'skills_dump.zip'
    command = [sys.executable, str(pathlib.Path(__file__).with_name('dump_skill_folder.py')), '--skills-root', str(root), '--output', str(dump)]
    if args.force: command.append('--force')
    if args.dry_run: command.append('--dry-run')
    subprocess.run(command, check=True)
    if args.dry_run: return 0
    if not dump.is_file() or dump.stat().st_size == 0:
        raise RuntimeError('dump was not created or is empty')
    archive = safe_output(str(archive), args.force)
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        info = zipfile.ZipInfo('skills_dump.txt', (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, dump.read_bytes())
    with zipfile.ZipFile(archive) as zf:
        if zf.namelist() != ['skills_dump.txt']:
            raise RuntimeError('archive verification failed')
    print(f'Created {dump} ({sha256(dump)}) and {archive} ({sha256(archive)})')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
