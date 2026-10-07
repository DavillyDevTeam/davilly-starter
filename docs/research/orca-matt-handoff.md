# Research: Orca handoff with Matt skills

How this Starter and every Generated app should integrate **Orca full handoff** with **Matt Pocock skills** (wayfinder, grilling, domain-modeling, triage, `docs/agents/`).

This note does not edit `AGENTS.md`, does not vendor skills, and does not create an Orca automation. Implementation is [Task: Starter Orca and Matt agent rails](https://github.com/DavillyDevTeam/davilly-starter/issues/23), [Task: Template Orca and Matt agent rails](https://github.com/DavillyDevTeam/davilly-starter/issues/24), and [Task: Wayfinder frontier Orca automation](https://github.com/DavillyDevTeam/davilly-starter/issues/25). ADR: [`docs/adr/0003-orca-matt-handoff.md`](../adr/0003-orca-matt-handoff.md).

On Linux outside an Orca-managed terminal the executable is `orca-ide` (never bare `orca`, that is GNOME Orca). Inside Orca, use `orca`. The bundled skill uses `ORCA` as a placeholder for whichever executable you resolved. ([orca-cli discovery stub](https://github.com/stablyai/orca); `orca-ide skills get orca-cli`)

## Answer (gist)

1. Keep `AGENTS.md` as thin always-loaded **pointers**. Put the recipes in a new disclosed `docs/agents/handoff.md`. Do not inline the Orca CLI surface. Name `wayfinder` (and `triage`) in `AGENTS.md` or in every automation prompt: those skills are user-invoked (`disable-model-invocation: true`) and will not self-load.
2. Install skills **on the host**, not in git. Two packs, two commands: `orca-ide skills install --skill orca-cli --skill orchestration --agent grok,universal` (Orca bundled, global by default) and `npx skills add mattpocock/skills --global --agent grok -y` (Matt pack; `npx skills` defaults to **project** unless `--global`). `--local` is for experiments. Do not vendor. `orca skills share` is optional and Orca-only.
3. Frontier automation is a **dispatcher**, not the worker. `orca automations create` has no `--issue`. Precheck the map's sub-issues in map order (`ready-for-agent`, unassigned, `issue_dependencies_summary.blocked_by == 0`); claim with `gh issue edit N --add-assignee @me`; full-handoff with `worktree create --name … --no-parent --agent grok --issue N --prompt … --json`; stop after `accepted: true`. Create the automation `--disabled` and fire it with `automations run`. Provider `grok`. Use `--workspace` for the dispatcher and `--fresh-session`.
4. The Copier Template copies **per-repo config** (`AGENTS.md`, `docs/agents/*`, glossary, `docs/adr/`). It does not copy skill trees, lockfiles, or live automations. `just ci` and boot never call Orca.

## 1. `AGENTS.md` pointers vs disclosed `docs/agents/handoff.md`

### What setup already writes

`setup-matt-pocock-skills` scaffolds per-repo config the other engineering skills read. It edits whichever of `CLAUDE.md` / `AGENTS.md` already exists (this repo: `AGENTS.md`) and writes `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`. The `## Agent skills` block is three one-line summaries, each ending `See docs/agents/<file>.md`. Re-run only to switch trackers or start over; skill updates do not overwrite these files. (`setup-matt-pocock-skills` SKILL.md, steps 4–5)

That is already the writing-for-agents pattern: an `AGENTS.md` line is a **context pointer** (always-loaded **context load**); the body lives behind the pointer as **disclosed reference**. “Material reached only through a pointer escapes context load at the price of the pointer's own line.” Inline only if a sharpened pointer fails. (`writing-for-agents` SKILL.md, “Context pointers”, “The two loads”, “Information hierarchy”)

Current `AGENTS.md` matches that seed. It does not mention handoff, Orca, or wayfinder.

### Disclose the recipes

Handoff, skill install, and frontier automation are **not** produced by `setup-matt-pocock-skills`. They are Davilly-specific and branchy (live handoff vs scheduled pickup vs host install vs Template copy). Branching is the disclosure test: keep the always-loaded line short; put steps in `docs/agents/handoff.md`. (`writing-for-agents` SKILL.md, “Progressive disclosure”)

Do **not** paste `worktree create` flags, `automations create` recipes, or `npx skills` command lines into `AGENTS.md`. Those are environment lookups (`--help`, the skill guide). A document that restates them is a **cache**. (`writing-for-agents` SKILL.md, “Pruning”)

Recommended `AGENTS.md` addition (for [Task: Starter Orca and Matt agent rails](https://github.com/DavillyDevTeam/davilly-starter/issues/23); do not apply here):

```markdown
### Handoff

Full Orca ownership transfer (`worktree create --no-parent --agent --prompt`; `--issue` for a GitHub ticket), host skill install, and overnight frontier pickup. See `docs/agents/handoff.md`.

### Wayfinder

User-invoked map of decision tickets. Load the `wayfinder` skill; tracker operations live in `docs/agents/issue-tracker.md`.
```

Leading word **Handoff** front-loads the trigger. The three branches the disclosed file handles (transfer, install, overnight pickup) are named once. **Wayfinder** is a second pointer because that skill will not fire from its description. Collapse “handoff / handover / give this to another agent” to the one leading word; the orca-cli skill already lists those synonyms. (`writing-for-agents` SKILL.md, “Leading words”; orca-cli guide, “Full Handoffs”)

Do not add a fourth always-loaded essay on grilling or domain-modeling: those skills are **model-invoked** (they have a `description` and do not set `disable-model-invocation`). `triage`, `wayfinder`, `to-spec`, `to-tickets`, `implement-spec`, `setup-matt-pocock-skills`, and Matt `handoff` **are** user-invoked. Overnight prompts must name the user-invoked ones they need. (`wayfinder` / `triage` / `to-spec` SKILL.md frontmatter)

Matt **`handoff`** writes a compact document under `$TMPDIR` for a later session. It is not ownership transfer. ADR 0003 already forbids `spawn_subagent` / `claude --bg` as the default transfer. (`handoff` SKILL.md; `docs/adr/0003-orca-matt-handoff.md`)

### What `docs/agents/handoff.md` should hold

Co-locate (one file, four headings):

1. **Full handoff** — the `worktree create --no-parent --agent <id> --prompt --json` recipe; GitHub `--issue`; stop after `accepted: true`; Linux `orca-ide`; known agent ids include `grok`.
2. **Host install** — the two commands in §2.
3. **Frontier automation** — the dispatcher shape in §3, including precheck, claim, prompt text.
4. **Git vs host vs Template** — the copy set in §4.

Completion criterion for a full handoff, from the orca-cli guide: the new worktree id and agent handle have been reported **and** the prompt's send receipt reported `accepted: true`. Do not wait for the receiving agent to finish. Do not use `orca orchestration task-create`, `dispatch --inject`, or `check --wait` for full handoffs. (`orca-ide skills get orca-cli`, “Full Handoffs”)

`--issue` is a **linked GitHub issue number** on the worktree (selector `issue:<number>`; also `worktree set --issue`). It does not inject the ticket body. The `--prompt` still has to tell the receiving agent to `gh issue view N --comments` and load `wayfinder`. (`orca-ide worktree create --help`; `orca-ide worktree set --help`; orca-cli guide, Selectors)

## 2. Skill install: git vs host

### Two packs

| Pack | Installer | Source | Default scope |
| --- | --- | --- | --- |
| Orca bundled (`orca-cli`, `orchestration`, …) | `orca-ide skills install` | `https://github.com/stablyai/orca` via `npx skills add` | **Global** (`--global`) |
| Matt Pocock (`wayfinder`, `grilling`, `domain-modeling`, `triage`, `setup-matt-pocock-skills`, …) | `npx skills add mattpocock/skills` | `https://github.com/mattpocock/skills` | **Project** unless `-g` / `--global` |

`orca skills install` “Reads the bundled skill registry locally… Resolves to the same `npx skills add <repo> --skill <name> ...` command used by Orca Settings, plus the non-interactive flags an unattended host needs (`npx --yes` and `-y`)… Installs globally (all projects, adds --global) by default. Use `--local` to install into the current project instead.” Omit `--skill` and `--all` to list names. (`orca-ide skills install --help`)

Dry-run on this host (`orca-ide skills install --skill orca-cli --agent universal --dry-run --json`):

```text
npx --yes skills add https://github.com/stablyai/orca --skill orca-cli --global --agent universal -y
```

`--local` drops `--global`. Bare `--local` without `--agent` targeted every detected agent (`antigravity`, `claude-code`, `codex`, `gemini-cli`, `github-copilot`, `grok`, `hermes-agent`, `opencode`, `universal`) — the help text's “litters a host with config directories” warning. Pass `--agent grok,universal` (Davilly default provider + the shared `.agents/skills` directory). `--agent` is required when Orca detects no agent. (`orca-ide skills install --help`; dry-run JSON)

Available bundled names (`orca-ide skills install --json`): `computer-use`, `linear-tickets`, `orca-cli`, `orca-emulator`, `orca-emulator-android`, `orca-linear`, `orca-per-workspace-env`, `orchestration`. **Matt skills are not in this list.** Do not `--all`: emulator/Linear/computer-use are unrelated to this Starter.

Recommended host commands:

```bash
orca-ide skills install --skill orca-cli --skill orchestration --agent grok,universal
npx skills add mattpocock/skills --global --agent grok -y
```

Refresh: `orca-ide skills update --skill orca-cli --skill orchestration` and `npx skills update -g`. (`orca-ide skills update --help`; `npx skills --help`)

`orchestration` is the supervised DAG skill. Full handoff uses `orca-cli` only; still install it so a human who asks to coordinate can. (orca-cli guide: “For structured coordination, invoke the `orchestration` skill”)

### Share bundle is not the Consumer path

`orca skills share --skill <selector> … --bundle-name <name>` publishes installed skills behind one **unlisted** link. It needs the default-off permission Settings → Share Skills; there is no CLI way to grant it. `--all` and arbitrary paths are unsupported. Denied → `agent_skill_sharing_disabled`, do not retry. Anyone with the link can install. (`orca-ide skills share --help`; `orca-ide skills get orca-cli --reference publishing`)

skills.sh packs (`npx skills add https://skills.sh/p/<pack-id>`) are a second, Vercel-signed unlisted collection. (skills.sh Packs docs)

Neither is required. Both packs already live on public GitHub. A share/pack is an optional convenience for Orca hosts; Consumers without Orca cannot use `orca skills share`. ADR 0003: Orca is optional.

### What belongs in git vs on the host

**In git** (Starter and Template):

- `AGENTS.md` (thin pointers)
- `docs/agents/issue-tracker.md`, `triage-labels.md`, `domain.md`, **`handoff.md`**
- Glossary (`CONTEXT.md` here; upstream seed is `GLOSSARY.md` — align on the next agent-rails touch, do not block this layout)
- `docs/adr/` for the repo's own decisions

**On the host** (not git):

- Skill trees: global `~/.agents/skills/` plus the per-agent links `npx skills` creates
- Global lockfile `~/.agents/.skill-lock.json` (this host; Matt entries use `pluginName: mattpocock-skills` and `sourceUrl: https://github.com/mattpocock/skills.git`)
- Orca automations (runtime objects; `orca automations list`)
- `gh` auth (the claim identity `@me`)

**Do not vendor** skill folders into the repo or the Template. The map's fog (“Which Matt skill pack versions to pin, if research says they must be vendored”) can stay fog: pinning lives in the host lockfile and `npx skills update`, not in git. Project-local install (`orca skills install --local` / `npx skills add` without `-g`) drops a project `skills-lock.json` and agent directories; those are experiments, not the default, and should stay gitignored.

`just ci` and Generated-app boot must not call `orca-ide` or `npx skills`.

## 3. Wayfinder-frontier automation

### What “frontier” means

Wayfinder: a session **claims** by assigning the ticket **first**, before any work. The frontier is the open, **unblocked**, **unclaimed** children of the map. Unblocked = every blocker closed. (`wayfinder` SKILL.md, “Tickets”, “Work through the map”)

This repo's tracker doc: map is a `wayfinder:map` issue; children are GitHub sub-issues; blocking is native `blocked_by`; **frontier query** lists the map's open children, drops any with `issue_dependencies_summary.blocked_by > 0` or an assignee, first in **map order** wins; claim is `gh issue edit <n> --add-assignee @me`. (`docs/agents/issue-tracker.md`, “Wayfinding operations”; GitHub seed in `setup-matt-pocock-skills/issue-tracker-github.md`)

Overnight filter from the ticket: also require `ready-for-agent`. That is the AFK triage state (“fully specified, ready for an AFK agent”). HITL grilling/prototype tickets on this map carry `ready-for-human` and must not be picked up. (`triage` SKILL.md, “Roles”; `docs/agents/triage-labels.md`)

`issue_dependencies_summary.blocked_by` counts **open** blockers only (the live gate). `total_blocked_by` includes closed ones. On 2026-10-06, [Task: Scaffold generator landing boot](https://github.com/DavillyDevTeam/davilly-starter/issues/8) had `blocked_by: 0` and `total_blocked_by: 1` (closed research parent). Filter on `blocked_by`, not on `gh issue list --json blockedBy` `totalCount` (that field still lists closed blockers). ([REST issue dependencies](https://docs.github.com/rest/issues/issue-dependencies); live `GET /repos/DavillyDevTeam/davilly-starter/issues/8`)

**Map order is not `gh issue list` order.** `gh issue list --state open` on this repo returns recency (26, 25, …, 7). `GET /repos/{owner}/{repo}/issues/{issue_number}/sub_issues` returns the parent’s child list in map order (7, 8, 9, …). Use the sub-issues endpoint (paginate). ([REST sub-issues](https://docs.github.com/rest/issues/sub-issues); live `GET /repos/DavillyDevTeam/davilly-starter/issues/1/sub_issues`)

GitHub search has `is:blocked` / `is:blocking` and `no:assignee`, but search ranking is not map order. Fine as a human filter; not the precheck. ([Dependencies on issues changelog](https://github.blog/changelog/2025-08-21-dependencies-on-issues); `gh issue list --help` `--search`)

### `automations create` cannot take `--issue`

```text
orca automations create --name <name> --trigger <preset|cron|rrule> --prompt <text> --provider <agent>
  [--precheck <command>] [--repo <selector>|--workspace <selector>|…]
```

Flags of record: `--provider` (agent id; help examples `codex`, `claude`, `gemini`; orca-cli known ids include `grok`), `--precheck` (exit 0 continues, anything else records a **skipped** run), `--repo` XOR `--workspace`, `--workspace-mode existing|new-per-run`, `--base-branch`, `--disabled` / `--enabled`, `--reuse-session` / `--fresh-session`, `--time` / `--day` / `--timezone`. **No `--issue`.** (`orca-ide automations create --help`; `orca-ide skills get orca-cli --reference automations`)

So the scheduled run cannot bind the GitHub ticket at create time. The number is the next frontier child, discovered each run. The automation's **prompt** must perform the handoff with `worktree create --issue`.

`--repo` → new worktree **per run**. `--workspace` → existing Orca worktree. They are mutually exclusive. `--reuse-session` is only for existing-workspace automations. Prefer `--disabled` while testing; `orca automations run <id>` fires now. (automations reference)

### Recommended shape: dispatcher workspace + worker handoff

Use an **existing dispatcher worktree** (`--workspace`, `--workspace-mode existing`, `--fresh-session`) so each tick does not leave a leftover dispatcher checkout. The dispatcher does not implement the ticket.

1. **`--precheck`** exits 0 iff a takeable child exists (so empty nights are skipped, not confused agent turns).
2. **Prompt** loads the map, takes the first takeable child in map order, **claims** it, then full-handoffs.
3. Dispatcher **stops** after `accepted: true`. It does not wait, does not resolve, does not take a second ticket.

Precheck (Starter map is issue 1; Template/Generated-app maps substitute their `wayfinder:map` number):

```bash
gh api --paginate repos/DavillyDevTeam/davilly-starter/issues/1/sub_issues --jq '
  [.[]
    | select(.state == "open")
    | select([.labels[].name] | index("ready-for-agent"))
    | select((.assignees | length) == 0)
    | select(.issue_dependencies_summary.blocked_by == 0)
  ] | first | .number // empty
' | grep -q .
```

`first` on `[]` yields `null`; `// empty` prints nothing; `grep -q .` exits 1 → skipped run. (`orca-ide automations create --help`, “Use --precheck to run a bounded command before scheduled runs; exit code 0 continues, anything else records a skipped run.”) The help example `gh pr list --json number -q .[0].number` exits 0 on an empty list unless `jq -e` is used; do not copy that pattern.

Create **disabled** (do not run this in the research ticket):

```bash
orca-ide automations create \
  --name "Wayfinder frontier" \
  --trigger daily --time 02:00 --timezone <IANA> \
  --provider grok \
  --workspace <dispatcher-selector> \
  --workspace-mode existing \
  --fresh-session \
  --disabled \
  --precheck '<precheck above>' \
  --prompt '<dispatcher prompt below>' \
  --json
```

`--timezone` is host-specific. `--provider grok` is ADR 0003; Claude/Codex are documented swaps (`--provider claude` / `--provider codex`). Omit `--base-branch` so Orca uses the repo default (independent top-level work). (`orca-ide worktree create --help`, “--no-parent only affects Orca lineage; omit --base-branch to use the repo default base”)

Dispatcher prompt (keep this text in `docs/agents/handoff.md`; substitute `ORCA`):

```text
You are the Wayfinder frontier dispatcher for this repo. Do not implement the ticket.

1. Load the wayfinder skill. Read the wayfinder:map issue (low-res). Consult docs/agents/issue-tracker.md (Wayfinding operations) and docs/agents/handoff.md.
2. List the map's sub-issues in map order (GET …/issues/<map>/sub_issues, paginate). Take the first open child with label ready-for-agent, no assignees, and issue_dependencies_summary.blocked_by == 0. If none, stop.
3. Claim it first: gh issue edit <N> --add-assignee @me. If it is already assigned to someone else, stop.
4. Full handoff, then stop:
   ORCA worktree create --name "<ticket title>" --no-parent --agent grok --issue <N> --prompt "<worker prompt>" --json
5. Done when the create/send receipt has accepted: true. Report the worktree id and handle. Do not wait for the worker. Do not resolve a second ticket.
```

Worker prompt (passed as `--prompt`; `--issue N` is already on the worktree):

```text
Load the wayfinder skill. You own GitHub issue <N> (already claimed). Read gh issue view <N> --comments and the wayfinder:map Notes. Call whatever skills Notes names (grilling and domain-modeling if in doubt). Resolve this one ticket: comment the answer, close it, append a gist+link to the map's Decisions so far. Do not start another ticket.
```

`--agent grok` “launches the selected agent in the first terminal”; `--prompt` sends initial work. Prefer agent-first create (no extra fallback shell). (`orca-ide skills get orca-cli`, “Agent/setup flags”; `orca-ide worktree create --help`)

Wayfinder: never resolve more than one ticket per session, except research (charting fires those in parallel). Overnight dispatchers should still hand off **one** AFK ticket per run so claim/frontier stay honest. (`wayfinder` SKILL.md, “Invocation”)

This map **includes execution** of decided slices (Notes override plan-don’t-do). A `wayfinder:task` with `ready-for-agent` is valid overnight work; a `wayfinder:grilling` with `ready-for-human` is not. (`wayfinder` SKILL.md, “Plan, don't do”; map issue 1 Notes)

### Cheaper alternative (not the default)

`--repo` + `--workspace-mode new-per-run` can make the automation **itself** the worker (one worktree per ticket, then `worktree set --issue N` after claim). That skips a dispatcher hop but does not use `worktree create --issue` at create time, which is the ADR/ticket transfer. Keep it as a documented swap in `handoff.md`; default to dispatcher + `--issue`.

## 4. What the Copier Template must copy

Copier expands `template/` (plus `copier.yml` with `_subdirectory: template`) into the Generated app. Starter-only files stay outside `template/`. ([Research: uvx Typer Copier layout](https://github.com/DavillyDevTeam/davilly-starter/issues/2); `docs/research/uvx-typer-copier.md`)

### Copy (Generated-app tree)

```
AGENTS.md                          # thin pointers, including Handoff + Wayfinder
CONTEXT.md                         # or GLOSSARY.md once domain.md is aligned
docs/agents/issue-tracker.md       # GitHub; infers remote via gh
docs/agents/triage-labels.md       # default five roles
docs/agents/domain.md              # single-context
docs/agents/handoff.md             # disclosed recipes (this note)
docs/adr/                          # empty or Generated-app ADRs; not Starter 0001–0003
```

Parameterize identity (project name, author, license) the way the rest of the Template does. `issue-tracker.md` already says “Infer the repo from `git remote -v`” — do not hard-code `DavillyDevTeam/davilly-starter` into the Template copy.

### Do not copy

- `~/.agents/skills`, project `.agents/`, `skills-lock.json`, `.claude/skills`
- Live Orca automations, `orca.yaml` recipes, dispatcher worktree ids
- Starter `docs/research/` and Starter ADRs
- Anything that invokes `orca` / `orca-ide` from `just ci` or boot

GitHub **labels** (`needs-triage`, `ready-for-agent`, `wayfinder:map`, `wayfinder:research`, …) are tracker state, not Template files. Document a one-shot `gh label create` (or first `gh issue create --label`) in `handoff.md`. `setup-matt-pocock-skills` writes the mapping file; it does not create labels.

Consumers who never install Orca still get a Generated app that boots and passes `just ci`. Consumers who install the two skill packs + Orca get the same handoff and can add a **disabled** frontier automation against *their* map issue. That is the ADR 0003 split.

The Starter repo itself gets the same `AGENTS.md` pointers + `docs/agents/handoff.md` ([Task: Starter Orca and Matt agent rails](https://github.com/DavillyDevTeam/davilly-starter/issues/23)); the Template is a copy of that rails set, parameterized ([Task: Template Orca and Matt agent rails](https://github.com/DavillyDevTeam/davilly-starter/issues/24)); the disabled automation is host-only ([Task: Wayfinder frontier Orca automation](https://github.com/DavillyDevTeam/davilly-starter/issues/25)).

## Sources

- `orca-ide skills get orca-cli` (full handoffs, worktrees, `--agent` / `--prompt`, `accepted: true`, known ids including `grok`, Linux `orca-ide` stub)
- `orca-ide skills get orca-cli --reference automations`
- `orca-ide skills get orca-cli --reference publishing`
- `orca-ide skills install --help`, `orca-ide skills update --help`, `orca-ide skills share --help`, `orca-ide skills list --json`
- `orca-ide skills install --skill orca-cli --agent universal --dry-run --json` (and `--local` / `--all` dry-runs)
- `orca-ide automations create --help`, `orca-ide automations run --help`, `orca-ide worktree create --help`, `orca-ide worktree set --help`
- Matt skills: `setup-matt-pocock-skills`, `wayfinder`, `writing-for-agents`, `handoff`, `triage`, `grilling`, `domain-modeling` (`SKILL.md` frontmatter and bodies)
- `npx skills --help`; https://www.skills.sh/docs/cli ; https://www.skills.sh/docs/packs
- `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/adr/0003-orca-matt-handoff.md`, map issue 1 Notes
- GitHub: [sub-issues REST](https://docs.github.com/rest/issues/sub-issues), [issue dependencies REST](https://docs.github.com/rest/issues/issue-dependencies), [dependencies changelog](https://github.blog/changelog/2025-08-21-dependencies-on-issues)
- Live checks: `GET …/issues/1/sub_issues`, `GET …/issues/8`, `gh issue list --json parent,blockedBy`
