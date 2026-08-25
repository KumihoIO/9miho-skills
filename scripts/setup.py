#!/usr/bin/env python3
"""Register miho-mcp with the agent hosts installed on this machine.

Idempotent by design: an existing `miho` entry is left untouched unless it
is missing or points at a different command, so re-running after a 9miho
move is the supported way to repoint everything. Claude Code is configured
through its own CLI when present; Cursor, OpenCode and Codex are written
directly. Anything undetectable prints exact manual instructions instead of
guessing at a config format.

Stdlib only — this file ships in a repo users clone before installing
anything else.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:9999"
HOME = Path.home()


def ask(message: str, default: str) -> str:
    try:
        answer = input(f"{message} [{default}]: ").strip()
    except EOFError:
        return default
    return answer or default


def healthz(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(
            f"{base_url.rstrip('/')}/api/healthz", timeout=5
        ) as response:
            return response.status == 200
    except OSError:
        return False


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"  ! {path} is not valid JSON; skipping it — fix by hand")
        return {}
    return data if isinstance(data, dict) else {}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def entry_changed(existing: object, wanted: dict) -> bool:
    return existing != wanted


def write_cursor(repo: str, url: str) -> None:
    path = HOME / ".cursor" / "mcp.json"
    data = load_json(path)
    servers = data.setdefault("mcpServers", {})
    wanted = {
        "command": "uv",
        "args": ["run", "--directory", repo, "miho-mcp"],
        "env": {"MIHO_SERVER_URL": url},
    }
    if servers.get("miho") == wanted:
        print("= cursor: already registered")
        return
    servers["miho"] = wanted
    save_json(path, data)
    print(f"+ cursor: wrote {path}")


def write_opencode(repo: str, url: str) -> None:
    # opencode's docs put global config at ~/.config/opencode/opencode.json;
    # XDG_CONFIG_HOME moves the base on platforms that redirect it.
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else HOME / ".config"
    path = base / "opencode" / "opencode.json"
    data = load_json(path)
    mcp = data.setdefault("mcp", {})
    wanted = {
        "type": "local",
        "command": ["uv", "run", "--directory", repo, "miho-mcp"],
        "environment": {"MIHO_SERVER_URL": url},
        "enabled": True,
    }
    if mcp.get("miho") == wanted:
        print("= opencode: already registered")
        return
    mcp["miho"] = wanted
    save_json(path, data)
    print(f"+ opencode: wrote {path}")


CODEX_TOML_BLOCK = """[mcp_servers.miho]
command = "uv"
args = ["run", "--directory", "{repo}", "miho-mcp"]

[mcp_servers.miho.env]
MIHO_SERVER_URL = "{url}"
"""


def write_codex(repo: str, url: str) -> None:
    path = HOME / ".codex" / "config.toml"
    block = CODEX_TOML_BLOCK.format(repo=repo, url=url)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    if "[mcp_servers.miho]" in existing:
        if f'"{repo}"' in existing and url in existing:
            print("= codex: already registered")
            return
        print(
            f"! codex: [mcp_servers.miho] already exists in {path} with "
            "different values — review it by hand"
        )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    sep = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(existing + sep + block + "\n", encoding="utf-8")
    print(f"+ codex: appended to {path}")


def configure_claude(repo: str, url: str) -> None:
    from shutil import which

    cli = which("claude")
    if not cli:
        print(
            "! claude CLI not found — register manually:\n"
            f"  claude mcp add -e MIHO_SERVER_URL={url} miho -- "
            f"uv run --directory {repo} miho-mcp"
        )
        return
    import subprocess

    result = subprocess.run(
        [cli, "mcp", "list"], capture_output=True, text=True, check=False
    )
    if "miho" in result.stdout.lower():
        print("= claude: already registered")
        return
    subprocess.run(
        [
            cli,
            "mcp",
            "add",
            "-e",
            f"MIHO_SERVER_URL={url}",
            "miho",
            "--",
            "uv",
            "run",
            "--directory",
            repo,
            "miho-mcp",
        ],
        check=False,
    )
    print("+ claude: registered via `claude mcp add`")


def main() -> int:
    print("9miho skills setup\n")
    repo = ask("Path to your 9miho checkout", str(Path.cwd().parent / "9miho"))
    url = ask("9miho server URL", DEFAULT_URL)

    if not healthz(url):
        print(
            f"! {url}/api/healthz did not answer. Start the server first "
            "(uv run miho-server); registration can still be written now and "
            "will connect once it runs."
        )

    hosts = [
        ("cursor", lambda: write_cursor(repo, url)),
        ("opencode", lambda: write_opencode(repo, url)),
        ("codex", lambda: write_codex(repo, url)),
        ("claude", lambda: configure_claude(repo, url)),
    ]
    for name, fn in hosts:
        try:
            fn()
        except Exception as exc:  # one host failing must not stop the rest
            print(f"! {name}: {exc}")

    print(
        "\nNext steps:\n"
        "  1. Restart each host so MCP servers reload.\n"
        "  2. In the 9miho checkout, seed guidance once:\n"
        "       uv run python scripts/ingest_skills.py\n"
        "  3. Ask your agent to call list_skills().\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
