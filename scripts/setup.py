#!/usr/bin/env python3
"""Register 9miho's installed Desktop runtime with supported agent hosts.

The default path is the signed runtime installed by Kumiho Desktop, never a
private checkout.  Development source mode exists only through the explicit
``--source-checkout`` option.

The updater is deliberately fail-closed.  It may add a missing ``miho``
entry or migrate the exact legacy ``uv run --directory ... miho-mcp`` shape
written by setup 0.4.2 and earlier.  It backs up an existing file before a
write and never overwrites an unrecognized, user-owned ``miho`` entry.

PUBLICATION SYNC: this file is copied into the public tree by the private
``scripts/gen_skill_stubs.py`` generator.  Keep ``McpCommand``, the legacy
classifiers, and the config paths below as the narrow synchronization seam.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Sequence


DEFAULT_URL = "http://127.0.0.1:9999"
MANAGED_BEGIN = "# BEGIN 9MIHO MANAGED MCP"
MANAGED_END = "# END 9MIHO MANAGED MCP"
Action = Literal["apply", "check", "dry-run"]


class SetupError(RuntimeError):
    """A host config could not be changed without risking user data."""


@dataclass(frozen=True)
class McpCommand:
    command: str
    args: tuple[str, ...]
    required_path: Path
    required_kind: Literal["file", "directory"]
    mode: Literal["desktop", "source"]


@dataclass(frozen=True)
class HostResult:
    host: str
    state: Literal["current", "updated", "drift", "skipped", "error"]
    message: str


def installed_binary(home: Path, platform: str | None = None) -> Path:
    platform = platform or sys.platform
    name = "9miho.exe" if platform.startswith("win") else "9miho"
    return home / ".kumiho" / "apps" / "9miho" / "bin" / name


def desktop_command(home: Path, platform: str | None = None) -> McpCommand:
    binary = installed_binary(home, platform)
    return McpCommand(
        command=str(binary),
        args=("--mcp-stdio",),
        required_path=binary,
        required_kind="file",
        mode="desktop",
    )


def source_command(checkout: Path) -> McpCommand:
    checkout = checkout.expanduser().resolve()
    return McpCommand(
        command="uv",
        args=("run", "--directory", str(checkout), "miho-mcp"),
        required_path=checkout,
        required_kind="directory",
        mode="source",
    )


def _json_entry(command: McpCommand, url: str) -> dict[str, object]:
    return {
        "command": command.command,
        "args": list(command.args),
        "env": {"MIHO_SERVER_URL": url},
    }


def _opencode_entry(command: McpCommand, url: str) -> dict[str, object]:
    return {
        "type": "local",
        "command": [command.command, *command.args],
        "environment": {"MIHO_SERVER_URL": url},
        "enabled": True,
    }


def _claude_entry(command: McpCommand, url: str) -> dict[str, object]:
    return {"type": "stdio", **_json_entry(command, url)}


def _legacy_uv_parts(
    command: object, args: object, environment: object, expected_url: str
) -> bool:
    return (
        command in {"uv", "uv.exe"}
        and isinstance(args, list)
        and len(args) == 4
        and args[:2] == ["run", "--directory"]
        and isinstance(args[2], str)
        and bool(args[2])
        and args[3] == "miho-mcp"
        and isinstance(environment, dict)
        and set(environment) == {"MIHO_SERVER_URL"}
        and environment["MIHO_SERVER_URL"] == expected_url
    )


def _legacy_json_entry(entry: object, expected_url: str) -> bool:
    return (
        isinstance(entry, dict)
        and set(entry) == {"command", "args", "env"}
        and _legacy_uv_parts(entry["command"], entry["args"], entry["env"], expected_url)
    )


def _legacy_opencode_entry(entry: object, expected_url: str) -> bool:
    if not isinstance(entry, dict) or set(entry) != {
        "type", "command", "environment", "enabled"
    }:
        return False
    tokens = entry["command"]
    return (
        entry["type"] == "local"
        and entry["enabled"] is True
        and isinstance(tokens, list)
        and len(tokens) == 5
        and _legacy_uv_parts(tokens[0], tokens[1:], entry["environment"], expected_url)
    )


def _legacy_claude_entry(entry: object, expected_url: str) -> bool:
    return (
        isinstance(entry, dict)
        and set(entry) == {"type", "command", "args", "env"}
        and entry["type"] == "stdio"
        and _legacy_uv_parts(entry["command"], entry["args"], entry["env"], expected_url)
    )


def _backup(path: Path) -> Path | None:
    if not path.is_file():
        return None
    backup = path.with_name(path.name + ".9miho-setup.bak")
    suffix = 1
    while backup.exists():
        backup = path.with_name(path.name + f".9miho-setup.{suffix}.bak")
        suffix += 1
    shutil.copy2(path, backup)
    return backup


def _atomic_text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        temporary_path.write_text(body, encoding="utf-8", newline="\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SetupError(f"{path} is not valid UTF-8 JSON; it was not changed") from exc
    if not isinstance(parsed, dict):
        raise SetupError(f"{path} is not a JSON object; it was not changed")
    return parsed


def _write_json(path: Path, body: dict) -> Path | None:
    backup = _backup(path)
    _atomic_text(path, json.dumps(body, indent=2, ensure_ascii=False) + "\n")
    return backup


def _replace_json_entry(
    path: Path,
    container_name: str,
    wanted: dict[str, object],
    legacy: Callable[[object], bool],
    action: Action,
) -> tuple[str, Path | None]:
    body = _load_json(path)
    if container_name in body:
        servers = body[container_name]
    else:
        servers = {}
    if not isinstance(servers, dict):
        raise SetupError(f"{path}: {container_name!r} is not an object; it was not changed")
    has_entry = "miho" in servers
    current = servers.get("miho")
    if current == wanted:
        return "current", None
    is_legacy = legacy(current)
    if has_entry and not is_legacy:
        raise SetupError(
            f"{path}: existing 'miho' entry is user-owned; it was not overwritten"
        )
    if action != "apply":
        return "drift", None
    servers["miho"] = wanted
    body[container_name] = servers
    backup = _write_json(path, body)
    return ("migrated legacy entry" if is_legacy else "registered"), backup


def configure_cursor(
    home: Path, command: McpCommand, url: str, action: Action
) -> tuple[Path, str, Path | None]:
    path = home / ".cursor" / "mcp.json"
    state, backup = _replace_json_entry(
        path,
        "mcpServers",
        _json_entry(command, url),
        lambda entry: _legacy_json_entry(entry, url),
        action,
    )
    return path, state, backup


def configure_opencode(
    home: Path,
    command: McpCommand,
    url: str,
    action: Action,
    environment: dict[str, str],
) -> tuple[Path, str, Path | None]:
    configured = environment.get("XDG_CONFIG_HOME")
    base = Path(configured).expanduser() if configured else home / ".config"
    path = base / "opencode" / "opencode.json"
    state, backup = _replace_json_entry(
        path,
        "mcp",
        _opencode_entry(command, url),
        lambda entry: _legacy_opencode_entry(entry, url),
        action,
    )
    return path, state, backup


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _codex_block(command: McpCommand, url: str) -> str:
    args = ", ".join(_toml_string(value) for value in command.args)
    return "\n".join(
        (
            MANAGED_BEGIN,
            "[mcp_servers.miho]",
            f"command = {_toml_string(command.command)}",
            f"args = [{args}]",
            "",
            "[mcp_servers.miho.env]",
            f"MIHO_SERVER_URL = {_toml_string(url)}",
            MANAGED_END,
        )
    )


LEGACY_CODEX_BLOCK = re.compile(
    r'^\[mcp_servers\.miho\]\r?\n'
    r'command\s*=\s*"(?:uv|uv\.exe)"\r?\n'
    r'args\s*=\s*\["run",\s*"--directory",\s*"(?:\\.|[^"\\])*",\s*"miho-mcp"\]\r?\n'
    r'\r?\n'
    r'^\[mcp_servers\.miho\.env\]\r?\n'
    r'MIHO_SERVER_URL\s*=\s*"(?:\\.|[^"\\])*"\r?\n?',
    re.MULTILINE,
)


def configure_codex(
    home: Path,
    command: McpCommand,
    url: str,
    action: Action,
    environment: dict[str, str],
) -> tuple[Path, str, Path | None]:
    configured = environment.get("CODEX_HOME")
    root = Path(configured).expanduser() if configured else home / ".codex"
    path = root / "config.toml"
    try:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        parsed = tomllib.loads(text) if text.strip() else {}
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise SetupError(f"{path} is not valid UTF-8 TOML; it was not changed") from exc
    servers = parsed.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise SetupError(f"{path}: mcp_servers is not a table; it was not changed")
    current = servers.get("miho")
    wanted = _json_entry(command, url)
    if current == wanted:
        return path, "current", None
    is_legacy = _legacy_json_entry(current, url)
    if current is not None and not is_legacy:
        raise SetupError(
            f"{path}: existing [mcp_servers.miho] is user-owned; it was not overwritten"
        )
    if action != "apply":
        return path, "drift", None

    block = _codex_block(command, url)
    if is_legacy:
        match = LEGACY_CODEX_BLOCK.search(text)
        if not match:
            raise SetupError(
                f"{path}: legacy miho values use an unknown layout; it was not changed"
            )
        updated = text[: match.start()] + block + "\n" + text[match.end() :]
        state = "migrated legacy entry"
    else:
        updated = text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n"
        state = "registered"
    backup = _backup(path)
    _atomic_text(path, updated)
    return path, state, backup


def _claude_locations(body: dict, path: Path) -> list[tuple[str, dict]]:
    found: list[tuple[str, dict]] = []
    if "mcpServers" in body:
        root = body["mcpServers"]
        if not isinstance(root, dict):
            raise SetupError(
                f"{path}: user mcpServers is not an object; it was not changed"
            )
        if "miho" in root:
            found.append(("user", root))
    if "projects" in body:
        projects = body["projects"]
        if not isinstance(projects, dict):
            raise SetupError(f"{path}: projects is not an object; it was not changed")
        for project, value in projects.items():
            if not isinstance(value, dict):
                raise SetupError(
                    f"{path}: project {project!r} is not an object; it was not changed"
                )
            if "mcpServers" not in value:
                continue
            servers = value["mcpServers"]
            if not isinstance(servers, dict):
                raise SetupError(
                    f"{path}: project {project!r} mcpServers is not an object; "
                    "it was not changed"
                )
            if "miho" in servers:
                found.append((f"project {project}", servers))
    return found


def configure_claude(
    home: Path,
    command: McpCommand,
    url: str,
    action: Action,
    environment: dict[str, str],
    cli: str | None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> tuple[Path, str, Path | None]:
    configured = environment.get("CLAUDE_CONFIG_DIR")
    root = Path(configured).expanduser() if configured else home
    path = root / ".claude.json"
    body = _load_json(path)
    locations = _claude_locations(body, path)
    if len(locations) > 1:
        raise SetupError(f"{path}: multiple miho entries exist; none were changed")
    wanted = _claude_entry(command, url)
    if locations:
        label, servers = locations[0]
        current = servers["miho"]
        if current == wanted:
            return path, f"current ({label})", None
        if not _legacy_claude_entry(current, url):
            raise SetupError(f"{path} ({label}): existing miho entry is user-owned")
        if action != "apply":
            return path, f"drift ({label})", None
        servers["miho"] = wanted
        backup = _write_json(path, body)
        return path, f"migrated legacy entry ({label})", backup

    if not cli:
        return path, "skipped (Claude CLI not installed)", None
    if action != "apply":
        return path, "drift", None
    backup = _backup(path)
    payload = json.dumps(wanted, separators=(",", ":"), ensure_ascii=False)
    cli_environment = dict(environment)
    # Preserve Claude Code's normal user-scope resolution in real use.  The
    # override is only needed when the caller explicitly selected a config
    # directory or supplied a synthetic home (for isolated tests/tooling).
    if configured or home.resolve() != Path.home().resolve():
        cli_environment["CLAUDE_CONFIG_DIR"] = str(root)
    result = runner(
        [cli, "mcp", "add-json", "--scope", "user", "miho", payload],
        capture_output=True,
        text=True,
        check=False,
        env=cli_environment,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise SetupError(f"Claude CLI rejected the miho entry ({message})")
    return path, "registered (user scope)", backup


def _required_path_exists(command: McpCommand) -> bool:
    if command.required_kind == "file":
        return command.required_path.is_file()
    return command.required_path.is_dir()


def run_setup(
    *,
    home: Path,
    command: McpCommand,
    url: str,
    action: Action,
    environment: dict[str, str] | None = None,
    include_claude: bool = True,
    claude_cli: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    emit: Callable[[str], None] = print,
) -> int:
    environment = dict(os.environ) if environment is None else dict(environment)
    if not _required_path_exists(command):
        emit(f"! required {command.mode} runtime is missing: {command.required_path}")
        if command.mode == "desktop":
            emit("  Install and launch Kumiho Desktop, then install/start 9miho from Apps. No config was changed.")
        else:
            emit("  --source-checkout must name an existing development checkout. No config was changed.")
        return 2

    jobs: list[tuple[str, Callable[[], tuple[Path, str, Path | None]]]] = [
        ("Cursor", lambda: configure_cursor(home, command, url, action)),
        ("OpenCode", lambda: configure_opencode(home, command, url, action, environment)),
        ("Codex", lambda: configure_codex(home, command, url, action, environment)),
    ]
    if include_claude:
        jobs.append(
            (
                "Claude Code",
                lambda: configure_claude(
                    home, command, url, action, environment, claude_cli, runner
                ),
            )
        )

    results: list[HostResult] = []
    for host, configure in jobs:
        try:
            path, state, backup = configure()
            normalized = (
                "current"
                if state.startswith("current")
                else "skipped"
                if state.startswith("skipped")
                else "drift"
                if state.startswith("drift")
                else "updated"
            )
            backup_note = f"; backup: {backup}" if backup else ""
            results.append(HostResult(host, normalized, f"{state} ({path}){backup_note}"))
        except Exception as exc:  # one host failure must not block the others
            results.append(HostResult(host, "error", str(exc)))
        result = results[-1]
        marker = {"current": "=", "updated": "+", "drift": "~", "skipped": "-", "error": "!"}[result.state]
        emit(f"{marker} {result.host}: {result.message}")

    if any(result.state == "error" for result in results):
        return 2
    if action == "check" and any(result.state == "drift" for result in results):
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report drift without writing")
    mode.add_argument("--dry-run", action="store_true", help="show planned changes without writing")
    parser.add_argument("--server-url", default=DEFAULT_URL)
    parser.add_argument(
        "--source-checkout",
        type=Path,
        help="developer-only opt-in: run miho-mcp from this source checkout",
    )
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--skip-claude", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    home = args.home.expanduser().resolve()
    command = source_command(args.source_checkout) if args.source_checkout else desktop_command(home)
    if command.mode == "source" and shutil.which("uv") is None:
        print("! --source-checkout requires uv on PATH. No config was changed.", file=sys.stderr)
        return 2
    action: Action = "check" if args.check else "dry-run" if args.dry_run else "apply"
    print(f"9miho skills setup ({command.mode}; {action})\n")
    code = run_setup(
        home=home,
        command=command,
        url=args.server_url,
        action=action,
        include_claude=not args.skip_claude,
        claude_cli=shutil.which("claude"),
    )
    if code == 0 and action == "apply":
        print("\nRestart each agent host, then call list_skills().")
        print("The installed runtime provisions bundled guidance lazily; no checkout or ingest step is required.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
