#!/usr/bin/env python3
"""Merge a local MCP entry into Claude Desktop; preserve other settings."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(release):
    if not re.fullmatch(r'v\d+\.\d+\.\d+', release):
        raise ValueError('Invalid version')
    home = Path.home()
    base = home / '.uno-studio-connector'
    launcher = Path(__file__).resolve().parent / 'plugins/uno-studio/connector/uno_connector.py'
    if not launcher.is_file():
        raise ValueError('Missing connector launcher')
    config = home / 'Library/Application Support/Claude/claude_desktop_config.json'
    original = config.read_bytes() if config.exists() else None
    data = json.loads(original) if original is not None else {}
    if not isinstance(data, dict) or not isinstance(data.get('mcpServers', {}), dict):
        raise ValueError('Invalid Claude configuration; no changes made')
    servers = data.setdefault('mcpServers', {})
    entry = {'command': os.path.realpath(sys.executable), 'args': [str(launcher)]}
    old = servers.get('uno-studio')
    if old is not None and not (isinstance(old, dict) and any('uno_connector.py' in str(a) or 'uno_studio_mcp.py' in str(a) for a in old.get('args', []))):
        raise ValueError('Unrelated server already named uno-studio; no changes made')
    if isinstance(old, dict):
        entry = dict(old, **entry)
    if old != entry:
        backup = base / 'backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup.mkdir(parents=True)
        if original is not None:
            atomic_write(backup / config.name, original.decode('utf-8'))
        else:
            atomic_write(backup / 'config-was-absent.txt', 'No previous configuration.\n')
        servers['uno-studio'] = entry
        now = config.read_bytes() if config.exists() else None
        if now != original:
            raise ValueError('Configuration changed concurrently; retry safely')
        atomic_write(config, json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print('Backup:', backup)
    current = base / 'current-desktop'
    previous = current.read_text().strip() if current.exists() else ''
    if previous and previous != release:
        atomic_write(base / 'previous-desktop', previous + '\n')
    atomic_write(current, release + '\n')
    print('Registered local MCP: uno-studio')
    print('Configuration:', config)
    print('When active work finishes, restart Claude Desktop; check Customize > Connectors > Yours > uno-studio.')
    print('No restart, plugin installation, or Uno project/media changes performed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', required=True)
    args = parser.parse_args()
    try:
        install(args.release)
    except (ValueError, OSError) as exc:
        sys.exit(str(exc))
