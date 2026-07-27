---
name: miho-storyboard
description: Multi-shot sequences that hold together — plan the shots, keep the subject pinned across all of them, animate selectively, and assemble with lineage intact.
tags: [9miho, storyboard, sequence, movie, shots, video, continuity]
allowed-tools: mcp__miho__get_skill, mcp__miho__list_skills
---

# miho-storyboard

This is a **pointer**, not the guidance.

9miho's real instructions for this task live in the 9miho installation you
are talking to — version-matched to its node catalog, its provider set and
its spend rules. A copy pinned in this repo would be wrong the first time
any of those changed, and wrong guidance about which node costs money is
expensive.

## Do this first

```
get_skill(task="storyboard")
```

Add `detail=` for anything specific — `get_skill(task="storyboard",
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

**You cannot confirm spend. Only the user can.** `run_graph` refuses a graph
containing billable nodes unless `confirm_spend=true`, and the refusal carries
an itemized estimate. That flag is a fail-fast, not an authorization: the
server shows the user a confirm card in their canvas and runs nothing until
they accept it there.

**`list_catalog` is the only truth about node types.** Never name a type you
have not listed this session.
