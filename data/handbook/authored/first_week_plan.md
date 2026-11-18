---
source_url: local://handbook/authored/first_week_plan.md
license: MIT
retrieved: 2026-11-01
origin: authored
derived_from:
  - CONTRIBUTING.md
  - README.md
---

# First Week Onboarding Plan for Ruff Contributors

This structured plan guides new contributors through their first week of development, derived directly from `CONTRIBUTING.md` and repository guidelines.

## Day 1: Toolchain Installation and Initial Build
- Install the official [Rust toolchain](https://www.rust-lang.org/tools/install).
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage Python utility commands and the repository dev toolchain.
- Fork and clone the `astral-sh/ruff` repository.
- Verify the local build by running Ruff from the repository root:
  ```shell
  cargo run -p ruff -- check /path/to/test_file.py --no-cache
  ```

## Day 2: Test Suite and Snapshot Testing
- Review the test setup described in `CONTRIBUTING.md`.
- Recommended test runner is `nextest`. Run tests via:
  ```shell
  uv run --only-dev cargo nextest run
  # Alternatively, standard cargo test:
  RUFF_UPDATE_SCHEMA=1 cargo test
  ```
- Understand snapshot testing with [Insta](https://insta.rs/docs/). Snapshots update AST, linting, and formatting baseline fixtures:
  ```shell
  uv run --only-dev cargo insta --version
  ```

## Day 3: Code Validation and Pre-Commit Hooks
- Configure local git commit hooks to catch lint and format errors early:
  ```shell
  uv run --only-dev --locked prek install
  ```
- Practice running the three required pre-PR validation checks:
  ```shell
  # 1. Rust linting
  CARGO_BUILD_WARNINGS=deny cargo clippy --workspace --all-targets --all-features
  # 2. Rust testing and schema generation
  RUFF_UPDATE_SCHEMA=1 cargo test
  # 3. Formatting and ecosystem linting
  uv run --only-dev --locked prek run --all-files
  ```

## Day 4: Understanding the Crates Architecture
- Explore repository crate organization:
  - `crates/ruff`: The CLI entrypoint.
  - `crates/ruff_python_parser`: Lexer and parser converting Python code into an Abstract Syntax Tree.
  - `crates/ruff_linter`: Lint rules, diagnostic emission, and auto-fix implementations.
  - `crates/ruff_python_formatter`: Black-compatible Python code formatter.
- Read through the example in `CONTRIBUTING.md`: "Example: Adding a new lint rule" and "Example: Adding an auto-fix".

## Day 5: First Issue and Contribution
- Browse newcomer-friendly issues carrying the `good first issue` or `help wanted` label.
- Verify that no open pull request is already addressing the issue.
- Implement the change or rule addition.
- If snapshot tests changed, interactively review and accept the diff:
  ```shell
  uv run --only-dev cargo insta review
  ```
- Open a Pull Request following `.github/PULL_REQUEST_TEMPLATE.md` with appropriate rule tags in the title.

