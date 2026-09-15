"""Shared deterministic helpers for desktop-commander utilities."""
from __future__ import annotations
import hashlib, json, os, pathlib, fnmatch
from datetime import datetime, timezone

_CONFIG_PATH = pathlib.Path(__file__).resolve().parents[1] / 'assets' / 'default-config.json'
try:
    _CONFIG = json.loads(_CONFIG_PATH.read_text(encoding='utf-8'))
except (OSError, json.JSONDecodeError):
    _CONFIG = {}
DEFAULT_EXCLUDES = set(_CONFIG.get('excluded_directory_names', ['.git', '.vs', '__pycache__', '.pytest_cache']))
DEFAULT_SUFFIXES = set(_CONFIG.get('excluded_suffixes', ['.zip', '.tmp', '.temp', '.pyc']))

def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def safe_root(path: str) -> pathlib.Path:
    root = pathlib.Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'Not a directory: {root}')
    return root

def safe_output(path: str, force: bool) -> pathlib.Path:
    result = pathlib.Path(path).expanduser().resolve()
    result.parent.mkdir(parents=True, exist_ok=True)
    if result.exists() and not force:
        raise FileExistsError(f'Output exists; use --force: {result}')
    return result

def excluded(path: pathlib.Path, patterns: list[str]) -> bool:
    if any(part in DEFAULT_EXCLUDES for part in path.parts):
        return True
    if path.suffix.lower() in DEFAULT_SUFFIXES:
        return True
    return any(fnmatch.fnmatch(path.name, p) for p in patterns)

def json_report(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
