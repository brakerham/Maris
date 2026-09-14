# Agent collaboration rules

All Codex agents working in this repository must first read:

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. The status file for their assigned role under `docs/coordination/agents/`
5. The task brief named in their assignment

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

- Avoid concurrent edits to the same implementation files. The Executor coordinates implementation ownership and integration.
- The Tester reports reproducible findings independently. Code changes by the Tester require an assigned path or an isolated branch/worktree and must be re-verified.
- Architecture or scope changes return to the Brainstorm coordinator and Technical Adviser before implementation.
- Subagents report through the parent agent that created them; the parent records their outcome in its role file.
- The coordinator may mark activity `stale` or `stalled_suspected` from missing heartbeats, but must inspect available process output and dependencies before declaring a task failed or restarting it.
