from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_9miho_setup", ROOT / "scripts" / "setup.py")
assert SPEC and SPEC.loader
setup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = setup
SPEC.loader.exec_module(setup)


class SetupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="9miho setup home with spaces ")
        self.home = Path(self.temporary.name) / "home with spaces"
        self.home.mkdir(parents=True)
        self.environment: dict[str, str] = {}

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def install_runtime(self) -> setup.McpCommand:
        command = setup.desktop_command(self.home)
        command.required_path.parent.mkdir(parents=True, exist_ok=True)
        command.required_path.write_bytes(b"signed-runtime-fixture")
        return command

    def test_desktop_contract_uses_exact_installed_binary_and_stdio_flag(self) -> None:
        windows = setup.desktop_command(self.home, "win32")
        unix = setup.desktop_command(self.home, "linux")

        self.assertEqual(
            windows.required_path,
            self.home / ".kumiho" / "apps" / "9miho" / "bin" / "9miho.exe",
        )
        self.assertEqual(
            unix.required_path,
            self.home / ".kumiho" / "apps" / "9miho" / "bin" / "9miho",
        )
        self.assertEqual(windows.command, str(windows.required_path))
        self.assertEqual(unix.command, str(unix.required_path))
        self.assertEqual(windows.args, ("--mcp-stdio",))
        self.assertEqual(unix.args, ("--mcp-stdio",))
        self.assertEqual(
            setup._json_entry(windows, setup.DEFAULT_URL)["env"],
            {"MIHO_SERVER_URL": "http://127.0.0.1:9999"},
        )

    def invoke_setup(self, command: setup.McpCommand, action: setup.Action = "apply", **kwargs) -> int:
        return setup.run_setup(
            home=self.home,
            command=command,
            url=setup.DEFAULT_URL,
            action=action,
            environment=self.environment,
            include_claude=kwargs.pop("include_claude", False),
            emit=kwargs.pop("emit", lambda _message: None),
            **kwargs,
        )

    def test_missing_desktop_runtime_never_mutates_configs(self) -> None:
        path = self.home / ".cursor" / "mcp.json"
        path.parent.mkdir(parents=True)
        original = (ROOT / "tests" / "fixtures" / "home with spaces" / "legacy-cursor.json").read_bytes()
        path.write_bytes(original)

        code = self.invoke_setup(setup.desktop_command(self.home))

        self.assertEqual(code, 2)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((self.home / ".codex" / "config.toml").exists())
        self.assertFalse((self.home / ".config" / "opencode" / "opencode.json").exists())
        self.assertEqual(list(path.parent.glob("*.bak")), [])

    def test_path_with_spaces_legacy_entry_is_backed_up_and_migrated(self) -> None:
        command = self.install_runtime()
        path = self.home / ".cursor" / "mcp.json"
        path.parent.mkdir(parents=True)
        fixture = ROOT / "tests" / "fixtures" / "home with spaces" / "legacy-cursor.json"
        original = fixture.read_bytes()
        path.write_bytes(original)

        self.assertEqual(self.invoke_setup(command), 0)

        entry = json.loads(path.read_text(encoding="utf-8"))["mcpServers"]["miho"]
        self.assertEqual(entry, setup._json_entry(command, setup.DEFAULT_URL))
        self.assertIn("home with spaces", entry["command"])
        backups = list(path.parent.glob("mcp.json.9miho-setup*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def test_second_run_is_byte_identical_and_creates_no_new_backup(self) -> None:
        command = self.install_runtime()
        self.assertEqual(self.invoke_setup(command), 0)
        tracked = [
            self.home / ".cursor" / "mcp.json",
            self.home / ".config" / "opencode" / "opencode.json",
            self.home / ".codex" / "config.toml",
        ]
        before = {path: path.read_bytes() for path in tracked}

        self.assertEqual(self.invoke_setup(command), 0)

        self.assertEqual({path: path.read_bytes() for path in tracked}, before)
        self.assertEqual(list(self.home.rglob("*.bak")), [])

    def test_user_owned_miho_entry_fails_closed(self) -> None:
        command = self.install_runtime()
        path = self.home / ".cursor" / "mcp.json"
        path.parent.mkdir(parents=True)
        custom = b'{"mcpServers":{"miho":{"command":"my-wrapper","args":[]}}}\n'
        path.write_bytes(custom)

        self.assertEqual(self.invoke_setup(command), 2)
        self.assertEqual(path.read_bytes(), custom)
        self.assertEqual(list(path.parent.glob("*.bak")), [])

    def test_invalid_json_fails_closed(self) -> None:
        command = self.install_runtime()
        path = self.home / ".cursor" / "mcp.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not-json", encoding="utf-8")

        self.assertEqual(self.invoke_setup(command), 2)
        self.assertEqual(path.read_text(encoding="utf-8"), "{not-json")
        self.assertEqual(list(path.parent.glob("*.bak")), [])

    def test_null_json_container_and_entry_fail_closed(self) -> None:
        command = self.install_runtime()
        cases = (
            b'{"mcpServers":null}\n',
            b'{"mcpServers":{"miho":null}}\n',
        )
        for index, original in enumerate(cases):
            with self.subTest(index=index):
                path = self.home / f"case-{index}" / "mcp.json"
                path.parent.mkdir(parents=True)
                path.write_bytes(original)

                state, backup = None, None
                with self.assertRaises(setup.SetupError):
                    state, backup = setup._replace_json_entry(
                        path,
                        "mcpServers",
                        setup._json_entry(command, setup.DEFAULT_URL),
                        lambda entry: setup._legacy_json_entry(
                            entry, setup.DEFAULT_URL
                        ),
                        "apply",
                    )

                self.assertIsNone(state)
                self.assertIsNone(backup)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(list(path.parent.glob("*.bak")), [])

    def test_check_and_dry_run_do_not_write(self) -> None:
        command = self.install_runtime()
        initial = sorted(path.relative_to(self.home) for path in self.home.rglob("*") if path.is_file())

        self.assertEqual(self.invoke_setup(command, "check"), 1)
        self.assertEqual(self.invoke_setup(command, "dry-run"), 0)

        after = sorted(path.relative_to(self.home) for path in self.home.rglob("*") if path.is_file())
        self.assertEqual(after, initial)

    def test_codex_legacy_block_is_backed_up_and_replaced(self) -> None:
        command = self.install_runtime()
        path = self.home / ".codex" / "config.toml"
        path.parent.mkdir(parents=True)
        original = (
            '[mcp_servers.miho]\n'
            'command = "uv"\n'
            'args = ["run", "--directory", "C:\\\\Source Trees\\\\Private 9miho", "miho-mcp"]\n\n'
            '[mcp_servers.miho.env]\n'
            'MIHO_SERVER_URL = "http://127.0.0.1:9999"\n'
        )
        path.write_text(original, encoding="utf-8")

        self.assertEqual(self.invoke_setup(command), 0)

        updated = path.read_text(encoding="utf-8")
        self.assertIn(setup.MANAGED_BEGIN, updated)
        self.assertIn(str(command.required_path).replace("\\", "\\\\"), updated)
        self.assertNotIn('command = "uv"', updated)
        backups = list(path.parent.glob("config.toml.9miho-setup*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), original)

    def test_codex_legacy_custom_url_is_not_silently_replaced(self) -> None:
        command = self.install_runtime()
        path = self.home / ".codex" / "config.toml"
        path.parent.mkdir(parents=True)
        custom_url = "http://127.0.0.1:17777"
        original = (
            '[mcp_servers.miho]\n'
            'command = "uv"\n'
            'args = ["run", "--directory", "C:\\\\Private 9miho", "miho-mcp"]\n\n'
            '[mcp_servers.miho.env]\n'
            f'MIHO_SERVER_URL = "{custom_url}"\n'
        )
        path.write_text(original, encoding="utf-8")

        self.assertEqual(self.invoke_setup(command), 2)

        self.assertEqual(path.read_text(encoding="utf-8"), original)
        self.assertEqual(list(path.parent.glob("*.bak")), [])

    def test_codex_legacy_custom_url_migrates_only_when_explicit(self) -> None:
        command = self.install_runtime()
        path = self.home / ".codex" / "config.toml"
        path.parent.mkdir(parents=True)
        custom_url = "http://127.0.0.1:17777"
        path.write_text(
            '[mcp_servers.miho]\n'
            'command = "uv"\n'
            'args = ["run", "--directory", "C:\\\\Private 9miho", "miho-mcp"]\n\n'
            '[mcp_servers.miho.env]\n'
            f'MIHO_SERVER_URL = "{custom_url}"\n',
            encoding="utf-8",
        )

        code = setup.run_setup(
            home=self.home,
            command=command,
            url=custom_url,
            action="apply",
            environment=self.environment,
            include_claude=False,
            emit=lambda _message: None,
        )

        self.assertEqual(code, 0)
        self.assertIn(
            f'MIHO_SERVER_URL = "{custom_url}"',
            path.read_text(encoding="utf-8"),
        )

    def test_claude_cli_failure_does_not_block_other_hosts(self) -> None:
        command = self.install_runtime()

        def fail(*_args, **_kwargs) -> subprocess.CompletedProcess:
            return subprocess.CompletedProcess([], 9, stdout="", stderr="fixture failure")

        code = self.invoke_setup(
            command,
            include_claude=True,
            claude_cli="claude-fixture",
            runner=fail,
        )

        self.assertEqual(code, 2)
        cursor = json.loads((self.home / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(cursor["mcpServers"]["miho"], setup._json_entry(command, setup.DEFAULT_URL))

    def test_invalid_claude_container_fails_closed_without_calling_cli(self) -> None:
        command = self.install_runtime()
        path = self.home / ".claude.json"
        original = b'{"projects":{"C:/work":{"mcpServers":[]}}}\n'
        path.write_bytes(original)
        calls: list[object] = []

        def runner(*args, **_kwargs) -> subprocess.CompletedProcess:
            calls.append(args)
            return subprocess.CompletedProcess([], 0, stdout="", stderr="")

        code = self.invoke_setup(
            command,
            include_claude=True,
            claude_cli="claude-fixture",
            runner=runner,
        )

        self.assertEqual(code, 2)
        self.assertEqual(calls, [])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(list(path.parent.glob(".claude.json.9miho-setup*.bak")), [])


class PublicTreeContractTest(unittest.TestCase):
    def test_posix_setup_launcher_is_executable_in_git(self) -> None:
        tracked = subprocess.run(
            ["git", "ls-files", "--stage", "--", "setup"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertTrue(
            tracked.stdout.startswith("100755 "),
            "the documented ./setup launcher must be executable in a clean clone",
        )

    def test_all_public_version_stamps_match(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        stamps = [
            json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))["plugins"][0]["version"],
            json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"],
            json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"],
            json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"],
        ]
        self.assertEqual(version, "0.4.4")
        self.assertEqual(stamps, [version] * len(stamps))

    def test_launchers_use_signed_runtime_without_system_python(self) -> None:
        unix = (ROOT / "setup").read_text(encoding="utf-8")
        windows = (ROOT / "setup.cmd").read_text(encoding="utf-8")
        self.assertIn("--setup-agent-hosts", unix)
        self.assertIn("--setup-agent-hosts", windows)
        self.assertNotIn("python", unix.lower())
        self.assertNotIn("python", windows.lower())

    def test_public_storyteller_trigger_includes_webtoon_production(self) -> None:
        body = (ROOT / "miho-storyteller-production" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Storyteller Moment or webtoon panel", body)
        self.assertIn("webtoon", body.split("---", 2)[1])

    def test_public_user_guidance_has_no_private_default_or_ingest_step(self) -> None:
        paths = [ROOT / "README.md", ROOT / "INSTALL_FOR_AGENTS.md"]
        paths.extend(ROOT.glob("miho-*/SKILL.md"))
        forbidden = ("ingest_skills.py", "<path-to-9miho>", '"command": "uv"')
        for path in paths:
            body = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, body, f"{path}: {token}")


if __name__ == "__main__":
    unittest.main()
