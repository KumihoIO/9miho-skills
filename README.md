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

You also need a running 9miho with `miho-mcp` in your MCP config — see
[INSTALL.md](./INSTALL.md).

## Skills

| Skill | Invoke |
|---|---|
| [`miho-generate`](./miho-generate) | `/miho:miho-generate` |
| [`miho-library`](./miho-library) | `/miho:miho-library` |
| [`miho-photoshoot`](./miho-photoshoot) | `/miho:miho-photoshoot` |
| [`miho-storyboard`](./miho-storyboard) | `/miho:miho-storyboard` |
| [`miho-subject`](./miho-subject) | `/miho:miho-subject` |

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
