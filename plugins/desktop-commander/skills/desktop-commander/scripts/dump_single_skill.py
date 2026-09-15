#!/usr/bin/env python3
"""Dump one skill directory using the same format as dump_skill_folder."""
import argparse, pathlib, sys
from dump_skill_folder import main as dump_all
from common import safe_root

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill_name', nargs='?')
    parser.add_argument('--skills-root')
    parser.add_argument('--skill-path')
    parser.add_argument('--output', required=True)
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--json-report')
    args = parser.parse_args()
    if bool(args.skills_root) == bool(args.skill_path):
        parser.error('provide exactly one of --skills-root or --skill-path')
    skill = pathlib.Path(args.skill_path).expanduser().resolve() if args.skill_path else safe_root(args.skills_root) / args.skill_name
    skill = skill.resolve()
    if not skill.is_dir() or not (skill / 'SKILL.md').is_file():
        parser.error(f'not a valid skill package: {skill}')
    forwarded = ['--skills-root', str(skill), '--output', args.output]
    for pattern in args.exclude:
        forwarded += ['--exclude', pattern]
    if args.force: forwarded.append('--force')
    if args.dry_run: forwarded.append('--dry-run')
    if args.json_report: forwarded += ['--json-report', args.json_report]
    sys.argv = [sys.argv[0]] + forwarded
    return dump_all()

if __name__ == '__main__':
    raise SystemExit(main())
