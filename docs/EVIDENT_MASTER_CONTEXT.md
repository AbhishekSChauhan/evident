# EVIDENT
## Evidence Engine For Hiring Decisions

Version: 1.0

---

# Vision

Hiring today is fundamentally broken.

Resumes are increasingly AI-generated.
Interview performance is highly variable.
Recruiters evaluate presentation quality instead of actual competence.

Most hiring systems answer:

"Does this person have the right keywords?"

They do not answer:

"Can this person actually do the job?"

Evident exists to solve this problem.

Our mission is:

Measure demonstrated competence instead of resume quality.

---

# Core Belief

Recruiters do not hire skills.

Recruiters hire confidence.

A hiring manager wants confidence that:

- this candidate can perform the job
- this candidate has solved similar problems before
- this candidate can operate independently
- this candidate can adapt when situations change

Resumes are weak signals.

Evidence is a strong signal.

Therefore:

Evident is an Evidence Engine for Hiring Decisions.

---

# The Fundamental Shift

Old World:

Resume
→ ATS
→ Keyword Match
→ Interview
→ Hire

New World:

Resume
→ Evidence Extraction
→ Evidence Graph
→ Competence Model
→ Job Fit
→ Hire

---

# What Is Evidence?

Evidence is a verifiable signal that demonstrates competence.

Examples:

Candidate claims:

"Built predictive models achieving 0.82 ROC-AUC"

Evidence:

- Diagnosed data leakage
- Found schema bug
- Corrected feature encoding
- Re-trained models
- Validated outputs

The claim is not valuable.

The evidence behind the claim is valuable.

---

# Core Product

Evident converts resumes into evidence.

Pipeline:

Resume
→ Claim Extraction
→ Evidence Collection
→ Competence Assessment
→ Evidence Graph
→ Job Matching
→ Hiring Decision Support

---

# Claim Extraction

Resume bullets are converted into claims.

Example:

"Reduced API latency from 1.2s to 180ms"

Claim:

Performance Optimization

Claim Type:

- Execution
- System Ownership
- Optimization

Each claim becomes assessable.

---

# Evidence Collection

The system conducts a forensic interview.

Goal:

Determine whether the candidate truly understands and performed the work.

Not:

- trivia
- leetcode
- theoretical testing

Instead:

Evidence gathering.

---

# Universal Competence Framework

Every profession can be measured using six dimensions.

These dimensions are intentionally domain-independent.

---

## 1. Knowledge

Definition:

Understanding how and why something works.

Evidence:

- Concepts
- Mental models
- Architecture understanding
- Domain expertise

Examples:

Engineer:
Explains cache invalidation.

Sales:
Explains sales cycle dynamics.

Marketer:
Explains attribution models.

Question:

"Why does this happen?"

---

## 2. Execution

Definition:

Ability to actually perform work.

Evidence:

- Actions taken
- Processes followed
- Deliverables produced

Question:

"What did you do?"

---

## 3. Problem Solving

Definition:

Ability to identify and resolve issues.

Evidence:

- Diagnosis
- Root cause analysis
- Resolution

Question:

"What went wrong and how did you fix it?"

---

## 4. Judgment

Definition:

Ability to make good decisions.

Evidence:

- Tradeoffs
- Prioritization
- Decision rationale

Question:

"Why did you choose that approach?"

---

## 5. Ownership

Definition:

What the candidate personally owned.

Evidence:

- Responsibilities
- Decision boundaries
- Accountability

Question:

"What was specifically your responsibility?"

---

## 6. Adaptability

Definition:

Ability to apply knowledge to new situations.

Evidence:

- Transfer learning
- Hypotheticals
- Scenario reasoning

Question:

"What would change if the environment changed?"

---

# Evidence Graph

The Evidence Graph is the core intellectual property.

Nodes:

- Claims
- Evidence
- Competence Dimensions
- Jobs
- Hiring Outcomes

Relationships:

Claim
→ supported by Evidence

Evidence
→ contributes to Competence

Competence
→ predicts Job Success

Job
→ requires Competence

Candidate
→ matched to Job

---

# Evidence Node Structure

Example:

Node:

Diagnosed Data Leakage

Type:

Problem Solving

Attributes:

- confidence
- source answer
- timestamp
- supporting quote

Links:

Claim:
"Built predictive model"

Dimension:
Problem Solving

Job Requirement:
Machine Learning

---

# Competence Score

Important:

Evident does NOT score communication.

Evident scores evidence.

The goal is:

Measure demonstrated competence.

Not:

Measure presentation quality.

---

# Coverage

Coverage measures:

How much evidence has been collected.

Example:

Knowledge:
100

Execution:
100

Problem Solving:
80

Judgment:
20

Ownership:
0

Adaptability:
0

Coverage:

4/6 dimensions explored

Meaning:

Candidate may be strong.

Evidence is incomplete.

---

# Coverage Gaps

Coverage Gap:

A competence dimension with insufficient evidence.

Example:

No ownership evidence.

We do NOT assume weakness.

We mark:

Unknown.

This is critical.

Unknown ≠ Bad

Unknown = Not Yet Proven

---

# Hiring Manager Output

Recruiters do not want scores.

Recruiters want evidence.

Evident provides:

## Resume Claim

Built predictive models achieving 0.82 ROC-AUC

---

## Evidence Found

Knowledge

- Detected data leakage risk
- Explained feature importance analysis

Execution

- Re-trained models
- Fixed schema issue

Problem Solving

- Diagnosed root cause
- Corrected upstream data issue

Judgment

- Refused to trust metrics before validation

Ownership

- Limited evidence collected

Adaptability

- Successfully generalized reasoning

---

## Recommendation

Strong evidence of machine learning competence.

Highest confidence:

- Knowledge
- Execution
- Problem Solving

Coverage gap:

- Ownership

---

# Long-Term Vision

Phase 1

Evidence-Based Screening

Resume
→ Evidence

---

Phase 2

Evidence-Based Search

Recruiters search:

"Find backend engineers who have personally solved scaling issues above 1M requests/day."

Search runs on evidence.

Not keywords.

---

Phase 3

Evidence-Based Matching

Jobs become:

Required evidence profiles.

Candidates become:

Evidence graphs.

Matching becomes graph-to-graph.

---

Phase 4

Hiring Intelligence Layer

Evident learns:

Evidence
→ Interview Outcome

Evidence
→ Offer

Evidence
→ Hire

Evidence
→ Promotion

Evidence
→ Retention

Evidence
→ High Performance

The graph becomes predictive.

---

# Ultimate Goal

Become the competence layer of hiring.

Not:

Resume database.

Not:

ATS.

Not:

Interview platform.

Instead:

The system of record for evidence-backed hiring decisions.



# EVIDENT

## One-line definition

Evident is an Evidence Engine for Hiring Decisions.

## Mission

Help recruiters and hiring managers make hiring decisions
based on demonstrated evidence rather than resumes,
keywords, credentials, or interview performance alone.

## Core Insight

Recruiters do not hire skills.

Recruiters hire confidence that a candidate can perform
the job successfully.

Resumes contain claims.

Hiring decisions require evidence.

Evident converts claims into evidence.

## Long-Term Vision

Become the world's largest structured repository of
workplace competence evidence.

Not a candidate database.

Not a resume database.

An evidence database.


## Implementation Audits

The following documents are considered implementation-reality references.

They describe what is actually implemented in the codebase and may differ from the intended architecture.

- docs/STATE_MACHINES.md
- docs/ARCHITECTURE_LAYER_AUDIT.md

When architectural discussions arise, consult these documents before proposing new features or refactors.

If an audit conflicts with a design document, surface the conflict explicitly.

The planner's objective is not to complete moves.

The planner's objective is to maximize evidence gained per question.