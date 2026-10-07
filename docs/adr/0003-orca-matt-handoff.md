# Orca is the handoff runtime; Matt skills are what the agent runs

When Orca is installed, a full handoff is an Orca worktree plus an agent prompt (`orca-cli`: `worktree create --no-parent --agent <id> --prompt`, GitHub `--issue` when the work is a ticket). The original agent stops after the send is accepted. Matt Pocock skills (wayfinder, grilling, domain-modeling, triage, and the rest of `docs/agents/`) are the planning and execution skills the receiving agent loads. `spawn_subagent` and `claude --bg` are not the default ownership transfer.

Orca is optional for Consumers: `just ci` and the Generated app boot without it. Agent rails still ship `AGENTS.md` + `docs/agents/` so a host with Orca and the skills pack can pick up the same workflow. Default Davilly automation provider is `grok`; Claude/Codex are documented swaps.
