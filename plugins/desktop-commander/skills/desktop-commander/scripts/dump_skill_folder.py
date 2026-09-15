#!/usr/bin/env python3
"""Dump all readable files below a skills root in stable order."""
import argparse, pathlib
from common import safe_root, safe_output, sha256, excluded, json_report, now_utc

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--json-report')
    args = parser.parse_args()
    root = safe_root(args.skills_root)
    output = pathlib.Path(args.output).expanduser().resolve()
    files = sorted((p for p in root.rglob('*') if p.is_file() and not excluded(p, args.exclude)),
                   key=lambda p: p.relative_to(root).as_posix().lower())
    if args.dry_run:
        print(f'{len(files)} files selected; output would be {output}')
        return 0
    output = safe_output(args.output, args.force)
    records = []
    with output.open('w', encoding='utf-8', newline='\n') as dest:
        for path in files:
            relative = path.relative_to(root).as_posix()
            record = {'path': relative, 'absolute_path': str(path), 'sha256': sha256(path), 'size_bytes': path.stat().st_size}
            records.append(record)
            dest.write('=' * 80 + '\n')
            dest.write(f"FILE: {relative}\nABSOLUTE_PATH: {path}\nSHA256: {record['sha256']}\nSIZE_BYTES: {record['size_bytes']}\n")
            dest.write('=' * 80 + '\n\n')
            try:
                dest.write(path.read_text(encoding='utf-8'))
            except UnicodeDecodeError:
                dest.write('[binary or non-UTF-8 file omitted]\n')
            dest.write('\n\n')
    report = {'created_utc': now_utc(), 'root': str(root), 'output': str(output), 'file_count': len(records), 'files': records, 'output_sha256': sha256(output)}
    if args.json_report:
        json_report(safe_output(args.json_report, args.force), report)
    print(f'Wrote {len(records)} files to {output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
