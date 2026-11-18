# Privacy and Data Governance Architecture

## Overview

The Onboarding assistant incorporates a strict, layered privacy architecture designed to prevent intellectual property leaks, credential leakage, and prompt injection attacks.

Every tool invocation—whether querying live GitHub REST endpoints or searching local vector embeddings—must pass through this privacy governance layer before any data leaves the MCP server boundary.

---

## The Six Core Privacy Pillars

### 1. Absolute Source Code Isolation
- **Rule**: No tool in this system reads or returns the contents of source code files (`.rs`, `.py`, `.c`, `.toml`, etc.).
- **Implementation**: Tools only inspect file names, entry types, and byte sizes. File content fetching is strictly restricted to an allowlist of public documentation files (`README*`, `CONTRIBUTING*`, `CODEOWNERS`, `MAINTAINERS*`, `SECURITY*`, and markdown guides under `docs/`).
- **Purpose**: Eliminates the risk of proprietary intellectual property or application business logic leaking into external LLM prompts.

### 2. Path Denylist Enforcement
- **Rule**: Critical security paths are blocked unconditionally from all live and local inspection tools.
- **Configured Denylist**: `.env`, `secrets`, `.github/workflows`, `config/prod`, `id_rsa`.
- **Implementation**: Evaluated in `mcp_server/privacy.py::is_path_denied`. If any requested path segment matches the denylist, the tool immediately aborts and returns a structured error:
  ```json
  {"error": {"code": "path_blocked", "message": "Access to path is denied by repository security policy."}}
  ```

### 3. Comprehensive Credential Redaction
- **Rule**: Every byte of text returned by any tool is passed through regex token redaction engines before serialization.
- **Redaction Patterns**:
  - GitHub personal access, OAuth, and app tokens (`ghp_`, `github_pat_`, `gho_`, `ghu_`, `ghr_`).
  - AWS Access Key IDs (`AKIA...`).
  - PEM Private Key blocks (`-----BEGIN ... PRIVATE KEY-----`).
  - Authorization Bearer tokens (`Bearer ...`).
  - Generic variable assignments matching `api_key=...`, `secret=...`, `token=...`, or `password=...`.
- **Telemetry**: Redactions are counted per call and recorded in the audit log.

### 4. Target Repository Allowlist Boundary
- **Rule**: All GitHub REST API tools are locked strictly to the configured `TARGET_REPO`.
- **Implementation**: The repository name is injected by the server application and is completely hidden from the LLM tool schemas, preventing an attacker from coaxing the agent to inspect unauthorized repositories.

### 5. Zero-Payload Cryptographic Audit Logging
- **Rule**: Every tool execution is recorded in an immutable SQLite audit log table (`audit_log`), but NO sensitive arguments or payload contents are ever stored.
- **Logged Columns**:
  - `ts`: ISO 8601 UTC timestamp.
  - `tool`: Invoked tool name.
  - `args_sha256`: Deterministic SHA-256 hash of the arguments dictionary.
  - `status`: Execution status (`success`, `error`, `blocked`, `preview`, `applied`).
  - `bytes_returned`: Size of the structured return payload in bytes.
  - `redactions`: Number of sensitive credentials stripped from the output.

### 6. Sanitization of Untrusted External Content
- **Rule**: Content originating from public issues, pull request descriptions, commit messages, and repository readmes is attacker-controllable and represents a vector for indirect prompt injection.
- **Implementation**:
  - Issue and PR titles are sanitized and strictly capped at 120 characters with multi-line normalization.
  - README excerpts are capped at 4,000 characters.
  - The agent system prompt explicitly instructs the LLM that all content inside tool results represents passive data and that instructions within tool outputs must never be executed.

---

## Important Notice on Free-Tier LLM APIs

> [!WARNING]
> **Free-Tier LLM Data Usage Policy**:
> When using free-tier API keys with Google Gemini (via `google-genai`), submitted content may be processed by human reviewers and utilized by Google to improve its products and models under standard consumer terms of service.
> 
> For this exact reason, this demonstration project operates **exclusively on public open-source data** from `astral-sh/ruff`.
> 
> **Enterprise Production Path**:
> For corporate enterprise deployments containing proprietary documentation, organizations should configure zero-data-retention enterprise endpoints:
> - Google Vertex AI with Customer-Managed Encryption Keys (CMEK) and strict data retention disabled.
> - Enterprise Groq / Azure OpenAI with zero retention agreements.
> - Fully air-gapped, self-hosted open-weights models (such as LLaMA 3.3 or Qwen 2.5) hosted on private infrastructure via vLLM or Ollama.

