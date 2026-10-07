# Generated app is FastAPI + Vite React SPA

v1 Generated apps are an explicit FastAPI HTTP API plus a Vite React SPA, Postgres in Compose, SPA on Cloudflare Pages in prod and the API on any Docker host. Next.js full-stack, Django, Go, and Rust were considered and rejected for this Starter.

FastAPI matches a Python solopreneur plus overnight agents; Vite matches existing React work without App Router. An explicit API is the Tauri-later path and keeps Stripe webhooks and JWT auth as ordinary routes. Next.js was stronger for one-language typing and SSR landing pages; it hid the backend as Server Actions and would have to be peeled apart for a second client. Go and Rust were stronger on types and scale; they are the wrong default for a stranger-facing generator and for AFK agents. Django lost on typing.

Local dev is Vite + Uvicorn. FastAPI does not serve the SPA in prod and does not run on Cloudflare Workers.
