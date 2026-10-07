# davilly-starter

Davilly’s open-source **app starter**. Not an LLM/agent product kit.

```bash
uvx davilly-starter new my-app
```

The CLI does not generate an app yet. This repo is the public home for that generator.

## What it will generate (v1)

A **web** app (no desktop in v1):

| Piece | Choice |
|--------|--------|
| API | FastAPI |
| UI | Vite + React SPA |
| Auth | Email/password or magic link + sessions |
| Payments | Stripe |
| Marketing | Landing page |
| Local run | Docker Compose |
| Copy | English **and** Portuguese (Brazil) |
| Agent rails | `AGENTS.md` + `docs/agents/` (issue tracker / triage / domain docs) |

**Later (not v1):** Tauri as a generator flag. Not Next.js. Not a second HTTP server.

## Why it exists

This is **Davilly Software’s internal starter**, published so other people can use the same skeleton. Strangers clone it; if nobody else does, Davilly still uses it.

GitHub org: [DavillyDevTeam](https://github.com/DavillyDevTeam). The product name is `davilly-starter`, not “AI stack”.

## License

[MIT](LICENSE) © 2026 Davilly Software
