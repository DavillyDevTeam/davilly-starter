# davilly-starter

Davilly Software’s public app Starter: a Generator that writes a Generated app for a Consumer.

## Language

**Starter**:
The product in this repository: a published Generator plus the Template it expands. v1 serves Davilly Software and external Consumers equally.
_Avoid_: AI stack, kit, boilerplate

**Generator**:
The `davilly-starter new` CLI (Typer wrapping Copier) that writes a Generated app from the Template. Invoked as `uvx davilly-starter new my-app` once on PyPI, or via `uvx` from this git URL until then.
_Avoid_: scaffold CLI, cookiecutter (the engine is Copier)

**Template**:
The Copier tree inside the Starter that becomes a Generated app after parameters are filled.
_Avoid_: example app, reference app

**Generated app**:
The application tree the Generator writes. v1 is a FastAPI API plus a Vite React SPA, with Postgres, parameterized identity, and no hard-coded Davilly product branding.
_Avoid_: starter (that word is this repo), scaffold, boilerplate

**Consumer**:
A person or agent who runs the Generator to obtain a Generated app. Davilly Software and strangers are both Consumers in v1.
_Avoid_: user (ambiguous with an end-user of a Generated app), customer (ambiguous with Stripe)

**End-user**:
A person who signs into a Generated app (email/password, optional Google or GitHub).
_Avoid_: Consumer, customer

**Workspace**:
The Generated app’s polyglot tree (FastAPI + Vite SPA) as an Nx workspace: pnpm for TypeScript, uv for Python (Nx targets call `uv run`). This Starter itself is not an Nx workspace.
_Avoid_: Just, Turborepo, moon
