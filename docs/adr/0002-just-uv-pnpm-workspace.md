---
status: superseded by ADR-0004
---

# Polyglot workspace is Just + uv + pnpm

A Generated app is one git repo with a FastAPI package and a Vite SPA. Root tasks go through **Just**; all Python dependency operations go through **uv**; the SPA uses **pnpm**. This Starter itself is a uv project; the Copier Template is package data, not a second language workspace of the Starter.

Turborepo and Nx are JS-first and treat Python as a foreign task. moonrepo is polyglot but less common for strangers cloning a starter. Bazel and Pants are too heavy for v1. A root `package.json` that shells out to uv would hide the Python toolchain. Just stays language-agnostic; `just --list` is the Consumer-facing interface (`dev`, `lint`, `typecheck`, `test`, `ci`).
