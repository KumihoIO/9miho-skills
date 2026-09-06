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
| [`miho-subject`](./miho-subject) | `/miho:miho-subject` | Give a character, product or person a reusable visual identity |

## Series production, not just single shots

Two of these drive **Storyteller**, where a series is one *Living Canon*
document — premise, cast with their visual anchors, relationships that change
by episode, and **Moments** small enough to produce. A Moment becomes a
*Direction*: a provider-neutral packet naming intent, performance, blocking,
camera and audio, which is registered as a pinned artefact and is what the
video leg consumes. What comes back is a **Take**, one candidate among
several — generating it does not make it the story's.

Two gates in that loop belong to the person, not to the agent, and neither
can be answered by a tool call: **Canon approval** (a confirmation card bound
to the exact document, which the agent opens and cannot answer) and the
**spend confirmation** on every paid run. Choosing which Take is the approved
one is the same kind of act, made in 9miho rather than in the transcript. An
agent presents candidates and asks; the human decides.

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
