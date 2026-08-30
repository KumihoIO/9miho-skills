# Install for agents

The user asked you to connect these public trigger skills to their installed
9miho. Stop at the first unsafe condition; do not invent a source-based
fallback.

## Step 1 — verify the Kumiho Desktop runtime

Check the platform path:

- Windows: `~/.kumiho/apps/9miho/bin/9miho.exe`
- macOS/Linux: `~/.kumiho/apps/9miho/bin/9miho`

It must be 9miho 0.16.1 or newer. If it is missing or outdated, ask the user
to install, update, and start 9miho in Kumiho Desktop. The bundled launcher
checks the required setup capability before invoking it, makes no MCP config
change on failure, and exits with status 2. Do not substitute a private
checkout.

## Step 2 — preview the MCP registration

From this skill pack, run `setup.cmd --dry-run` on Windows or
`./setup --dry-run` on macOS/Linux. The intended entry is always the installed
binary with `--mcp-stdio` and
`MIHO_SERVER_URL=http://127.0.0.1:9999`.

The setup may migrate only the exact legacy entry it previously generated.
If it reports invalid configuration or an unrecognized existing `miho` entry,
show the conflict and stop. Do not overwrite it.

## Step 3 — register and reload

Run `setup.cmd` or `./setup`, then restart each affected agent host. Use
`--check` afterward if you need a read-only verification.

## Step 4 — confirm bundled guidance

Call `list_skills()`, then `get_skill(task="image")`. The installed runtime
provisions its version-matched bundled skill pack idempotently on first use;
there is no manual ingest step.

If the API returns 503, Kumiho may still be starting behind Desktop; wait
briefly and retry. If it returns 409, report the named user-managed Kumiho
item and stop. 9miho refuses to overwrite that item by design.

## Do not

- Do not guess node type names. `list_catalog` is the only truth.
- Do not pass `confirm_spend=true` without first surfacing the estimate. The
  user still answers the confirmation card in 9miho.
- Do not cache guidance from `get_skill` for a later installation; it is
  version-matched to the runtime serving it.
- Do not use a source checkout as an installation or recovery workaround.
