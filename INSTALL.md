# Install

The public installation has two pieces: the trigger skills in this repo and
the 9miho MCP runtime installed by Kumiho Desktop.

## 1. Install the trigger skills

```bash
npx skills add KumihoIO/9miho-skills
```

Alternatives: `gh skill install KumihoIO/9miho-skills`, or in Claude Code
`/plugin marketplace add KumihoIO/9miho-skills` followed by
`/plugin install miho@miho`.

## 2. Install and start 9miho in Kumiho Desktop

Kumiho Desktop installs the signed MCP-capable runtime at one of these fixed
locations:

- Windows: `~/.kumiho/apps/9miho/bin/9miho.exe`
- macOS/Linux: `~/.kumiho/apps/9miho/bin/9miho`

Open Kumiho Desktop, install 9miho from Apps, and start it. The setup script
will make no configuration changes if that runtime is missing.

The runtime carries the canonical guidance that matches its own server and
provisions it idempotently when `list_skills()` or `get_skill()` first asks
for it. A normal installation needs neither a 9miho source checkout nor a
separate guidance-seeding command.

## 3. Register the installed MCP runtime

Run the setup bundled with this repo:

```bash
./setup                 # macOS / Linux
setup.cmd               # Windows
```

It writes the same stdio contract for Cursor, OpenCode, Codex, and Claude
Code:

```json
{
  "command": "<HOME>/.kumiho/apps/9miho/bin/9miho",
  "args": ["--mcp-stdio"],
  "env": { "MIHO_SERVER_URL": "http://127.0.0.1:9999" }
}
```

Windows uses `9miho.exe`; setup resolves the real absolute path before
writing it. OpenCode uses the equivalent command-array form.

Preview or audit without changing anything:

```bash
./setup --dry-run
./setup --check
```

`--check` returns 1 when a supported host needs registration or migration and
2 when setup cannot proceed safely. `--dry-run` reports planned changes but
still returns a nonzero status for conflicts or invalid configuration.

### Safe migration boundary

- A missing `miho` entry may be added.
- An exact entry already using the installed runtime is left byte-identical.
- The exact legacy entry written by setup 0.4.2 or earlier is backed up, then
  migrated from `uv run --directory … miho-mcp` to the installed runtime.
- Any other existing `miho` entry is treated as user-owned and left untouched.
- Invalid JSON/TOML is reported and left untouched.

Backups are written beside the original configuration with a
`.9miho-setup*.bak` suffix before a real write.

| Host | Configuration |
| --- | --- |
| Cursor | `~/.cursor/mcp.json`, inside `mcpServers.miho` |
| OpenCode | `$XDG_CONFIG_HOME/opencode/opencode.json` or `~/.config/opencode/opencode.json`, inside `mcp.miho` |
| Codex | `$CODEX_HOME/config.toml` or `~/.codex/config.toml`, as `[mcp_servers.miho]` plus its env table |
| Claude Code | User or project entry in `~/.claude.json`; a new entry is added with `claude mcp add-json --scope user` |

Restart each host after setup so it reloads MCP servers.

## 4. Confirm first retrieval

Ask the agent to call `list_skills()`, then `get_skill(task="image")`. The
first request may provision the bundled pack before returning it. A 409 means
9miho found a user-managed Kumiho item with the same identity and deliberately
refused to overwrite it; review that item instead of forcing a replacement.

## Development source mode (explicit opt-in)

Maintainers working from a real 9miho checkout can opt in explicitly:

```bash
python scripts/setup.py --source-checkout "/path/with spaces/to/9miho"
```

This mode requires `uv` and is for source development only. It is not an
installation or recovery path for Kumiho Desktop users.
