# CORE DEVELOPMENT PRINCIPLES


- Follow Beck's "Tidy First" approach by separating structural changes from behavioral changes
- Maintain high code quality throughout development

## CODE QUALITY STANDARDS

- Eliminate duplication
- Express intent clearly through naming and structure
- Make dependencies explicit
- Keep methods small and focused on a single responsibility
- Minimize state and side effects
- Use the simplest solution that could possibly work

## Python-specific

- Prefer function style over class style.
- Prefer dependency injection style over managed resource or singleton.
- When threading seems attractive, consider using `asyncio`.
- When a compute-heavy operation is needed, think of avoiding GIL
  and using await possible instead of forking Python processes.
    - Prefer `numba` for compute-heavy operations over Cython, consider
      deeply about SIMD/MIMD, accelerated via GPU/accelerator operation.
    - Prefer array or tensor-based data structure for
      internal communication over library-specific data structure, for example, `Pillow` image data.
- Follow PEP over traditions, for example, a strict `pyproject.toml` structure.
- All configurations for tools are managed inside `pyproject.toml` instead of dedicated files per tool unless inevitable.
- Dependencies and virtual environments are managed via `uv`, and the build must be done by `hatchling`, but `uv build` or
  `pip install` must play with it.
- Compiling a specific module is recommended, as it is helpful in achieving a bit-perfect artifact and native performance optimization.

- Follw the Zen of Python ruthlessly

## Collaboration with MCP Servers

### Architect

You have "architect" who you can consult with at any planning stage.

### Senior Engineer

You have "senior-engineer" who you can talk about any problem you want to solve

### Pair programmer

You have "pair-programmer" who you should code with.

# Repository Guidelines

## Tooling & Prerequisites

- Use `uv` for environments and commands.
- Python 3.10+; build backend is `hatchling` (via `uv build`).
- Requires bundled `libgit2` for runtime plus `certifi` for CA bundles.
- Native builds use Zig + CMake (libgit2/mbedtls/zlib submodules).
## Project Structure & Module Organization

- `girokmoji/`: core library plus CLI entry `__main__.py`; functional modules include `semver.py`, `changelog.py`, `git.py`, `template.py`, and `const.py`.
- `tests/`: `pytest` suite (e.g., `test_cli.py`, `test_semver.py`, `test_changelog.py`). Mirror modules under test and keep fixtures close to their usage.
- `docs/`: supplementary docs and usage examples. Capture CLI walkthroughs and release recipes here.
- Root: `pyproject.toml`, `README.md`, `LICENSE`, CI workflows under `.github/workflows/`, `uv.lock`, and `RELEASE_NOTE_LONG.md`.

## Build, Test, and Development Commands

- Setup: `uv venv && uv sync` to create the virtual environment and install dependencies.
- Local CLI smoke test: `uv run girokmoji --help` or `uvx --from "girokmoji@latest" girokmoji ...`.
- Type checks: `uv run pyright`.
- Coverage (optional): `uv run coverage run -m pytest && uv run coverage report`.
- Build artifacts: `uv build` (hatchling backend; wheel and sdist land in `dist/`).
- **Always run before committing/pushing:** `uv run ruff format . && uv run ruff check . && uv run pyright && uv run pytest`. Do not skip even for small changes.
- When adding dependencies or tooling, update `pyproject.toml` and refresh `uv.lock`.

## Coding Style & Naming Conventions

- Python 3.10+, 4-space indentation, prefer functions over classes, and use dependency injection instead of singletons.
- `snake_case` for modules, functions, and variables; `PascalCase` for classes; constants `UPPER_SNAKE`.
- Keep CLI concerns inside `girokmoji/__main__.py` and keep pure logic in dedicated modules to stay testable.
- Express intent with names and structure; avoid implicit state. Run `ruff` and `pyright` locally before pushing.

## Testing Guidelines

- Framework: `pytest`. Place tests in `tests/` as `test_*.py`; choose descriptive names like `test_parses_prerelease_tag`.
- Add or update tests alongside every behavior change. Reproduce bugs in tests before fixing them.
- Keep tests fast by isolating git/filesystem boundaries and using lightweight fixtures.

## Commit & Pull Request Guidelines

- Commit style: Gitmoji + conventional prefix, imperative mood (`:<emoji>: type: subject`). Examples: `:sparkles: feat: add semver prerelease parsing`, `:bug: fix: handle missing tags`.
- Separate tidy/refactor commits from behavioral changes to honor "Tidy First".
- Commit bodies should explain why the change is needed, summarize what changed, and reference issues (e.g., `closes #42`).
- PRs must list summary, rationale, linked issues, and the commands run (`uv run ruff format .`, `uv run ruff check .`, `uv run pyright`, `uv run pytest`). Include CLI/output snippets when behavior changes.
- CI must be green (tests, lint, type checks) before review.

## Security & Configuration Tips

- Uses libgit2 directly. Ensure tags/history are available; in CI use checkout with `fetch-depth: 0`.
- For release generation/tagging, run inside a git repo with reachable tags.
- Never commit secrets; configuration happens through env vars or CLI args.

## Issue-Driven Workflow (Loop)

- Status labels: use `status:ready`, `status:in-progress`, `status:blocked`, `status:review`. Create any missing label via `gh label create "status:<name>" -R KMilhan/girokmoji --color 0366d6`.
- Pick work from open, non-epic issues labeled `status:ready` (prefer `priority:high`, then `type:task`/`type:enhancement`). Fallbacks: open `priority:high`, then the oldest open issue.
- Start work by scoping GitHub CLI (`gh repo set-default KMilhan/girokmoji`), moving the issue to `status:in-progress`, removing `status:ready`, and leaving a short comment outlining intended steps.
- Push frequently, keep commits atomic, and reference the issue ID in each commit/PR (`closes #<n>`). If blocked, swap labels to `status:blocked` with context.
- Close issues immediately after merge with a link to the commit/PR: `gh issue close <n> -R KMilhan/girokmoji -c "Done in <sha/url>"`.

## One-Phrase Command: "start work"

- Saying "start work" (optionally `start work #<n>`) triggers an autonomous loop:
  1. Ensure GitHub CLI targets `KMilhan/girokmoji` and status labels exist.
  2. Select the next issue per the workflow above or use the requested issue.
  3. Mark it in progress and comment the plan.
  4. Implement, commit to `main` with the Gitmoji+conventional format referencing the issue, and push immediately.
  5. Close the issue citing the commit/PR link.
  6. Stop after one issue unless instructed with "start work continuously" (which loops to the next ready issue).
- Utilities:
  - `preview start`: list the candidate issue and intended steps without mutating labels/comments.
  - `pause work`: swap back to `status:ready`, add context, and halt.
  - `next`: finish the current issue if done, then pick the next ready issue immediately.
