# Typing hard-rules

## Dependency and task tools

- Use **uv only** for every Python dependency operation; run Python tools through `uv run`. Do not use pip, Poetry, or PDM.
- Use **pnpm** for JavaScript and TypeScript dependencies and commands; do not use npm, npx, or Bun.
- This Starter is a uv Python project. The **Generated app** uses **Nx** as its task surface: `pnpm nx run-many -t lint,typecheck,test,build`. Python Nx targets invoke `uv run`. Do not introduce Just. See [ADR 0004](../adr/0004-nx-uv-pnpm-workspace.md).

## Type correctness

Apply these rules to the Generator and to code authored for the Generated app:

- Use the strictest practical type-checker settings. Fix type errors in code rather than weakening checker settings.
- Do not use Python `Any` or TypeScript `any` as an escape hatch. Model concrete types; narrow `object` or `unknown` at untrusted boundaries.
- Do not add `# type: ignore`, `# pyright: ignore`, `@ts-ignore`, `@ts-expect-error`, or other checker-suppression comments without the specific error code and a one-line explanation of why suppression is necessary. Use checker-supported code scoping where available; for TypeScript directives, include the diagnostic code in the explanation. Fix the underlying type error whenever possible.
- Do not use TypeScript `as` assertions (including double assertions) to silence the checker. Use narrowing, validation, or correct declarations instead.
- **CI typecheck is the gate:** CI must fail on type errors. Run the configured typecheck before submitting changes; resolve failures rather than suppressing them, skipping the check, or allowing it to fail. TypeScript uses `tsc --noEmit`; consult the project's configuration for the Python checker and exact commands.

## Template boundary

These are the Starter's agent rails. Do not create a Generated-app `AGENTS.md` before the Template exists ([Task: Scaffold generator landing boot](https://github.com/DavillyDevTeam/davilly-starter/issues/8)). Copy these rules into the Template through the Generated-app toolchain task once that boundary exists.
