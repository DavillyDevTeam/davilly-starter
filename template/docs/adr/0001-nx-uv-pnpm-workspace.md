# Workspace is Nx + uv + pnpm

This repository is an **Nx** workspace: the Vite SPA and FastAPI live as Nx projects, pnpm is the JS package manager, and **uv** is the Python dependency tool (Nx targets shell out to `uv run`).

The task surface is `pnpm nx run-many -t lint,typecheck,test,build` (and a documented `dev` target). FastAPI targets are `nx:run-commands` wrapping `uv run`.
