#!/usr/bin/env python3
"""Run a desktop-commander operation from one request JSON object."""
from __future__ import annotations
import argparse, json, pathlib, subprocess, sys

ALLOWED = {
    'dump_skill_folder': 'dump_skill_folder.py',
    'dump_single_skill': 'dump_single_skill.py',
    'zip_skill': 'zip_skill.py',
    'chain_dump_and_zip': 'chain_dump_and_zip.py',
}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    request_path = pathlib.Path(args.request).expanduser().resolve()
    request = json.loads(request_path.read_text(encoding='utf-8'))
    operation = request.get('operation')
    if operation not in ALLOWED:
        raise ValueError(f'unsupported operation: {operation!r}')
    root = pathlib.Path(__file__).resolve().parent
    script = root / ALLOWED[operation]
    if operation == 'dump_skill_folder':
        required = ('skills_root', 'output')
        command = ['--skills-root', request['skills_root'], '--output', request['output']]
    elif operation == 'dump_single_skill':
        required = ('output',)
        command = ['--output', request['output']]
        if request.get('skill_path'):
            command += ['--skill-path', request['skill_path']]
        else:
            required += ('skills_root', 'skill_name')
            command += ['--skills-root', request['skills_root'], request['skill_name']]
    elif operation == 'zip_skill':
        required = ('skill_path', 'output')
        command = ['--skill-path', request['skill_path'], '--output', request['output']]
    else:
        required = ('skills_root', 'output_dir')
        command = ['--skills-root', request['skills_root'], '--output-dir', request['output_dir']]
    missing = [key for key in required if not request.get(key)]
    if missing:
        raise ValueError('missing request fields: ' + ', '.join(missing))
    if request.get('force'): command.append('--force')
    if request.get('dry_run'): command.append('--dry-run')
    result = subprocess.run([sys.executable, str(script), *command], text=True)
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
