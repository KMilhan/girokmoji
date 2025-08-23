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
- Requires `libgit2` for `pygit2` runtime, and only that.

## Project Structure & Module Organization

- `girokmoji/`: core library and CLI entry `__main__.py` (modules: `semver.py`, `changelog.py`, `git.py`, `template.py`, `const.py`).
- `tests/`: `pytest` suite (e.g., `test_cli.py`, `test_semver.py`, `test_changelog.py`).
- `docs/`: supplementary docs and examples.
- Root: `pyproject.toml`, `README.md`, `LICENSE`, CI workflows under `.github/workflows/`.

## Build, Test, and Development Commands

- Setup: `uv venv && uv sync` (creates venv and installs deps).
- Test: `uv run pytest` (runs all tests).
- Lint/Format: `uv run ruff check .` and `uv run ruff format .`.
- Type check: `uv run pyright`.
- Build artifacts: `uv build` (hatchling backend; creates wheel/sdist in `dist/`).
- Run locally: `uv run girokmoji ...` or `uvx --from "girokmoji@latest" girokmoji ...`.

## Coding Style & Naming Conventions

- Python 3.10+, 4-space indentation, prefer functions over classes; `snake_case` for modules/functions, `PascalCase` for classes.
- Keep CLI concerns in `__main__.py`; keep pure logic in library modules.
- Run `ruff` and `pyright` before pushing; fix all warnings or justify in PR.

## Testing Guidelines

- Framework: `pytest`. Place tests in `tests/` as `test_*.py`; name tests clearly (e.g., `test_parses_prerelease_tag`).
- Add tests with each change; prefer small, behavior-focused tests.
- Measure coverage when useful: `uv run coverage run -m pytest && uv run coverage report`.

## Commit & Pull Request Guidelines

- Commit style: Gitmoji + conventional prefix, English, imperative mood.
  - Examples: `:sparkles: feat: add semver prerelease parsing`, `:bug: fix: handle missing tags`.
- Keep commits small and focused; separate refactors from behavior changes.
- PRs must include: summary, rationale, linked issues, test results, and CLI/output examples when relevant.
- CI must be green (tests, lint, type checks) before review.

## Security & Configuration Tips

- Uses `pygit2` (libgit2). Ensure tags/history are available; in CI use checkout with `fetch-depth: 0`.
- For release generation/tagging, run inside a git repo with reachable tags.
