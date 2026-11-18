---
source_url: local://handbook/authored/glossary.md
license: MIT
retrieved: 2026-11-01
origin: authored
derived_from:
  - CONTRIBUTING.md
  - docs/configuration.md
  - docs/linter.md
  - docs/formatter.md
---

# Ruff Project Glossary

A comprehensive reference of tools, libraries, and terms used across the Ruff repository, derived directly from documentation files.

## Development Tools
- **uv**: An extremely fast Python package manager and resolver created by Astral. In the Ruff repo, `uv` is used to run Python utility commands, manage the developer toolchain, and execute development scripts.
- **nextest**: A next-generation test runner for Cargo projects. Recommended for running Ruff's test suite via `uv run --only-dev cargo nextest run` due to its parallel execution performance.
- **insta**: A Rust snapshot testing library. Ruff stores expected test outputs (such as diagnostic messages, AST structures, and formatted code) in `.snap` files. Run `uv run --only-dev cargo insta review` to inspect and accept changed snapshots.
- **prek**: A pre-commit hook runner tool used in the repository to format Rust code, check markdown files, and run code linters prior to git commits (`uv run --only-dev --locked prek run --all-files`).
- **clippy**: The official Rust static analyzer and linter. Enforced in CI with `CARGO_BUILD_WARNINGS=deny cargo clippy --workspace --all-targets --all-features`.

## Core Crates
- **`crates/ruff`**: The primary command-line binary interface for both linting and formatting.
- **`crates/ruff_python_parser`**: The parsing crate that transforms raw Python source code into structured Abstract Syntax Tree (AST) nodes and tokens.
- **`crates/ruff_linter`**: The core linting engine holding all rule implementations, diagnostics, rule configurations, and auto-fix logic.
- **`crates/ruff_python_formatter`**: The AST-driven code formatting engine designed as a drop-in replacement for Black.
- **`crates/ruff_notebook`**: Specialized handling for Jupyter Notebook files (`.ipynb`), extracting cell contents while preserving line mappings.
- **`crates/ruff_annotate_snippets`**: Library for rendering terminal diagnostic snippets with colored arrows and source code previews.

## Rule and Linting Concepts
- **Rule Code**: An alphanumeric identifier for a lint rule (e.g., `E402`, `SIM103`, `B031`). Grouped under prefixes representing tool lineages (such as `flake8-bugbear`, `pycodestyle`, `pydocstyle`).
- **Auto-fix**: Automated remediation of a detected diagnostic. Classified in Ruff documentation as either safe (preserves program semantics under all circumstances) or unsafe.
- **Ecosystem CI**: Automated integration testing where Ruff is run across major open-source Python codebases (e.g., Pandas, FastAPI, Scikit-learn) to detect unexpected regressions before release.

