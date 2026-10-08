# Handoff

Use `orca-cli` for full ownership transfer. Matt skills guide the receiving agent's work; Matt's `handoff` skill writes a session note and does not transfer ownership. See [ADR 0003](../adr/0003-orca-matt-handoff.md) and the [handoff research](https://github.com/DavillyDevTeam/davilly-starter/blob/research/orca-matt-handoff/docs/research/orca-matt-handoff.md).

## Full handoff

1. Load `orca-cli` and resolve its executable for this session. Honor `ORCA_CLI_COMMAND`, then `ORCA_DEV_REPO_ROOT` (`orca-dev`). On Linux outside an Orca-managed terminal use `orca-ide`; inside Orca use `orca`. Below, `ORCA` is a placeholder for that executable, not a literal command. Load its version-matched guide with `ORCA skills get orca-cli` and check current command help.
2. Prepare a worker prompt naming the ticket, map, skills, scope, and completion criteria. `--issue` links the issue to the worktree; it does not inject the issue body. Example:

   ```text
   Load the wayfinder skill. You own GitHub issue <N> (already claimed).
   Read gh issue view <N> --comments and the parent map's Notes.
   Load skills named in Notes, including grilling or domain-modeling when relevant.
   Execute only this ticket. Validate the change and publish a branch and PR.
   Comment the result, close the ticket, and append a gist plus link to the map's
   Decisions so far. Stop after this ticket.
   ```

3. Transfer with an independent top-level worktree:

   ```text
   ORCA worktree create --name "<ticket title>" --no-parent --agent grok --issue <N> --prompt "<worker prompt>" --json
   ```

   Omit `--issue` for work without a GitHub ticket. Omit `--base-branch` to use the repository default base. Davilly's documented default provider is `grok`; `--agent codex` or `--agent claude` is an explicit host swap. This machine's launcher may use Codex.
4. Done means the receipt reports `accepted: true` and the new worktree id and agent handle have been reported. Stop after acceptance; the receiving agent owns completion. If acceptance is missing or false, report the failed transfer and retain ownership. Use supervised `orchestration` only when coordination is requested; subagents and background Claude sessions are not the default ownership transfer.

## Host install

Install skills globally on an agent host. Substitute the resolved executable for `ORCA`:

```text
ORCA skills install --skill orca-cli --skill orchestration --agent grok,universal
npx skills add mattpocock/skills --global --agent grok -y
```

For a Codex host, substitute `codex` for `grok` in both installers; retain `universal` for the Orca bundle. Orca and Matt are separate packs. `orchestration` supports requested supervision; full transfer uses `orca-cli`.

Refresh with `ORCA skills update --skill orca-cli --skill orchestration` and `npx skills update -g`. Host skill lockfiles track installed revisions. Use global scope; project-local installs are experiments, not repository content. A missing skill requires host setup before the workflow that needs it can run. Re-running `setup-matt-pocock-skills` is for changing repository configuration, not updating skills.

`wayfinder` and `triage` are user-invoked skills: name them explicitly in requests or dispatcher prompts. `grilling` and `domain-modeling` can load from their task triggers.

## Frontier automation

Host automation implementation belongs to [Task: Wayfinder frontier Orca automation](https://github.com/DavillyDevTeam/davilly-starter/issues/25). This document describes the protocol; it creates no runtime automation.

Use an existing dispatcher workspace with a fresh session and provider `grok`. Create disabled for review and manual testing. The automation is a dispatcher; its worker receives the linked ticket through `worktree create --issue`, since `automations create` has no `--issue`.

Dispatcher prompt:

```text
Load the wayfinder skill. Read the wayfinder:map issue and its Notes, plus
 docs/agents/issue-tracker.md and docs/agents/handoff.md.
List the map's sub-issues via the paginated GitHub sub_issues endpoint in map order.
Take the first open child with ready-for-agent, no assignees, and
issue_dependencies_summary.blocked_by == 0. If none, stop.
Re-read the candidate before claiming; stop if its eligibility changed.
Claim first with gh issue edit <N> --add-assignee @me, then verify the assignment.
Full-handoff that one ticket using the Full handoff recipe and worker prompt above.
Report the worktree id, handle, and accepted receipt, then stop.
```

A bounded precheck exits zero only when a takeable child exists, otherwise the run is skipped. Use `blocked_by` (open blockers), not `total_blocked_by`. Preserve sub-issue map order across pagination; issue-list recency is not map order. Select only `ready-for-agent` work. The dispatcher neither implements nor resolves tickets. GitHub assignment is not an atomic lock: serialize dispatcher runs and stop if another claimant is observed.

## Git vs host vs Template

Repository content is thin `AGENTS.md` pointers, disclosed `docs/agents/` recipes, `CONTEXT.md`, and repo-specific ADRs. Skills, global skill lockfiles, GitHub authentication, Orca worktree ids, and runtime automations belong on the host. Keep skill directories and installer lockfiles out of git.

[Task: Template Orca and Matt agent rails](https://github.com/DavillyDevTeam/davilly-starter/issues/24) owns the parameterized Template copy. Generated apps use their own remote, map, domain language, and ADRs. Starter research and ADRs are not copied as Generated-app decisions.

Tracker labels are GitHub state. On a new repository, create the canonical roles from `triage-labels.md` and the `wayfinder:<type>` labels needed by its map with `gh label create <label> --color <hex> --description "<meaning>"`; first check existing labels with `gh label list`. This Starter already has its tracker configuration.

Orca is optional for Consumers. Generation, boot, and validation do not install skills or invoke Orca. The Generated-app task surface is Nx: `pnpm nx run-many -t lint,typecheck,test,build` (ADR 0004), with uv for Python and pnpm for TypeScript. This Starter is a uv project, not an Nx workspace.
