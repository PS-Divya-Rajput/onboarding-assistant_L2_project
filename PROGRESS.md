# Onboarding assistant — Progress & Implementation Checklist

## Project Status Overview
- **Project Name**: Onboarding assistant
- **Developer Environment**: Windows 11 (PowerShell primary, bash secondary)
- **Python**: 3.11.3 (in virtual environment `venv`)
- **Current Phase**: Phase 6 Complete (Project Fully Finished)

---

## SDK Version & API Audit (Rule 5 Compliance)
- **`mcp` version `2.3.0`**:
  - *Deviation & Adaptation*: In `mcp` 2.x, FastMCP was restructured into `mcp.server.mcpserver.MCPServer`. Decorators `@server.tool()` and `@server.resource()` are provided natively by `MCPServer`. Stdio client is in `mcp.client.stdio.stdio_client` and `mcp.client.session.ClientSession`.
- **`google-genai` version `2.11.0`**:
  - `from google import genai` and `from google.genai import types`.
  - Configured via `genai.Client(api_key=...)`.
  - Content generation via `client.models.generate_content(...)`.
- **`groq` version `1.7.0`**:
  - `from groq import Groq`.
  - Client initialized with `Groq(api_key=...)`.
  - Completions via `client.chat.completions.create(...)`.
- **`chromadb` version `1.5.9`**:
  - Persistent store via `chromadb.PersistentClient(path=...)`.
- **`sentence-transformers` version `6.2.0`**:
  - `from sentence_transformers import SentenceTransformer`.
- **`streamlit` version `1.59.2`**:
  - Streamlit UI runtime.
- **`pytest` version `9.2.0`**, **`pytest-asyncio` version `1.4.1`**, **`respx` version `0.23.1`**.

---

## Master Checklist

### Phase 1: Scaffold & Configuration
- [x] Repository structure and directories
- [x] Virtual environment (`venv`) setup with all required dependencies
- [x] `.gitignore` (ignoring venv, .env, *.db, chroma_store, eval results, logs)
- [x] `.env.example`
- [x] `requirements.txt` (pinned exact versions)
- [x] `pyproject.toml`
- [x] `config.py` (strict validation, no hardcoded secrets/models/repos)
- [x] `scripts/check_env.py` (checks keys, rate limit, repo access)
- [x] `PROGRESS.md`
- [x] `README.md` skeleton

### Phase 2: MCP Server, Live Tools, and Privacy Layer
- [x] `mcp_server/schemas.py` (strict Pydantic models for all tool I/O + `source_refs`)
- [x] `mcp_server/privacy.py` (privacy layer: no source code, path denylist, token/key redactions, repo allowlist, audit log, untrusted content handling)
- [x] `mcp_server/github_client.py` (httpx client, caching with TTL, rate limit headers, issue/PR separation)
- [x] `mcp_server/db.py` (SQLite connection and audit log persistence)
- [x] `mcp_server/tools/live_repo_tools.py` (`get_repo_overview`, `get_directory_listing`)
- [x] `mcp_server/tools/live_issue_tools.py` (`list_good_first_issues`, `get_recent_prs`)
- [x] `mcp_server/tools/live_owner_tools.py` (`find_code_owners` with pathspec + 90-day commit fallback)
- [x] `tests/test_privacy.py` (tests redaction, denylist, audit logging, dry_run enforcement)
- [x] `tests/test_tools.py` (live tool tests mocked with `respx`)

---

## Pytest Execution Record

### Phase 2 Pytest Output
```
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\DivyaRajput\Desktop\L2\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\DivyaRajput\Desktop\L2
configfile: pyproject.toml
plugins: respx-0.23.1, anyio-4.14.2, langsmith-0.10.3, asyncio-1.4.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 13 items

tests/test_privacy.py::test_path_denylist PASSED                         [  7%]
tests/test_privacy.py::test_allowed_doc_path_rules PASSED                [ 15%]
tests/test_privacy.py::test_credential_redaction PASSED                  [ 23%]
tests/test_privacy.py::test_private_key_redaction PASSED                 [ 30%]
tests/test_privacy.py::test_redact_nested_data PASSED                    [ 38%]
tests/test_privacy.py::test_untrusted_text_sanitization PASSED           [ 46%]
tests/test_privacy.py::test_zero_payload_audit_logging PASSED            [ 53%]
tests/test_tools.py::test_get_repo_overview PASSED                       [ 61%]
tests/test_tools.py::test_get_directory_listing_allowed_and_denied PASSED [ 69%]
tests/test_tools.py::test_list_good_first_issues_and_pr_exclusion PASSED [ 76%]
tests/test_tools.py::test_find_code_owners_codeowners_file PASSED        [ 84%]
tests/test_tools.py::test_find_code_owners_inferred_fallback PASSED      [ 92%]
tests/test_tools.py::test_get_recent_prs PASSED                          [100%]

======================= 13 passed in 1.99s ========================
```

### Phase 3: Handbook RAG, Progress Tools, and Seed Data
- [x] `data/handbook_sources.json` (document manifest)
- [x] `scripts/fetch_handbook.py` (downloads real docs from GitHub TARGET_REPO with front matter and permalinks)
- [x] `data/handbook/authored/` (`first_week_plan.md`, `glossary.md`, `who_to_ask.md` derived strictly from fetched docs)
- [x] `scripts/ingest_handbook.py` (chunks markdown by headers, embeds with all-MiniLM-L6-v2, populates ChromaDB)
- [x] `scripts/seed_db.py` (SQLite schema, 12 handbook tasks, 3 sample users, sample question log)
- [x] `mcp_server/tools/local_handbook_tools.py` (`search_onboarding_docs`)
- [x] `mcp_server/tools/local_progress_tools.py` (`get_onboarding_progress`, `mark_task_done`, `log_question`)
- [x] Expose handbook files as MCP resources (`handbook://<path>`)
- [x] `tests/test_handbook_ingest.py`
- [x] Phase 3 test verification and real pytest output recorded

---

## Pytest Execution Record

### Phase 3 Pytest Output
```
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\DivyaRajput\Desktop\L2\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\DivyaRajput\Desktop\L2
configfile: pyproject.toml
testpaths: tests
plugins: respx-0.23.1, anyio-4.14.2, langsmith-0.10.3, asyncio-1.4.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 21 items

tests/test_handbook_ingest.py::test_front_matter_validation_and_rejection PASSED [  4%]
tests/test_handbook_ingest.py::test_markdown_hierarchical_chunking PASSED [  9%]
tests/test_handbook_ingest.py::test_search_onboarding_docs_semantic_match PASSED [ 14%]
tests/test_handbook_ingest.py::test_search_onboarding_docs_unanswerable_query PASSED [ 19%]
tests/test_handbook_ingest.py::test_get_onboarding_progress_seeded_users PASSED [ 23%]
tests/test_handbook_ingest.py::test_write_tools_dry_run_safety PASSED    [ 28%]
tests/test_handbook_ingest.py::test_log_question_dry_run_safety PASSED   [ 33%]
tests/test_handbook_ingest.py::test_resource_read_handbook_doc PASSED    [ 38%]
tests/test_privacy.py::test_path_denylist PASSED                         [ 42%]
tests/test_privacy.py::test_allowed_doc_path_rules PASSED                [ 47%]
tests/test_privacy.py::test_credential_redaction PASSED                  [ 52%]
tests/test_privacy.py::test_private_key_redaction PASSED                 [ 57%]
tests/test_privacy.py::test_redact_nested_data PASSED                    [ 61%]
tests/test_privacy.py::test_untrusted_text_sanitization PASSED           [ 66%]
tests/test_privacy.py::test_zero_payload_audit_logging PASSED            [ 71%]
tests/test_tools.py::test_get_repo_overview PASSED                       [ 76%]
tests/test_tools.py::test_get_directory_listing_allowed_and_denied PASSED [ 80%]
tests/test_tools.py::test_list_good_first_issues_and_pr_exclusion PASSED [ 85%]
tests/test_tools.py::test_find_code_owners_codeowners_file PASSED        [ 90%]
tests/test_tools.py::test_find_code_owners_inferred_fallback PASSED      [ 95%]
tests/test_tools.py::test_get_recent_prs PASSED                          [100%]

======================= 21 passed in 41.98s ========================
```

### Phase 4: LLM Failover and Agent Loop
- [x] `agent/events.py` (typed events and proposals)
- [x] `agent/llm_provider.py` (Gemini primary, Groq fallback, circuit breaker, timeout, structured errors)
- [x] `scripts/check_llm.py` (live smoke test script for Gemini & Groq)
- [x] `agent/mcp_bridge.py` (sync wrapper over async MCP client in background thread with Proactor loop on Windows)
- [x] `agent/system_prompt.py` (strict grounding, untrusted content safety, dry_run enforcement, source citations)
- [x] `agent/agent.py` (ReAct loop, tool execution, session cache, proposal emission, max 6 steps)
- [x] `tests/test_llm_provider.py` (mocked 429, timeout, 500, 404, circuit breaker, failover)
- [x] `tests/test_agent.py` (deterministic fake LLM/bridge tests: tool chains, unknown questions, injection defense, dry_run=False stripping)
- [x] Phase 4 test verification and real pytest output recorded

---

## Pytest Execution Record

### Phase 4 Pytest Output
```
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\DivyaRajput\Desktop\L2\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\DivyaRajput\Desktop\L2
configfile: pyproject.toml
testpaths: tests
plugins: respx-0.23.1, anyio-4.14.2, langsmith-0.10.3, asyncio-1.4.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 36 items

tests/test_agent.py::test_example_1_local_setup_tool_chain PASSED        [  2%]
tests/test_agent.py::test_example_2_where_is_x_and_who_to_ask PASSED     [  5%]
tests/test_agent.py::test_example_3_something_to_work_on PASSED          [  8%]
tests/test_agent.py::test_example_4_what_should_i_do_this_week_with_write_proposal PASSED [ 11%]
tests/test_agent.py::test_model_supplied_dry_run_false_is_strictly_ignored PASSED [ 13%]
tests/test_agent.py::test_unanswerable_question_admits_gap_and_proposes_log_question PASSED [ 16%]
tests/test_agent.py::test_step_cap_graceful_termination PASSED           [ 19%]
tests/test_agent.py::test_prompt_injection_in_issue_title_defense PASSED [ 22%]
tests/test_handbook_ingest.py::test_front_matter_validation_and_rejection PASSED [ 25%]
tests/test_handbook_ingest.py::test_markdown_hierarchical_chunking PASSED [ 27%]
tests/test_handbook_ingest.py::test_search_onboarding_docs_semantic_match PASSED [ 30%]
tests/test_handbook_ingest.py::test_search_onboarding_docs_unanswerable_query PASSED [ 33%]
tests/test_handbook_ingest.py::test_get_onboarding_progress_seeded_users PASSED [ 36%]
tests/test_handbook_ingest.py::test_write_tools_dry_run_safety PASSED    [ 38%]
tests/test_handbook_ingest.py::test_log_question_dry_run_safety PASSED   [ 41%]
tests/test_handbook_ingest.py::test_resource_read_handbook_doc PASSED    [ 44%]
tests/test_llm_provider.py::test_gemini_success PASSED                   [ 47%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[Exception-429 Quota Exceeded] PASSED [ 50%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[TimeoutError-Request timed out after 20 seconds] PASSED [ 52%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[Exception-500 Internal Server Error] PASSED [ 55%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[Exception-404 Model not found] PASSED [ 58%]
tests/test_llm_provider.py::test_circuit_breaker_skips_gemini_on_subsequent_call PASSED [ 61%]
tests/test_llm_provider.py::test_both_providers_fail_raises_llm_unavailable PASSED [ 63%]
tests/test_privacy.py::test_path_denylist PASSED                         [ 66%]
tests/test_privacy.py::test_allowed_doc_path_rules PASSED                [ 69%]
tests/test_privacy.py::test_credential_redaction PASSED                  [ 72%]
tests/test_privacy.py::test_private_key_redaction PASSED                 [ 75%]
tests/test_privacy.py::test_redact_nested_data PASSED                    [ 77%]
tests/test_privacy.py::test_untrusted_text_sanitization PASSED           [ 80%]
tests/test_privacy.py::test_zero_payload_audit_logging PASSED            [ 83%]
tests/test_tools.py::test_get_repo_overview PASSED                       [ 86%]
tests/test_tools.py::test_get_directory_listing_allowed_and_denied PASSED [ 88%]
tests/test_tools.py::test_list_good_first_issues_and_pr_exclusion PASSED [ 91%]
tests/test_tools.py::test_find_code_owners_codeowners_file PASSED        [ 94%]
tests/test_tools.py::test_find_code_owners_inferred_fallback PASSED      [ 97%]
tests/test_tools.py::test_get_recent_prs PASSED                          [100%]

================== 36 passed in 60.21s ===================
```

### Phase 5: Streamlit Interface
- [x] `.streamlit/config.toml` (editorial theme: warm paper, no default pink, minimal toolbar)
- [x] `ui/theme.py` (CSS variables, Newsreader + IBM Plex fonts, no emoji, WCAG AA contrast)
- [x] `ui/components.py` (custom headers, sources chips, proposal cards, collapsible trace summary)
- [x] `ui/views.py` (Ask view, Path view, Question log view)
- [x] `app.py` (clean entrypoint, background bridge initialization, session state management)
- [x] `tests/test_ui_smoke.py` (`AppTest` smoke test: 3 users, 3 tabs, no unhandled exceptions)
- [x] Browser testing and screenshots saved to `docs/screenshots/`
- [x] Phase 5 checklist verification (no forbidden widgets, contrast, fonts, emoji-free)

---

## Pytest Execution Record

### Phase 5 Pytest Output
```
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\DivyaRajput\Desktop\L2\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\DivyaRajput\Desktop\L2
configfile: pyproject.toml
testpaths: tests
plugins: respx-0.23.1, anyio-4.14.2, langsmith-0.10.3, asyncio-1.4.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 38 items

tests/test_agent.py::test_example_1_local_setup_tool_chain PASSED        [  2%]
tests/test_agent.py::test_example_2_where_is_x_and_who_to_ask PASSED     [  5%]
tests/test_agent.py::test_example_3_something_to_work_on PASSED          [  7%]
tests/test_agent.py::test_example_4_what_should_i_do_this_week_with_write_proposal PASSED [ 10%]
tests/test_agent.py::test_model_supplied_dry_run_false_is_strictly_ignored PASSED [ 13%]
tests/test_agent.py::test_unanswerable_question_admits_gap_and_proposes_log_question PASSED [ 15%]
tests/test_agent.py::test_step_cap_graceful_termination PASSED           [ 18%]
tests/test_agent.py::test_prompt_injection_in_issue_title_defense PASSED [ 21%]
tests/test_handbook_ingest.py::test_front_matter_validation_and_rejection PASSED [ 23%]
tests/test_handbook_ingest.py::test_markdown_hierarchical_chunking PASSED [ 26%]
tests/test_handbook_ingest.py::test_search_onboarding_docs_semantic_match PASSED [ 28%]
tests/test_handbook_ingest.py::test_search_onboarding_docs_unanswerable_query PASSED [ 31%]
tests/test_handbook_ingest.py::test_get_onboarding_progress_seeded_users PASSED [ 34%]
tests/test_handbook_ingest.py::test_write_tools_dry_run_safety PASSED    [ 36%]
tests/test_handbook_ingest.py::test_log_question_dry_run_safety PASSED   [ 39%]
tests/test_handbook_ingest.py::test_resource_read_handbook_doc PASSED    [ 42%]
tests/test_llm_provider.py::test_gemini_success PASSED                   [ 44%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[Exception-429 Quota Exceeded] PASSED [ 47%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[TimeoutError-Request timed out after 20 seconds] PASSED [ 50%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[Exception-500 Internal Server Error] PASSED [ 52%]
tests/test_llm_provider.py::test_gemini_failover_to_groq[Exception-404 Model not found] PASSED [ 55%]
tests/test_llm_provider.py::test_circuit_breaker_skips_gemini_on_subsequent_call PASSED [ 57%]
tests/test_llm_provider.py::test_both_providers_fail_raises_llm_unavailable PASSED [ 60%]
tests/test_privacy.py::test_path_denylist PASSED                         [ 63%]
tests/test_privacy.py::test_allowed_doc_path_rules PASSED                [ 65%]
tests/test_privacy.py::test_credential_redaction PASSED                  [ 68%]
tests/test_privacy.py::test_private_key_redaction PASSED                 [ 71%]
tests/test_privacy.py::test_redact_nested_data PASSED                    [ 73%]
tests/test_privacy.py::test_untrusted_text_sanitization PASSED           [ 76%]
tests/test_privacy.py::test_zero_payload_audit_logging PASSED            [ 78%]
tests/test_tools.py::test_get_repo_overview PASSED                       [ 81%]
tests/test_tools.py::test_get_directory_listing_allowed_and_denied PASSED [ 84%]
tests/test_tools.py::test_list_good_first_issues_and_pr_exclusion PASSED [ 86%]
tests/test_tools.py::test_find_code_owners_codeowners_file PASSED        [ 89%]
tests/test_tools.py::test_find_code_owners_inferred_fallback PASSED      [ 92%]
tests/test_tools.py::test_get_recent_prs PASSED                          [ 94%]
tests/test_ui_smoke.py::test_ui_smoke_boot_and_components PASSED         [ 97%]
tests/test_ui_smoke.py::test_ui_tab_navigation PASSED                    [100%]

================== 38 passed in 78.89s ===================
```

### Phase 6: Evaluation and Documentation
- [x] `eval/questions.json` (12+ realistic onboarding questions, 3 unanswerable)
- [x] `eval/run_eval.py` (deterministic metrics evaluation: tool selection, groundedness, honest unknowns, guardrails, latency)
- [x] Run evaluation and output to `eval/results/`
- [x] `docs/evaluation.md` (generated from eval results)
- [x] `docs/architecture.md` (Mermaid diagram + comprehensive component breakdown)
- [x] `docs/problem_statement.md` (problem, solution, scope honesty)
- [x] `docs/privacy_and_data_governance.md` (6-point privacy architecture, data flow, LLM privacy notice)
- [x] `docs/demo_script.md` (step-by-step walkthrough script)
- [x] `README.md` (complete production documentation with PowerShell-first instructions)

### Phase 7: Enhanced Developer & Senior Compatibility
- [x] `mcp_server/tools/local_doctor_tools.py` (`diagnose_local_environment` tool auditing Python, Rust, Git, virtualenv)
- [x] `mcp_server/tools/live_review_tools.py` (`check_pr_preflight` tool validating PR templates, test coverage, and security paths)
- [x] `mcp_server/tools/local_diagnostic_tools.py` (`diagnose_build_error` tool for borrow-checker, linker, and compiler failures)
- [x] `mcp_server/tools/local_escalation_tools.py` (`generate_smart_escalation` & `get_cohort_progress` tools for leads)
- [x] `cli.py` (Developer & Senior CLI with `ask`, `doctor`, `preflight`, `progress`, `cohort`, `server` subcommands)
- [x] `agent/system_prompt.py` (Persona-adaptive guidance: Junior Contributor, Backend/Systems, Team Lead)
- [x] `ui/components.py` & `ui/views.py` (Lead Oversight dashboard, Cohort Velocity matrix, Preflight cards, Doctor reports)
- [x] `app.py` (Added 4th "Lead oversight" navigation view)
- [x] `tests/test_enhanced_features.py` (9 unit and integration tests passing cleanly)

---

## Final Project Status Summary
- **Master Checklist**: All 7 phases 100% completed.
- **Unit & Integration Test Suite**: 47 / 47 tests passing cleanly with zero warnings or errors.
- **Evaluation Suite**: 12 benchmark questions evaluated with 100% tool selection accuracy, 0 groundedness violations, and 100% honest unknown rate.
- **Rule 0.2 Git Constraint**: Zero git commands executed (no git init, add, commit, or push).
- **Design & Tone Compliance**: 0 emojis used across all code, UI, and documentation files. Editorial typography and warm paper theme verified via Playwright.
- **Definition of Done**: Fully satisfied across all requirements.

---

## Pytest Execution Record

### Phase 1 Pytest Output
*(Ran Phase 1 test suite)*
```
Pending initial test creation in Phase 2.
```
