# Install

Two halves: the skills (this repo) and the tool surface (`miho-mcp`, which
serves the actual guidance).

## 1. Skills

```bash
npx skills add KumihoIO/9miho-skills
```

Alternatives: `gh skill install KumihoIO/9miho-skills`, or in Claude Code
`/plugin marketplace add KumihoIO/9miho-skills` then
`/plugin install miho@miho`.

## 2. A running 9miho

Follow the 9miho README. You need the server answering on `/api/healthz`,
and Kumiho reachable — 9miho stores every asset there, so without Kumiho it
has no database and nothing runs.

## 3. miho-mcp in your MCP config

Fastest path ? run the bundled setup from this repo; it detects installed
hosts and registers the same entry idempotently:

```bash
./setup            # macOS / Linux
setup.cmd          # Windows
```

Prefer by hand? The server entry is the same everywhere; only the file it
lives in differs.

```json
{
  "mcpServers": {
    "miho": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/9miho", "miho-mcp"],
      "env": { "MIHO_SERVER_URL": "http://127.0.0.1:9999" }
    }
  }
}
```

| Host | Where it goes |
| --- | --- |
| Cursor | `~/.cursor/mcp.json`, inside `"mcpServers"` |
| OpenCode | `~/.config/opencode/opencode.json`, as `"mcp": {"miho": {"type": "local", "command": ["uv", "run", "--directory", "/path/to/9miho", "miho-mcp"], "environment": {"MIHO_SERVER_URL": "http://127.0.0.1:9999"}, "enabled": true}}` |
| Codex | `~/.codex/config.toml`: `[mcp_servers.miho]` with `command = "uv"`, `args = ["run", "--directory", "/path/to/9miho", "miho-mcp"]`, and `[mcp_servers.miho.env]` carrying `MIHO_SERVER_URL` |
| Claude Code | `claude mcp add -e MIHO_SERVER_URL=http://127.0.0.1:9999 miho -- uv run --directory /path/to/9miho miho-mcp` |

After editing a config, restart that host so the server list reloads.

## 4. Seed the guidance (once per installation)

In the 9miho checkout:

```bash
uv run python scripts/ingest_skills.py
```

This writes the skill pack into that installation's Kumiho, where
`get_skill` reads it. Re-running is idempotent — it creates a new revision
rather than duplicating.

## Check it worked

Ask your agent to call `list_skills()`. You should get seven skills and a set
of task words. If the tool is missing, step 3 did not take. If it returns an
empty pack with a hint about `ingest_skills.py`, step 4 did not.
