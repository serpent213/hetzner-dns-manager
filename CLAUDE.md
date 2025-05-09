# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Build/Lint/Test Commands

- Format code: `uv run poe format`
- Format check: `uv run poe formatcheck`
- Lint: `uv run poe lint`
- Type check: `uv run poe typecheck`
- Tests: `uv run poe test`
- Run all checks: `uv run poe check`
- Fix format and lint: `uv run poe fix`

## Code Style Guidelines

- Python version: 3.10+
- Line length: 118 characters max
- Formatting: Uses ruff formatter
- Structure: `hdem` is a stand-alone, self-contained script (PEP 723), only tests exist outside of it
  - The file contains the sections: Data Model, Helper Classes, Helper Functions, CLI Actions
- Dependencies: In `pyproject.toml` and additionally in the header of the `hdem` executable
- Imports: Organized in blocks (standard library, 3rd party, local)
- Error handling: Use specific exceptions with clear error messages
- Types: All functions should have proper type annotations
- Documentation: Functions should have docstrings with Args/Returns sections
- Pattern matching: Use Python 3.10+ match/case for cleaner conditionals
- Validation: Always validate input data strictly (see Record.__post_init__)
