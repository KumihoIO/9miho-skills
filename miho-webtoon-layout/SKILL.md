---
name: miho-webtoon-layout
description: Compose generated, approved 9miho webtoon panels — directly place dialogue balloons, outlined text and lightning tails, adjust asymmetric gutters and diagonal art boundaries, and review the final episode layout through agent tools.
tags: [9miho, webtoon-layout, webtoon, layout, balloon, lettering, whitespace, diagonal, composition]
---

# miho-webtoon-layout

This is a **pointer**, not the guidance.

9miho's real instructions for this task live in the 9miho installation you
are talking to — version-matched to its node catalog, its provider set and
its spend rules. A copy pinned in this repo would be wrong the first time
any of those changed, and wrong guidance about which node costs money is
expensive.

## Do this first

```
get_skill(task="webtoon-layout")
```

Add `detail=` for anything specific — `get_skill(task="webtoon-layout",
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
user must approve the held request before anything runs. When available,
`answer_spend_request(request_id)` carries that same itemized card into this
conversation; otherwise the user answers it in the canvas. Never send an agent's
approve/deny value. Follow the approved request with `get_run`, not a second
`run_graph` call.

**`list_catalog` is the only truth about node types.** Never name a type you
have not listed this session.
