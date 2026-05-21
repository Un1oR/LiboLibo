## Codex: nested context workaround

> [!NOTE]
> Temporary workaround for Codex path-aware discovery gaps:
> [nested AGENTS.md](https://github.com/openai/codex/issues/12115),
> [nested local skills](https://github.com/openai/codex/issues/19672).
> Remove this section when both are fixed.

When the task is related to a subdirectory, do not assume this root `AGENTS.md` is the only relevant context.

Check the related subtree and its parents for local `AGENTS.override.md`, `AGENTS.md`, and `.agents/skills`.

Apply the most specific relevant instructions and skills for that subtree. If multiple subtrees are involved, apply each subtree’s context only where it is relevant.