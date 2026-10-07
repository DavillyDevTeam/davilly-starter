# Generated app Workspace is Nx + uv + pnpm

A Generated app is an **Nx** workspace: Vite SPA and FastAPI live as Nx projects, pnpm is the JS package manager, **uv** remains the only Python dependency tool (Nx targets shell out to `uv run`). This Starter (the Generator) stays a uv Python package; the Copier Template is package data, not an Nx project of the Starter.

Just is out. The Consumer-facing interface is `pnpm nx run-many -t lint,typecheck,test,build` (and a documented `dev` target). Python is a second-class citizen inside Nx; that cost is accepted because you want Nx’s graph, caching, and generator ecosystem, and because the SPA is the larger typed surface. FastAPI targets are `nx:run-commands` wrapping uv so agents cannot invent pip.
