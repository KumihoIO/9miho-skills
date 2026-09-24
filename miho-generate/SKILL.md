---
name: miho-generate
description: Compose and run 9miho flows that produce images and video — routing a brief to the right node types, validating before spending, and surfacing the spend confirmation rather than answering it.
tags: [9miho, generate, image, video, movie, edit, subject, flow, spend]
---

# miho-generate

This is a **pointer**, not the guidance.

9miho's real instructions for this task live in the 9miho installation you
are talking to — version-matched to its node catalog, its provider set and
its spend rules. A copy pinned in this repo would be wrong the first time
any of those changed, and wrong guidance about which node costs money is
expensive.

## Do this first

```
get_skill(task="generate")
```

Add `detail=` for anything specific — `get_skill(task="generate",
detail="…")`. The task word is what you are about to do, not a skill name;
free text is accepted. `list_skills()` shows what this installation has.

For multi-cut video with a user-supplied image, ask the installed skill for
reference registration, revision pinning, and the current variant's image
handling before wiring the graph. Bind the image only to shots that actually
depict that subject; count every paid alternative in the estimate, and plan
finished runtime from selected sequential cuts rather than take count. Add
exact informational text during editing when spelling matters.

For a requested video ratio such as 9:16, inspect the chosen catalog variant's
live config schema and set its supported aspect field on every paid video node.
Aspect words in the prompt alone do not configure the output. Check the saved
node controls before the spend request and the rendered clip dimensions before
editing; if the ratio is wrong, correct the config and obtain a new estimate
and human approval for any rerender.

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
