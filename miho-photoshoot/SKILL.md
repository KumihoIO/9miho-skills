---
name: miho-photoshoot
description: Brand and product imagery by mode — studio, lifestyle, hero banner, pin, ad pack, try-on — each a small flow over the same nodes rather than a different model.
tags: [9miho, photoshoot, product, brand, image, modes, marketing]
allowed-tools: mcp__miho__get_skill, mcp__miho__list_skills
---

# miho-photoshoot

This is a **pointer**, not the guidance.

9miho's real instructions for this task live in the 9miho installation you
are talking to — version-matched to its node catalog, its provider set and
its spend rules. A copy pinned in this repo would be wrong the first time
any of those changed, and wrong guidance about which node costs money is
expensive.

## Do this first

```
get_skill(task="photoshoot")
```

Add `detail=` for anything specific — `get_skill(task="photoshoot",
detail="…")`. The task word is what you are about to do, not a skill name;
free text is accepted. `list_skills()` shows what this installation has.

## If that tool is not there

miho-mcp is not configured. Install and start 9miho from Kumiho Desktop,
then run the setup bundled with this skill pack (`setup.cmd` on Windows or
`./setup` on macOS/Linux). It registers the installed runtime directly:

- Windows: `~/.kumiho/apps/9miho/bin/9miho.exe --mcp-stdio`
- macOS/Linux: `~/.kumiho/apps/9miho/bin/9miho --mcp-stdio`
- Environment: `MIHO_SERVER_URL=http://127.0.0.1:9999`

If the runtime is missing, install or launch it from Kumiho Desktop and retry.
Do not substitute a private source checkout. The installed runtime provisions
its bundled guidance when `list_skills()` or `get_skill()` first requests it.

## Two rules that hold even before you fetch anything

**You cannot confirm spend. Only the user can.** `run_graph` refuses a graph
containing billable nodes unless `confirm_spend=true`, and the refusal carries
an itemized estimate. That flag is a fail-fast, not an authorization: the
server shows the user a confirm card in their canvas and runs nothing until
they accept it there.

**`list_catalog` is the only truth about node types.** Never name a type you
have not listed this session.
