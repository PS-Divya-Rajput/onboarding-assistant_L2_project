# Live Demonstration Script

This walkthrough guides reviewers through a step-by-step demonstration of the **Onboarding assistant**, highlighting tool reasoning chains, grounded citations, human-in-the-loop proposals, honest knowledge gap handling, and automatic LLM failover.

---

## Preparation and Launch

1. **Activate the Virtual Environment (PowerShell)**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Verify Services and Ingestion**:
   ```powershell
   .\venv\Scripts\python.exe scripts\check_env.py
   .\venv\Scripts\python.exe scripts\seed_db.py
   ```

3. **Launch the Streamlit Interface**:
   ```powershell
   .\venv\Scripts\python.exe -m streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.

---

## Scenario Walkthrough

### Scenario 1: Local Setup and Toolchain Prerequisites
- **Goal**: Demonstrate local RAG search over real repository documentation.
- **User Selection**: Select `Ravi Patel (Junior Contributor)` in the sidebar.
- **Input Query**:
  > *"How do I set the project up locally?"*
- **Expected System Behavior**:
  1. The agent invokes `search_onboarding_docs` with query *"setup prerequisites"*.
  2. The trace row renders: `01 search_onboarding_docs local 0.2 s`.
  3. The final answer provides exact prerequisites: installing the Rust toolchain, installing Astral's `uv`, building with `cargo run -p ruff -- check <file> --no-cache`, and running tests with `nextest`.
  4. The answer cites `[S1]`, pointing to `CONTRIBUTING.md > The Basics > Prerequisites`.
  5. The sources footer displays the green `[S1] · CONTRIBUTING.md` chip with a direct permalink.

---

### Scenario 2: Code Ownership and Component Navigation
- **Goal**: Demonstrate live directory inspection and CODEOWNERS pattern matching.
- **User Selection**: Keep `Ravi Patel` or switch to `Elena Rostova`.
- **Input Query**:
  > *"Where is the Python parser code located and who should I ask?"*
- **Expected System Behavior**:
  1. The agent invokes `get_directory_listing(path="crates")`.
  2. The agent invokes `find_code_owners(path="crates/ruff_python_parser")`.
  3. The trace collapses to: `2 steps · 0 handbook · 2 live · Gemini · 1.4 s`.
  4. The answer explains that the parser is located in `crates/ruff_python_parser` and that official code ownership is held by `@MichaReiser` and `@dhruvmanila` per `.github/CODEOWNERS`.

---

### Scenario 3: Task Discovery Without Duplication
- **Goal**: Demonstrate good-first issue filtering with automated exclusion of issues that have active PRs.
- **Input Query**:
  > *"Give me something to work on that doesn't have an active PR"*
- **Expected System Behavior**:
  1. The agent invokes `list_good_first_issues(limit=5, exclude_with_open_pr=True)`.
  2. The live GitHub client scans open PR titles/descriptions, identifies referenced issue numbers (`#N`), and filters them out.
  3. The assistant returns newcomer-friendly issues ready for assignment, linking directly to each issue URL.

---

### Scenario 4: Progress Check & Human-in-the-Loop Write Approval
- **Goal**: Demonstrate semi-autonomous write safety (proposal generation without writing until Apply is clicked).
- **User Selection**: `Ravi Patel` (currently on step 3).
- **Input Query**:
  > *"What should I do this week?"*
- **Expected System Behavior**:
  1. The agent calls `get_onboarding_progress` and `search_onboarding_docs`.
  2. The agent identifies that Ravi completed steps 1 and 2, is currently on step 3 (*"Install uv package manager"*), and needs to proceed to step 4 (*"Build Ruff locally"*).
  3. The agent calls `mark_task_done(task_id=3)`.
  4. **The Guardrail Engages**:
     - `dry_run=True` is enforced.
     - The agent yields a `ProposalRequested` event.
     - An amber-tinted **Proposed change** card renders:
       `Mark step 3 "Install uv package manager" as done for Ravi Patel`.
     - Two buttons appear: **Apply** and **Discard**.
  5. Click **Apply**:
     - The proposal executes with `dry_run=False`.
     - The database updates.
     - The sidebar segmented progress bar updates dynamically from `2 of 12` to `3 of 12` steps.

---

### Scenario 5: Honest Admission of Gaps & Question Logging
- **Goal**: Demonstrate that unanswerable queries never produce hallucinations.
- **Input Query**:
  > *"What is the corporate payroll policy and expense reimbursement procedure?"*
- **Expected System Behavior**:
  1. The agent searches the handbook via `search_onboarding_docs`.
  2. Cosine similarity drops below `0.30`; `matches: []` and `coverage: "none"` are returned.
  3. The agent does NOT invent a fictitious payroll policy.
  4. The agent responds honestly:
     > *"I do not know the answer as this topic is not documented in the repository handbook."*
  5. The agent automatically proposes calling `log_question(question=..., answered_from="none", resolved=false)` so documentation maintainers can address the gap.
  6. Click **Apply**:
     - The gap is logged to the `question_log` table.
     - Switch to the **Question log** tab in the top navigation to see the entry appear under **Gaps in the handbook**.

---

### Scenario 6: Automated LLM Failover
- **Goal**: Demonstrate resilience when the primary provider encounters an outage or rate limit.
- **Execution**:
  1. In the terminal or configuration, simulate a Gemini failure (or run `pytest tests/test_llm_provider.py` which executes this deterministically).
  2. When Gemini fails, the 60-second circuit breaker trips.
  3. The agent seamlessly reroutes the prompt to the Groq fallback (LLaMA 3.3 70B).
  4. The header status line immediately updates from `Gemini` with a green dot to `Groq, fallback active` with an amber dot.
  5. The trace details summary reflects that Groq fulfilled the response, ensuring zero developer downtime.

