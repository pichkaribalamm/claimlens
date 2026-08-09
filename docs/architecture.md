# ClaimLens Architecture

## System Overview

User
 │
 ▼
Orchestrator
 │
 ├─────────────┐
 ▼             ▼
Claim Parser   Technology Profiler
 │             │
 └──────┬──────┘
        ▼
 Search Planner
        ▼
 Search Service
        ▼
 Evidence Extractor
        ▼
 Evidence Verifier
        ▼
 Claim Mapper
        ▼
 Report Generator


 

 ## Responsibilities

### Claim Parser

Input

Claim Text

Output

List<ClaimElement>

### Technology Profiler

Input

Claim Text

Output

TechnologyProfile

### Search Planner

Input

Claim Element
Target Scope

Output

List<SearchQuery>

### Search Service

Input

SearchQuery

Output

SearchResult[]

### Evidence Extractor

Input

SearchResult

Output

Evidence[]

### Evidence Verifier

Input

Evidence[]

Output

VerifiedEvidence[]

### Claim Mapper

Input

ClaimElement
VerifiedEvidence[]

Output

ClaimMapping

### Report Generator

Input

ClaimMapping[]

Output

ClaimAnalysisReport


## Data Contracts

### Claim

Contains:

- Claim number
- Raw text

---

### ClaimElement

Contains:

- ID
- Parent claim
- Text
- Keywords (optional, later)

---

### TargetScope

Contains:

- Company
- Product
- Technology

---

### SearchQuery

Contains:

- Query
- Rationale
- Priority

---

### SearchResult

Contains:

- Title
- URL
- Snippet
- Source

---

### Evidence

Contains:

- Excerpt
- URL
- Title
- Confidence
- Source type

---

### ClaimMapping

Contains:

- Claim element
- Evidence
- Reasoning
- Confidence
