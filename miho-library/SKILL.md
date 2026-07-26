---
name: miho-library
description: Find, inspect and trace assets in the 9miho library — search before generating, pin the right revision, and answer where any output came from via its provenance edges.
tags: [9miho, library, assets, search, lineage, provenance, revisions]
allowed-tools: mcp__miho__get_skill, mcp__miho__list_skills
---

# miho-library

This is a **pointer**, not the guidance.

9miho's real instructions for this task live in the 9miho installation you
are talking to — version-matched to its node catalog, its provider set and
its spend rules. A copy pinned in this repo would be wrong the first time
any of those changed, and wrong guidance about which node costs money is
expensive.

## Do this first

```
get_skill(task="library")
```

Add `detail=` for anything specific — `get_skill(task="library",
detail="…")`. The task word is what you are about to do, not a skill name;
free text is accepted. `list_skills()` shows what this installation has.

## If that tool is not there

miho-mcp is not configured. Add it to your MCP config:

```json
{"mcpServers": {"miho": {
  "command": "uv",
  "args": ["run", "--directory", "<path-to-9miho>", "miho-mcp"],
  "env": {"MIHO_SERVER_URL": "http://127.0.0.1:8000"}
}}}
```

Then confirm the 9miho server answers on `/api/healthz`, and that its Kumiho
is up — 9miho stores every asset there, so without it nothing runs.

## Two rules that hold even before you fetch anything

**Never confirm spend on the user's behalf.** `run_graph` refuses a graph
containing billable nodes unless `confirm_spend=true`, and names them. That
refusal is a question *for the user*.

**`list_catalog` is the only truth about node types.** Never name a type you
have not listed this session.
