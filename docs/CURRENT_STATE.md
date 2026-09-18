# Evident — Current State & Architecture Roadmap

Version: 1.0  
Date: September 2026  
Source of Truth Reference: [EVIDENT_MASTER_CONTEXT.md](file:///Users/212705/ProofScreen/docs/EVIDENT_MASTER_CONTEXT.md)

---

# 1. What Exists Today

The following components are fully implemented, covered by automated test suites (**532 tests passing cleanly**), and operational in the codebase:

### A. Resume Parsing & Normalization
- **File**: `api/ingest/parse.py`
- Ingests PDF, DOCX, TXT, and Markdown files. Normalizes whitespace, extracts clean text, strips headers, and handles encoding.

### B. Taxonomy-Typed Claim Extraction (LLM #1)
- **Files**: `api/engine/extract.py`, `api/taxonomy.py`
- Extracts up to 3 candidate claims typed against 8 domain job families (`bpo_operations`, `software_engineering`, `product_management`, `customer_support`, `sales_business_dev`, `digital_marketing`, `data_analytics`, `hr_recruitment`) plus `general`.
- Applies claim strength heuristics, order index, and metric parsing.

### C. WhatsApp Question Planner & Python Validator (LLM #2 + Pure Python)
- **Files**: `api/engine/question.py`, `api/engine/question_eval.py`
- Adaptive 5-level probe ladder (`OPERATING_CONTEXT` $\rightarrow$ `DEEP_DIVE` $\rightarrow$ `PERTURB` $\rightarrow$ `TRANSFER`).
- **7-Rule Pure Python Validator**: Evaluates every generated question deterministically for `answer_leakage`, `duplicate_content`, `multiple_fact_targets`, `hypothetical_misuse`, `unsupported_metric`, `scope_drift`, `no_claim_anchor`.
- Enforces a 1-regeneration cap with instant heuristic fallback (`AGENTS.md` Rule 5).
- **Binary Quality Evaluator**: Computes low-variance pass/fail flags (`has_concrete_anchor`, `is_single_ask`, `is_jargon_free`, `is_claim_echo_clean`, `binary_pass`).

### D. WhatsApp Candidate Channel & Conversational Engine
- **Files**: `api/channels/whatsapp_cloud.py`, `api/stt.py`, `api/routers/whatsapp.py`
- Meta Cloud API integration with webhook signature verification (`X-Hub-Signature-256`), idempotent message retry de-duplication (`provider_message_id`), 24-hour service window tracking, and Whisper audio transcription for voice notes.
- **Memory Exhaustion Steering**: Detects candidate skip/don't-know responses ("I don't know", "Not sure", "Skip"), bypasses repair turns, and advances planner with warm human acknowledgements (`"That's okay."`, `"Makes sense."`).

### E. Evidence Signal & Fact Extraction with Verbatim Enforcement (LLM #3 + Pure Python)
- **Files**: `api/engine/evidence.py`, `api/engine/consistency.py`
- Extracts countable signals (quantities, process steps, causal links, tool usage, incident markers, constraints) and facts.
- **Rule 4 (`enforce_verbatim()`)**: Pure Python quote verification drops any signal whose quote is not literally present in the candidate's response.
- **Fact Consistency Engine**: Evaluates fact memory across stable vs variable keys to compute a deterministic session consistency multiplier ($0.40$ to $1.0$).

### F. Universal Competence Model & Scoring Engine
- **Files**: `api/engine/signals.py`, `api/engine/scoring.py`, `api/engine/graph.py`
- Converts countable signals into 6 domain-independent dimension scores:
  1. **Knowledge** (understanding how/why things work)
  2. **Execution** (performing operational work; troubleshooting weighted 1.5x)
  3. **Problem Solving** (diagnosing outages and root causes)
  4. **Judgment** (trade-off evaluations and decisions)
  5. **Ownership** (taking responsibility; inferred from first-person operational verbs)
  6. **Adaptability** (transfer reasoning under perturbation)
- Applies published recruiter role weight profiles and consistency multiplier. **Rule 1**: The LLM never produces a score; Python turns counts into numbers.

### G. Evaluation Integrity, Replay, & Tenant Isolation (D6–D10)
- **Files**: `api/engine/evaluation.py`, `api/engine/provenance.py`, `api/engine/replay.py`, `api/tenancy.py`
- **D6 Evaluation Entity**: Immutable finalized evaluation records.
- **D7 Provenance**: Content-hashes taxonomy (`tax_1`), rubrics, scoring formula, prompts, and code version into `evaluation_version = evx_sha256(material)[:16]`.
- **D8 Replay**: 100% offline re-evaluation engine from recorded evidence with zero LLM network calls.
- **D9 Multi-Tenancy**: Scoped isolation across 15 database tables.
- **D10 Candidate Outcomes**: Audit trail recording hiring manager decisions (`hired`, `rejected`, `interviewed`).

### H. Job Fit Matching Engine
- **Files**: `api/engine/job_fit.py`, `api/engine/job_requirements.py`, `api/routers/job_fit.py`
- Extracts job requirements from job descriptions and verifies coverage against candidate claims, QA turns, and dimension profiles to compute raw `job_fit_score`, `skill_fit`, `competence_fit`, verified requirements, and risk area notes.

### I. Evaluation AI Evals & Diagnostic Tools
- **Files**: `api/engine/trajectory_eval.py`, `tests/test_eval_regression.py`, `scripts/review_traces.py`
- Trajectory evaluator for ladder progression and saturation reachability.
- Replay regression harness ensuring zero-drift score reproducibility.
- CLI trace reviewer for end-to-end error analysis.

---

# 2. What Is Partially Built

The following components are prototyped, functional in core API endpoints, but await frontend integration or scale data:

1. **Evidence Graph Storage Model**
   - **Current State**: Compiled in-memory as `CandidateGraph` Pydantic schemas (`api/schemas.py`) and returned via `/api/recruiter/candidates/{id}`.
   - **Gap**: Not yet stored in a dedicated graph database (e.g., Neo4j or Postgres `pgvector` nodes) for cross-session traversal.

2. **Recruiter Dashboard**
   - **Current State**: FastAPI backend endpoints (`/api/recruiter/*`, `/api/job-fit/*`) are complete and serve structured JSON responses.
   - **Gap**: The Next.js recruiter frontend dashboard is a separate application consuming `/openapi.json`.

3. **Outcome Feedback Optimization Loop**
   - **Current State**: `candidate_outcomes` database table records recruiter decisions (`hired`, `rejected`, `interviewed`, `offered`, `promoted`, `retained`) with `evaluation_id` pointers.
   - **Gap**: Automated rubric/weight recalibration loops are designed and waiting for production dataset volume ($n \ge 30$).

---

# 3. What Is Designed But Not Built

The following features are specified in the long-term vision ([EVIDENT_MASTER_CONTEXT.md](file:///Users/212705/ProofScreen/docs/EVIDENT_MASTER_CONTEXT.md)) but not yet implemented in code:

1. **Evidence-Based Natural Language Search (Phase 2 Vision)**
   - Query engine allowing recruiters to search: *"Find backend engineers who personally resolved database deadlocks under > 50k QPS."*
   - Requires vector indexing over extracted verbatim evidence quotes.

2. **Cross-Session Candidate Graph Aggregation**
   - Merging multiple interview sessions across different roles or time periods into a unified, evolving candidate evidence profile.

3. **ATS Two-Way Sync Integrations**
   - Automated triggers to ingest candidates from Greenhouse / Lever / Workday and push back evidence cards and fit scores.

4. **Predictive Outcome Hiring Models (Phase 4 Vision)**
   - Machine learning models linking pre-hire evidence graph nodes to post-hire performance, promotion, and retention metrics.

---

# 4. What We Need To Ship For MVP

To launch Evident as a commercial production product with initial customers:

| Feature / Requirement | Category | Target Completion |
|---|---|---|
| **Recruiter Dashboard Frontend Integration** | UI/UX | High Priority |
| **Authentication & User Role Management** | Security | High Priority (Move from single tenant key to JWT/OAuth per recruiter) |
| **ATS Webhook Ingestion (Greenhouse/Lever)** | Integration | High Priority |
| **Candidate Interview Self-Scheduling via WhatsApp** | Candidate Experience | Medium Priority |
| **Exportable Candidate Evidence PDF Summaries** | Recruiter Workflow | Medium Priority |
| **Evidence Vector Indexing (`pgvector`)** | Search/Matching | Medium Priority |

