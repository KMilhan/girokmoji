# Agent Instructions

- Use `uv` for managing dependencies.
- Create a virtual environment via `uv venv` and activate it (`source .venv/bin/activate`).
- Install the project with development extras using `uv pip install -e ".[dev]"`.
- Run tests with `pytest -q` after installing dependencies. Do **not** use `uv run pytest`.
- Always run tests after making changes.
