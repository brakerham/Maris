# Agent collaboration rules

All Codex agents working in this repository must first read:

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. `docs/coordination/control.md`
5. The status file for their assigned role under `docs/coordination/agents/`
6. The task brief named in their assignment

Before any external login, service restart, dependency installation, destructive operation, or user-action request, re-read `docs/coordination/control.md`. A newer coordinator directive supersedes an older task plan. If the control file says an action is complete or stopped, do not repeat it; stop safely and report the stale assumption to the coordinator.

## Progress reporting

- Identify your role and assigned task before changing project files.
- Update only your own role file under `docs/coordination/agents/`. The Brainstorm coordinator owns `docs/coordination/overview.md`.
- Record a log entry when you accept a task, reach a material milestone, become blocked, hand work off, or finish.
- Keep a `Current execution snapshot` in your role file with the current step, step start time, last progress time, last heartbeat, next checkpoint, what you are waiting on, and any observable process/session reference.
- Before starting an operation expected to take more than five minutes, record the operation and its next checkpoint. Prefer observable, resumable command sessions for long-running work.
- While execution control is available, refresh the heartbeat at a material output or at least every ten minutes. If a tool or external service prevents updates, record that limitation before starting and update immediately when control returns.
- Never report a percentage unless it comes from measurable units. Describe the completed step and current step instead.
- Use the shared status vocabulary defined in `docs/coordination/README.md`.
- `complete` requires links to actual deliverables and verification evidence. A plan, task dispatch, implementation claim, or passing self-test alone is not project acceptance.
- Record unknown or unverified external task state as `unverified`; do not infer that another agent is active or complete.
- Never put API keys, account tokens, personal financial data, or unredacted private logs in progress documents.

## Coordination boundaries

## Git authority and release workflow

- Only the Brainstorm coordinator may change Git state. All other agents and subagents must not run `git add`, `git commit`, `git restore`, `git reset`, `git checkout`/`switch`, `git merge`/`rebase`, `git push`, create/delete branches or tags, or open/merge pull requests.
- Other agents may use read-only Git commands such as `git status`, `git diff`, `git log`, and object hashing when needed for evidence. They deliver workspace changes, tests, reports, and immutable file-digest snapshots to the coordinator without staging them.
- When the coordinator accepts a task or milestone as `complete`, the coordinator reviews the exact file set and verification evidence, then creates a local Git commit for that accepted unit.
- Before the user declares a major release, commits remain local and must not be pushed to any remote.
- At the user-declared major release, the coordinator may publish the accepted local history to GitHub.
- After that first major release, every change must use a dedicated branch and GitHub pull request. The coordinator alone creates the branch, commits, pushes it, opens the PR, and merges only after required review and acceptance.
- A task reaching `review` is not permission to commit it as accepted work. Defect reports or explicit checkpoints may be committed with wording that clearly states their incomplete status.

- Avoid concurrent edits to the same implementation files. The Executor coordinates implementation ownership and integration.
- The Tester reports reproducible findings independently. Code changes by the Tester require an assigned path or an isolated branch/worktree and must be re-verified.
- Architecture or scope changes return to the Brainstorm coordinator and Technical Adviser before implementation.
- Subagents report through the parent agent that created them; the parent records their outcome in its role file.
- The coordinator may mark activity `stale` or `stalled_suspected` from missing heartbeats, but must inspect available process output and dependencies before declaring a task failed or restarting it.
