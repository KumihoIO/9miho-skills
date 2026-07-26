# Install for agents

You are an AI coding agent. The user asked you to set up 9miho skills.
Follow this exactly, and stop at the first step that fails rather than
working around it.

## Step 1 — is 9miho running?

```bash
curl -s http://127.0.0.1:8000/api/healthz
```

Expect `{"status":"ok"}`. If not, the user must start it (`uv run
miho-server` in their 9miho checkout). Do not continue without it.

## Step 2 — is Kumiho up?

If `/api/skills` returns **503**, Kumiho CE is not reachable. 9miho stores
every asset there; without it nothing registers and nothing runs. The user
starts it with `kumiho_server` on `127.0.0.1:9190`.

## Step 3 — is miho-mcp configured?

Call `list_skills()`. If the tool does not exist, add miho-mcp to the user's
MCP config (see INSTALL.md) and ask them to restart the session — MCP
servers are loaded at startup.

## Step 4 — is the pack seeded?

If `list_skills()` returns no skills, it will say so and name the command.
Ask the user to run, in their 9miho checkout:

```bash
uv run python scripts/ingest_skills.py
```

## Step 5 — confirm

Call `get_skill(task="image")`. You should get back guidance sections with
content, not names alone. You are set up.

## Do not

- Do not guess node type names. `list_catalog` is the only truth.
- Do not pass `confirm_spend=true` without the user saying yes in words.
- Do not copy guidance out of `get_skill` into your own notes for reuse
  later — it is version-matched to that server and will be wrong elsewhere.
