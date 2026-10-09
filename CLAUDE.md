# CLAUDE.md — Team Credit Burners (JunctionX Lisbon, 24h)

## Priorities (in this order)
1. A working end-to-end demo beats everything else. Get a thin version of the whole pipeline running before polishing any part.
2. Measured results (a small eval set with real numbers) come second.
3. Code quality comes third. Clean only what you're touching.
- If something takes more than 30 minutes, say so and propose a cut. Cutting scope is allowed.
- Never fake results. Cached or mocked demo fallbacks are fine only if listed in `docs/DEMO.md`.

## Token economy (don't waste, but never at the cost of a working demo)
- Search before reading: use Grep/Glob to find what you need, then read only that range. Don't read whole files or list whole directories "for context."
- Don't re-read files you just wrote or edited. Don't re-run a command whose output you already have.
- Long output (logs, tests, builds, large JSON): pipe through `tail`, `head` or `grep`. Never print it in full.
- Don't paste large content into the chat. Point to the file path.
- Replies: short. No restating the task, no recap, no explaining code that wasn't asked about. Give the result and the next step.
- Don't spawn subagents or parallel agents unless asked.
- Read `docs/CONTRACT.md` before researching anything about interfaces.
- If the same attempt fails twice, stop and report instead of trying a third variation.
- Use the smallest model that can do mechanical work (renames, formatting, boilerplate). Keep the strongest for design and hard debugging.
- Cache model and API outputs during development. Never rerun a VLM or LLM over the same inputs just because other code changed.

## Ownership (edit only your own area; propose changes to others)
| Area | Owner |
|---|---|
| `ml/` (models, pipeline, eval) | TBD |
| `api/` (service, storage, deploy) | TBD |
| `ui/` (frontend, demo, pitch visuals) | TBD |
- Shared files (`CLAUDE.md`, lockfiles, config, `docs/CONTRACT.md`): small separate commits, and tell the team in Discord.
- Interfaces between areas live in `docs/CONTRACT.md` (request/response shapes, file formats). If you change it, notify the affected owner first. Use mocks until real pieces connect.
- If a task needs a change in someone else's area, don't make it. Note it in your status file and tell the owner.

## Git (several people pushing at once)
- `main` must always run. Never push something that breaks the demo path.
- Small commits straight to `main`. Before each push: `git pull --rebase`, run `scripts/smoke_test.sh`, then push. Push at least every hour.
- For risky work over 1-2 hours, use a short branch `<name>/<topic>` and merge it back the same day.
- Never `git push --force`, `git reset --hard`, `git checkout .` or `git clean` without asking. A teammate's work may be in the tree.
- Merge conflicts: never resolve by taking one side blindly. If it's someone else's file, ask the owner. Lockfile conflicts: regenerate, don't hand-merge.
- One working tree per agent. For parallel work use `git worktree`. Never run two agents in the same folder.
- Don't commit data, model weights, `.env`, notebook outputs or build artifacts. Commit `.env.example`.
- Commit message: `<area>: <what> — <why>`, one line.

## Tracking work
- Start of every session: `git pull --rebase`, then read `docs/status/*.md`, `docs/CONTRACT.md` and `git log -10`.
- Each person keeps `docs/status/<name>.md` (Doing / Done / Blocked / Decisions). Update it with every push, in 2-3 lines. One file per person avoids merge conflicts.
- `docs/DEMO.md`: the 3-minute script, fallbacks and known failures. `docs/RESULTS.md`: metrics and how they were measured.
- `docs/PLAN.md`: objective, approach, schedule. Read it at the start of every session.
- No changelog, design notes or other docs.

## Testing and verification
- One smoke test (`scripts/smoke_test.sh`) covers the whole demo path, input in and output out. Run it before every push.
- Eval scripts in `ml/` produce the numbers for `docs/RESULTS.md`. Never weaken them to improve the numbers.
- Run the real thing end to end after every merge, not just unit tests. Report what was tested live and what wasn't.
- Check inputs that can ruin a live demo: empty, huge, wrong type, and the same request twice.

## Safety
- Ask before anything destructive or outward-facing: deleting others' files, force pushes, changing shared cloud resources, spending credits in bulk.
- Secrets live only in `.env`. Never in code, commits or chat. Use synthetic data, never real personal data.
- Stop only processes you started, by exact id.
