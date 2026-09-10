# 9miho skills

Agent skills for [9miho](https://github.com/KumihoIO/9miho) — image → asset →
reference → video, with provenance.

Works with Claude Code, Cursor, Codex and any agent that loads Markdown
skills.

## Install

```bash
npx skills add KumihoIO/9miho-skills
```

or, in Claude Code:

```
/plugin marketplace add KumihoIO/9miho-skills
/plugin install miho@miho
```

You also need 9miho 0.16.1 or newer installed and running in Kumiho Desktop,
with its MCP runtime registered in your agent host — see
[INSTALL.md](./INSTALL.md).

For a normal installation, Kumiho Desktop owns both pieces: it installs and
starts 9miho, and this repo's `setup.cmd`/`./setup` registers that installed
runtime with `--mcp-stdio`. No 9miho source checkout or manual skill-ingest
step is required.

## Skills

| Skill | Invoke | For |
|---|---|---|
| [`miho-generate`](./miho-generate) | `/miho:miho-generate` | Compose and run 9miho flows that produce images and video |
| [`miho-library`](./miho-library) | `/miho:miho-library` | Find, inspect and trace assets in the 9miho library |
| [`miho-photoshoot`](./miho-photoshoot) | `/miho:miho-photoshoot` | Brand and product imagery by mode |
| [`miho-storyboard`](./miho-storyboard) | `/miho:miho-storyboard` | Multi-shot sequences that hold together |
| [`miho-storyteller-planning`](./miho-storyteller-planning) | `/miho:miho-storyteller-planning` | Plan and edit a Storyteller series through its Living Canon |
| [`miho-storyteller-production`](./miho-storyteller-production) | `/miho:miho-storyteller-production` | Produce a Storyteller Moment or webtoon panel |
| [`miho-storyteller-text`](./miho-storyteller-text) | `/miho:miho-storyteller-text` | Write web novels, shooting scripts or text storyboards from Storyteller Canon |
| [`miho-subject`](./miho-subject) | `/miho:miho-subject` | Give a character, product or person a reusable visual identity |

## Series production, not just single shots

Three of these drive **Storyteller**, where a series is one *Living Canon*
document — premise, cast with their visual anchors, relationships that change
by episode, and **Moments** small enough to produce. A Moment becomes a
*Direction*: a provider-neutral packet naming intent, performance, blocking,
camera and audio, which is registered as a pinned artefact and is what the
video leg consumes. What comes back is a **Take**, one candidate among
several — generating it does not make it the story's.

Two gates in that loop belong to the person, not to the agent. A tool can
carry the person's elicited response, but cannot supply its own decision: **Canon approval** (a confirmation card bound
to the exact document, which the person answers in 9miho or a supported
client's confirmation form) and the
**spend confirmation** on every paid run. Choosing which Take is the approved
one is the same kind of act, made in 9miho rather than in the transcript. An
agent presents candidates and asks; the human decides.

The text-production skill also prepares source-pinned writing context and
submits externally authored web novels or screenplays to Text Studio for
rendering and editorial review, without starting another model run. It needs
a runtime exposing `prepare_story_text` and `submit_story_text`; installing
these pointers alone does not add server tools. On supporting runtimes, existing
or translated novels can use explicit adaptation mode for editorial review, and
`export_story_text` exports a retained manuscript as DOCX without another model
run. Retrieve the version-matched instructions before using these capabilities.

For episode writing, the workflow continues from the reviewed manuscript to
production Moments and a validated Canon draft, then checks prose and Canon
against each other. This preserves character changes, causal connections and
partial payoffs for the next episode. Existing Moments are reconciled when prose
changes. A copyedit or an explicitly prose-only request can stay within that scope.

## Human approvals in your conversation

On a client that shows MCP elicitation forms to its user, opt in with
`setup.cmd --human-approvals` (Windows) or `./setup --human-approvals`.
Restart the MCP connection. This enables `answer_canon_approval_request` and
`answer_spend_request` on runtimes that provide them. Neither accepts an
approve/deny tool argument: the person answers the form. Unsupported clients
and dismissed forms leave cards pending. The embedded 9miho agent keeps this
transport disabled. Existing custom host configurations are preserved by setup.

Runtimes with fieldless confirmation forms use the human's native Confirm/Submit
as the decision, with no extra approval checkbox. The form shows the held Canon
summary or itemized spend estimate. Decline denies; Cancel leaves it pending.
Button labels belong to the host. Updating these pointers alone cannot change
an older runtime's form; update/reconnect the MCP runtime to load its changes.

## These are pointers

Each skill here carries a trigger and a few lines of conduct. **The guidance
itself is served by your 9miho installation** through the `get_skill` MCP
tool, version-matched to that server's node catalog, provider set and spend
rules.

That split is deliberate. A skill fires on its `description`, which an agent
loads at install time — so the trigger has to be installed. The guidance
does not, and a copy of it pinned here would be wrong the moment a catalog
changed. Wrong guidance about which node costs money is expensive.

Retrieval is keyed on **what you are about to do**, not on a skill name:

```
get_skill(task="video")
get_skill(task="movie", detail="multi-shot, consistent character")
```

`movie` is the case that settles it — no `movie` skill exists, because a
movie is storyboard shape plus image-to-video chaining plus subject
consistency, composed across several skills. A name lookup cannot do that.

## Licence

MIT — see [LICENSE](./LICENSE). Structure and prose patterns adapted from
[higgsfield-ai/skills](https://github.com/higgsfield-ai/skills), also MIT.

Generated from the canonical seed in `KumihoIO/9miho` under `skills/`. Send
guidance changes there, not here.
