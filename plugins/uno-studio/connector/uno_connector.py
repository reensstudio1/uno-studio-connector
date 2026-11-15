#!/usr/bin/env python3
"""Uno Studio connector for Claude Code.

Finds the Uno Studio folder on this computer and runs Uno's OWN MCP server (mcp/uno_studio_mcp.py, shipped with Uno).
This file contains no Uno app code. It never edits projects itself; Uno's server saves every change as a new version.

Where it looks (first match wins):
  1. environment variable UNO_STUDIO_ROOT
  2. ~/.uno-studio-connector.json  {"root": "..."}   (written by --set-root)
  3. ~/Library/Application Support/Uno Studio/active-root  (written by the Uno installer)
  4. common folders: ~/Applications, ~/Desktop, ~/Downloads, ~/Documents, /Applications  (…/Uno Studio, one level deep)
  5. Spotlight (mdfind) for mcp/uno_studio_mcp.py
A valid Uno folder has server.py and mcp/uno_studio_mcp.py.

Command line (for the installer and for support):
  python3 uno_connector.py --where            print the Uno folder that will be used
  python3 uno_connector.py --set-root PATH    remember a folder (backs up the previous setting)
  python3 uno_connector.py --version
Without arguments it speaks MCP on stdin/stdout.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

VERSION = "1.0.0"
HOME = os.path.expanduser("~")
CONF = os.path.join(HOME, ".uno-studio-connector.json")


def valid(root):
    return bool(root) and os.path.isfile(os.path.join(root, "server.py")) and os.path.isfile(os.path.join(root, "mcp", "uno_studio_mcp.py"))


def candidates():
    yield "env UNO_STUDIO_ROOT", os.environ.get("UNO_STUDIO_ROOT")
    try:
        yield "~/.uno-studio-connector.json", json.load(open(CONF, encoding="utf-8")).get("root")
    except (OSError, ValueError):
        pass
    try:
        yield "Uno active-root", open(os.path.join(HOME, "Library", "Application Support", "Uno Studio", "active-root"), encoding="utf-8").read().strip()
    except OSError:
        pass
    for base in [os.path.join(HOME, d) for d in ("Applications", "Desktop", "Downloads", "Documents")] + ["/Applications"]:
        yield base, os.path.join(base, "Uno Studio")
        for p in sorted(glob.glob(os.path.join(base, "*", "Uno Studio"))):
            yield base, p
    if sys.platform == "darwin" and shutil.which("mdfind"):
        try:
            out = subprocess.run(["mdfind", "-name", "uno_studio_mcp.py"], capture_output=True, text=True, timeout=4).stdout
            for line in out.splitlines():
                if line.endswith(os.path.join("mcp", "uno_studio_mcp.py")):
                    yield "Spotlight", os.path.dirname(os.path.dirname(line))
        except (OSError, subprocess.SubprocessError):
            pass


def find_root():
    tried = []
    for how, root in candidates():
        if not root:
            continue
        root = os.path.abspath(os.path.expanduser(root))
        if "/.Trash/" in root or root.startswith(("/private/var/folders/", "/var/folders/")):
            continue          # סל המחזור / אפליקציה שהופעלה ישירות מתוך zip (App Translocation)
        if valid(root):
            return root, how, tried
        tried.append(root)
    return None, None, tried


def set_root(path):
    path = os.path.abspath(os.path.expanduser(path))
    if not valid(path):
        sys.exit("Not an Uno Studio folder (needs server.py and mcp/uno_studio_mcp.py): %s" % path)
    if os.path.isfile(CONF):
        shutil.copy2(CONF, CONF + ".bak-%s" % time.strftime("%Y%m%d-%H%M%S"))
    tmp = CONF + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"root": path, "set_at": time.strftime("%Y-%m-%d %H:%M:%S"), "connector": VERSION}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONF)
    print("Uno Studio folder saved: %s" % path)


def fallback_server(tried):
    """No Uno folder found: a tiny MCP server with one tool that explains what to do (Claude Code shows it as connected)."""
    msg = ("Uno Studio was not found on this computer.\n"
           "1. Install Uno Studio (the folder with 'Uno Studio.app' that your course gave you) and open it once.\n"
           "2. If it is in an unusual place, run:  python3 \"%s\" --set-root \"/path/to/Uno Studio\"\n"
           "3. Restart Claude Code (or run /mcp → reconnect).\n\nFolders checked: %s"
           % (os.path.abspath(__file__), ", ".join(tried[:12]) or "none"))
    tool = {"name": "uno_status", "description": "Explains why the Uno Studio tools are not available yet and how to connect them.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}
    for line in sys.stdin:
        try:
            req = json.loads(line)
        except ValueError:
            continue
        rid, m = req.get("id"), req.get("method")
        if rid is None:
            continue
        if m == "initialize":
            res = {"protocolVersion": (req.get("params") or {}).get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {}},
                   "serverInfo": {"name": "uno-studio", "title": "Uno Studio (not found)", "version": VERSION}}
        elif m == "tools/list":
            res = {"tools": [tool]}
        elif m == "tools/call":
            res = {"content": [{"type": "text", "text": msg}], "isError": True}
        else:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}) + "\n"); sys.stdout.flush()
            continue
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "result": res}, ensure_ascii=False) + "\n"); sys.stdout.flush()


def main():
    a = sys.argv[1:]
    if a[:1] == ["--version"]:
        print(VERSION); return
    if a[:1] == ["--set-root"] and len(a) > 1:
        set_root(a[1]); return
    root, how, tried = find_root()
    if a[:1] == ["--where"]:
        print(json.dumps({"root": root, "found_by": how, "checked": tried, "connector": VERSION}, ensure_ascii=False, indent=2)); return
    if not root:
        fallback_server(tried); return
    env = dict(os.environ, UNO_STUDIO_ROOT=root)
    mcp = os.path.join(root, "mcp", "uno_studio_mcp.py")
    os.chdir(root)
    os.execve(sys.executable, [sys.executable, mcp], env)      # אותו stdin/stdout — Claude מדבר ישירות עם השרת של Uno


if __name__ == "__main__":
    main()
