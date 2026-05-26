# Hermes SKILL.md — Frontmatter Schema

> Draft v0.1 | Generated from skill-enricher gap analysis  
> Feedback welcome: patch this file directly

This document defines the **canonical frontmatter fields** for Hermes SKILL.md files.
Both human authors and the `skill-enricher.py` pipeline write against this schema.

---

## Guiding Principles

| Principle | Rationale |
|-----------|-----------|
| **Declare intent, not implementation** | `upstream_skills` says what feeds this skill; don't hard-code tool calls |
| **Hard constraints first** | `trigger_conditions` + `antagonist` are boolean gates — if true, skill is inapplicable |
| **Composability before automation** | `composes_with` enables workflow chaining before `skill-enricher` has to infer it |
| **Verification signals optional** | `verified`, `tested_against` are quality gates; authors should fill them in as they validate |
| **Complexity is multi-dimensional** | `complexity` (high/medium/low) is author-assigned; `step_count` + `pitfalls_count` are extracted |

---

## Required Fields

These four fields are the minimum viable skill declaration.

```yaml
---
name: my-skill              # unique kebab-case identifier
category: devops            # primary namespace (arbitrary string, not enforced)
description: >-             # one-paragraph plain-language description
  What this skill does and when to reach for it.
tags:                       # flat keyword list for graph edges + discovery
  - deployment
  - docker
trigger_conditions:         # free-text conditions that activate this skill
  - "use when the user asks to build a Docker Compose stack"
  - "use when deploying to a Linux host over SSH"
---
```

---

## Strongly Recommended

These fields make the graph useful for composition and quality filtering.

```yaml
---
# ── Workflow topology ──────────────────────────────────────────────
upstream_skills:            # skills that typically run before this one
  - github-pr-workflow       # bare name, no namespace prefix needed
  - code-review

downstream_skills:          # skills that typically run after this one
  - github-code-review
  - canary-watch

composes_with:              # skills that form a natural pair or bundle
  - github-pr-workflow      # → enricher generates bundle edges
  - github-code-review

antagonist:                 # skills that should NOT be used together
  - grapoi-fork             # (example) — conflicting approaches

# ── Delivery contract ───────────────────────────────────────────────
workflow_role: worker       # role in a composition chain
                             # values: orchestrator | generator | reviewer |
                             #         researcher | scheduler | migrator | worker

inputs:                     # what this skill expects as input
  - repo_url: string
  - branch: string

outputs:                    # what this skill produces as output
  - deployed_url: string
  - logs: string

output_artefacts:           # concrete files/URLs produced (for graph artefact scoring)
  - https://github.com/{org}/{repo}/releases/tag/{version}
  - deploy-report.md

# ── Quality signals ───────────────────────────────────────────────
confidence: high            # author's confidence in the skill
                             # values: high | medium | low
                             # Also settable by enricher from verified + has_examples

verified: true              # boolean — has the author tested this end-to-end?
tested_against:             # explicit list of environments/platforms tested
  - hermes-agent v0.12
  - Ubuntu 24.04
  - Claude Code CLI

# ── Complexity ────────────────────────────────────────────────────
complexity: medium          # override of inferred complexity
                             # values: high | medium | low
                             # Optional — enricher infers this; author override wins

pitfalls:                   # explicit pitfalls section replaces regex extraction
  - id: docker-network
    severity: high
    description: "Docker Compose networks must be shared across containers"
  - id: ssh-key-perms
    severity: medium
    description: "ssh private keys must be chmod 600"
---
```

---

## Optional Fields

These are for advanced use cases and can be added without breaking existing tools.

```yaml
---
# ── Author / provenance ────────────────────────────────────────────
author: Jane Smith
version: "1.2.0"
maintainer: jane@example.com

# ── I/O contract (advanced) ───────────────────────────────────────
input_schema:               # JSON Schema for structured inputs
  type: object
  properties:
    repo_url:
      type: string
      format: uri
    branch:
      type: string
      default: main

output_schema:
  type: object
  properties:
    deployed_url:
      type: string

# ── Inter-skill communication ─────────────────────────────────────
delivery_contract:          # how this skill passes state to downstream skills
  via: memory               # values: memory | file | cron | none
  key: "last_deploy_result"

# ── Discovery ──────────────────────────────────────────────────────
related_skills:             # soft links for sidebar / "see also" rendering
  - github-auth
  - canary-watch

provider: openclaw          # which agent system ships this skill

# ── Experimental ──────────────────────────────────────────────────
experimental: false         # if true, skill-enricher adds ⚠️ badge to graph node
```

---

## Field Reference Table

| Field | Type | Required | Inferred | Enricher-settable | Notes |
|-------|------|----------|----------|-------------------|-------|
| `name` | string | ✅ | — | — | kebab-case, unique |
| `category` | string | ✅ | — | ✅ | empty → namespace dir used |
| `description` | string | ✅ | — | — | |
| `tags` | string[] | ✅ | — | ✅ | empty → extracted from body |
| `trigger_conditions` | string[] | — | ✅ | ✅ | |
| `upstream_skills` | string[] | — | — | ✅ | bare name |
| `downstream_skills` | string[] | — | — | ✅ | bare name |
| `composes_with` | string[] | — | — | ✅ | bare name |
| `antagonist` | string[] | — | — | ✅ | bare name |
| `workflow_role` | enum | — | ✅ | ✅ | 7 values |
| `inputs` / `outputs` | any[] | — | — | ✅ | free-form |
| `output_artefacts` | string[] | — | ✅ | ✅ | |
| `confidence` | enum | — | ✅ | ✅ | high/medium/low |
| `verified` | bool | — | — | ✅ | |
| `tested_against` | string[] | — | — | ✅ | |
| `complexity` | enum | — | ✅ | ✅ | high/medium/low |
| `author` / `version` | string | — | — | ✅ | |
| `experimental` | bool | — | — | ✅ | |
| `related_skills` | string[] | — | — | ✅ | |
| `provider` | string | — | — | ✅ | |

---

## Enricher Override Rules

When the same field exists in frontmatter AND can be inferred by the enricher,
the frontmatter value wins (author intent > algorithmic inference).

| Field | Frontmatter wins if | Enricher wins if |
|-------|--------------------|-----------------|
| `category` | non-empty string | `""` (empty) |
| `workflow_role` | non-empty | enricher heuristic |
| `complexity` | non-empty | enricher heuristic |
| `tags` | non-empty array | `[]` |

---

## Gap Detection (future enricher features)

These fields are **not yet produced by `skill-enricher.py`** but would enable
powerful graph queries if added to the schema and populated:

| Field | Detection method | Enables |
|-------|-----------------|---------|
| `confidence` | weighted: `verified × 0.4 + has_examples × 0.3 + tested_against.length × 0.1 + has_pitfalls × 0.2` | Filter by trust level |
| `delivery_contract` | look for `memory`, `state`, `CRUD` keywords | Inter-skill state passing edges |
| `output_artefacts` | already extracted via regex — just needs surfacing in schema | Artefact-type edges |
| `composes_with` | mutual co-mention with other skills | Bundle edges (stronger than same-tag) |
| `antagonist` | manual only | Negative edges (never draw these together) |
