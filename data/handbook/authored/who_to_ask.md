---
source_url: local://handbook/authored/who_to_ask.md
license: MIT
retrieved: 2026-11-01
origin: authored
derived_from:
  - .github/CODEOWNERS
  - CONTRIBUTING.md
---

# Code Ownership and Who to Ask

This directory maps repository components and crates to official code owners based on `.github/CODEOWNERS` and contributor roles.

## Official Code Owners (from `.github/CODEOWNERS`)

- **Python Parser & Lexer** (`/crates/ruff_python_parser/`):
  - Primary Owners: `@MichaReiser`, `@dhruvmanila`
  - Scope: Tokenization, AST node definitions, parser error recovery.

- **Formatter Engine** (`/crates/ruff_formatter/`, `/crates/ruff_python_formatter/`):
  - Primary Owner: `@MichaReiser`
  - Scope: Formatting logic, layout engine, Black compatibility.

- **Jupyter Notebook Integration** (`/crates/ruff_notebook/`):
  - Primary Owner: `@dhruvmanila`
  - Scope: Notebook JSON parsing, cell extraction, line offset translation.

- **Diagnostic Snippet Rendering** (`/crates/ruff_annotate_snippets/`):
  - Primary Owner: `@BurntSushi`
  - Scope: Terminal highlighting, error spans, diagnostic snippet formatting.

- **Parser Fuzzing Tools** (`/python/py-fuzzer/`):
  - Primary Owner: `@AlexWaygood`
  - Scope: Differential fuzzing between Ruff parser and CPython.

- **Type Checker & Ty System** (`/crates/ty*`):
  - Notification Team: `@astral-sh/ty_notified`
  - Scope: Type inference, type checking infrastructure, language server daemon.

## Inferred Ownership (Git Commit Heuristic)
When a file or path lacks an explicit entry in `CODEOWNERS`, the assistant inspects the top committers over the last 90 days. Inferred owners are always designated as a **heuristic**, not official code ownership.

## General Guidance for Contributors
- When opening an issue or PR relating to an existing rule or crate, tag the relevant code owner from the list above.
- For pull requests, maintainer review assignments are handled automatically or guided by `.github/PULL_REQUEST_TEMPLATE.md`.
- Avoid duplicate work by checking open pull requests before beginning implementation on an issue.

