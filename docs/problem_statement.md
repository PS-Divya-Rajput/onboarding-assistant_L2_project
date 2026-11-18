# Problem Statement and Solution Scope

## The Problem

Software engineer onboarding is one of the most expensive and fragmented bottlenecks in engineering organizations:

1. **Lost Engineering Velocity**: New hires often spend their first 2–4 weeks struggling to configure development toolchains, resolve compiler discrepancies, run test suites, and decipher undocumented tribal conventions.
2. **Senior Engineer Interruption Fatigue**: Experienced maintainers and senior developers are frequently pulled out of flow state to answer repetitive foundational questions ("How do I run tests?", "Where does this module live?", "Who owns the parser?").
3. **Out-of-Date or Fragmented Documentation**: Crucial setup instructions, architecture notes, and contribution guidelines are often scattered across repository readmes, issue templates, wikis, and PR threads.
4. **Analysis Paralysis for First Tasks**: Junior and newcomer engineers struggle to determine which issues are truly unassigned and unworked versus those that already have active work-in-progress pull requests.

---

## The Solution

**Onboarding assistant** is a goal-based, tool-augmented AI developer assistant that answers onboarding questions in plain language while strictly grounding every claim in verified repository facts:

- **Dual-Knowledge Architecture**: Blends local RAG search over verified onboarding documentation ("how do we do things here") with live GitHub REST API tools ("what is true right now").
- **Human-in-the-Loop Safeguards**: Write actions (such as logging documentation gaps or marking onboarding checklist steps complete) are strictly proposed for explicit human approval via the UI.
- **Zero-Trust Privacy Layer**: Enforces strict boundaries to ensure intellectual property and sensitive credentials never leak to external LLMs.

---

## Honest Scope and Deployment Boundaries

To ensure complete explainability and transparency for technical review, this system operates within the following defined prototype boundaries:

1. **Target Repository Scope**:
   - The prototype targets a single large, active open-source repository: `astral-sh/ruff` (an extremely fast Python linter and formatter written in Rust).
   - *Enterprise Portability*: Deploying to a private enterprise repository requires solely updating the `TARGET_REPO` and `GITHUB_TOKEN` credentials in `.env`. All tool logic, pattern matchers, and privacy protections apply identically to private repositories.

2. **Scoped Handbook Corpus**:
   - The handbook is built directly from `astral-sh/ruff`'s real public documentation (`README.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, and guides under `docs/`).
   - Three authored notes (`first_week_plan.md`, `glossary.md`, `who_to_ask.md`) were drafted strictly from the fetched documentation to represent the synthesized notes a real engineering team would maintain.

3. **Simulated Multi-User State**:
   - Onboarding checklist progress and historical question logs are seeded with 3 realistic sample developer personas (`user_ravi`, `user_elena`, `user_marcus`) at different onboarding stages.
   - In a production enterprise deployment, the SQLite database starts empty and is populated through genuine user interactions.

4. **Zero Source Code Inspection**:
   - As a deliberate architectural privacy decision, no tool in this assistant reads or returns the contents of source code files (`.rs`, `.py`, `.c`, etc.).
   - All code ownership, directory hierarchies, and issue tracking are derived purely from metadata, directory entries, `CODEOWNERS`, and git commit histories.

