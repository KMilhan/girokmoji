# Agent Instructions

## Testing

- Use `uv venv` to create a virtual environment and `uv pip install -e ".[dev]"` to install dependencies.
- Run tests with `pytest`. Do not run `uv run pytest`.
- If installing dependencies fails (for example, due to network issues) or `pytest` is unavailable, note the failure in your PR summary.
- Ensure `pytest` is executed directly so failures are visible.
