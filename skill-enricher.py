#!/usr/bin/env python3
"""
skill-enricher: Extract rich metadata from Hermes SKILL.md files.
Generates an enriched skill graph JSON with structural, semantic, and workflow metadata.
Run: python skill-enricher.py [--output graph.json]
"""

import os
import re
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

SKILLS_DIR = Path.home() / ".hermes" / "skills"
OUTPUT_PATH = Path(__file__).parent / "enriched-skills-graph.json"

# ── Metadata extractors ───────────────────────────────────────────────────────

def extract_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter block."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}
    import yaml
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}

def extract_trigger_conditions(content: str) -> list[str]:
    """Find trigger/condition signals: 'when...', 'use when...', '[trigger]' patterns."""
    triggers = []
    patterns = [
        r"(?i)(?:use|activate|trigger|load)\s+(?:when|if|for)\s+([^\n.]{5,60})",
        r"\[trigger[:\s]+([^\]]{3,50})\]",
        r"trigger.*?(?:when|if)[:\s]+([^\n]{5,60})",
    ]
    for pat in patterns:
        for m in re.finditer(pat, content):
            t = m.group(1).strip().strip('"\'.,')
            if len(t) > 4:
                triggers.append(t)
    return list(set(triggers))

def extract_tools_mentioned(content: str) -> list[str]:
    """Find tool references: terminal(), write_file(), delegate_task(), etc."""
    tools = re.findall(r"(?<!\w)(terminal|write_file|patch|read_file|search_files|delegate_task|cronjob|skill_view|skill_manage|clarify|text_to_speech|session_search|memory|todo|execute_code|process|vision_analyze|batch_add)\s*(?=\()", content)
    return list(set(tools))

def extract_dependencies(content: str) -> list[str]:
    """Find skill dependencies: skill_view, other skill names referenced."""
    skill_refs = re.findall(r"skill_view\s*\(\s*['\"]?([a-zA-Z0-9_-]+)['\"]?\s*\)", content)
    return list(set(skill_refs))

def extract_code_examples(content: str) -> int:
    """Count fenced code blocks."""
    return len(re.findall(r"```[\w]*\n.*?```", content, re.DOTALL))

def extract_steps_count(content: str) -> int:
    """Count numbered steps and explicit step markers."""
    steps = re.findall(r"(?:^|\n)\s*\d+[.)]\s+", content)
    return len(steps) if steps else 0

def extract_pitfalls_count(content: str) -> int:
    """Count distinct pitfalls/warnings."""
    pitfalls = re.findall(r"(?i)(?:pitfall|warning|caution|gotcha|risk|don'?t|n'?t\s+(?:use|do|run)[:\s])", content)
    return len(pitfalls)

def extract_complexity_score(content: str) -> str:
    """Infer skill complexity from content features."""
    lines = content.lower()
    code_blocks = len(re.findall(r"```[\w]*\n.*?```", content, re.DOTALL))
    steps = len(re.findall(r"(?:^|\n)\s*\d+[.)]\s+", content))
    terms = sum([
        re.search(r"fork|pull|merge|rebase", lines),
        re.search(r"docker|kubernetes|container", lines),
        re.search(r"api|endpoint|rest|graphql", lines),
        re.search(r"database|sql|postgres|mongo", lines),
        re.search(r"llm|model|token|prompt", lines),
        re.search(r"auth|oauth|jwt|token", lines),
    ] is not None for _ in [1])
    score = code_blocks * 0.3 + steps * 0.5 + terms
    if score >= 8:
        return "high"
    elif score >= 4:
        return "medium"
    return "low"

def extract_output_artefacts(content: str) -> list[str]:
    """Find file paths, URLs, or output formats mentioned."""
    out = []
    out.extend(re.findall(r"[\w/._-]+\.(?:json|yaml|md|sh|py|toml|html|css|js|tsx|sql)", content))
    out.extend(re.findall(r"https?://[^\s<>'\"]{10,100}", content))
    return list(set(out))

def suggest_compose(goal: str, skills: list[dict], top_k: int = 8) -> list[dict]:
    """
    Given a free-text goal, walk the enriched skill graph and propose
    a ranked chain of skills that best address it.

    Scoring dimensions (each 0–1):
      - tag_match   : fraction of goal keywords found in skill tags
      - desc_match  : keyword overlap with skill description
      - role_fit    : workflow_role suitability for goal type
      - complexity  : medium/high complexity suited for multi-step goals
      - tools_avail : how many skill tools are commonly available
      - artefact    : output_artefacts match goal intent

    Returns a list of {rank, skill_name, score, justification, chain_position}.
    """
    import yaml  # already imported in extract_frontmatter; keep local for perf
    goal_lower = goal.lower()
    goal_keywords = set(re.findall(r"[a-z]{4,}", goal_lower))

    # ── Role suitability map ──────────────────────────────────────────
    GOAL_TYPE_KEYWORDS = {
        "orchestrator": ["plan", "orchestrate", "manage", "coordinate", "delegate",
                         "break down", "decompose", "multi-step", "workflow"],
        "generator":    ["generate", "create", "build", "write", "design", "implement",
                         " scaffold", "new project"],
        "reviewer":     ["review", "audit", "check", "fix", "debug", "refactor",
                         "improve", "test", "validate", "verify"],
        "researcher":   ["research", "find", "search", "explore", "discover", "analyze",
                         "summarize", "gather"],
        "scheduler":    ["schedule", "periodic", "cron", "remind", "automate", "monitor"],
        "migrator":     ["migrate", "port", "convert", "rewrite", "upgrade"],
    }
    def goal_role(goal: str) -> list[str]:
        scored = []
        for role, keywords in GOAL_TYPE_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in goal_lower)
            scored.append((role, hits))
        scored.sort(key=lambda x: -x[1])
        return [r for r, _ in scored[:3]]

    preferred_roles = goal_role(goal)

    # ── Per-skill scoring ─────────────────────────────────────────────
    results = []
    for s in skills:
        tag_match   = len(goal_keywords & set(w.lower() for w in s.get("tags", []))) / max(len(s.get("tags", [])), 1)
        desc_words  = set(re.findall(r"[a-z]{4,}", s.get("description", "").lower()))
        desc_match  = len(goal_keywords & desc_words) / max(len(goal_keywords), 1)
        role_fit    = 1.0 if s["workflow_role"] in preferred_roles else 0.3
        complexity  = 1.0 if s["complexity"] in ("high", "medium") else 0.2

        # tools match — higher when skill uses common tools
        COMMON_TOOLS = {"terminal", "write_file", "read_file", "patch", "delegate_task",
                        "search_files", "cronjob", "skill_view", "skill_manage", "execute_code"}
        skill_tools  = set(s.get("tools_used", []))
        tools_score  = len(skill_tools & COMMON_TOOLS) / max(len(skill_tools), 1) if skill_tools else 0.5

        # output artefact signal
        artefact_score = 0.0
        ARTIFACT_SIGNALS = {
            "json":  ["json", "api", "data"],
            "md":    ["document", "readme", "spec", "plan"],
            "py":    ["script", "automation", "pipeline"],
            "sh":    ["deploy", "setup", "install"],
            "html":  ["frontend", "ui", "web", "dashboard"],
        }
        for art in s.get("output_artefacts", []):
            for ext, signals in ARTIFACT_SIGNALS.items():
                if f".{ext}" in art and any(sig in goal_lower for sig in signals):
                    artefact_score = 0.7
                    break

        # weighted composite
        score = (
            tag_match   * 0.15 +
            desc_match  * 0.20 +
            role_fit    * 0.25 +
            complexity  * 0.10 +
            tools_score * 0.10 +
            artefact_score * 0.10 +
            (1.0 if s.get("has_examples") else 0.0) * 0.05 +
            (1.0 if s.get("verified") else 0.0) * 0.05
        )

        # justification string
        hit_tags = list(goal_keywords & set(w.lower() for w in s.get("tags", [])))[:4]
        reasons = []
        if hit_tags:
            reasons.append(f"tags [{', '.join(hit_tags)}]")
        if desc_match > 0.1:
            reasons.append(f"description matches goal")
        if role_fit > 0.5:
            reasons.append(f"role={s['workflow_role']} fits goal")
        if s.get("has_pitfalls_defined"):
            reasons.append("has pitfalls guidance")
        if s.get("has_examples"):
            reasons.append("has examples")

        results.append({
            "skill_name":      s["name"],
            "qualified_name":  s.get("qualified_name", s["name"]),
            "score":           round(score, 3),
            "workflow_role":   s["workflow_role"],
            "complexity":      s["complexity"],
            "tag_match":       round(tag_match, 2),
            "desc_match":      round(desc_match, 2),
            "role_fit":        round(role_fit, 2),
            "justification":  "; ".join(reasons) if reasons else "general purpose",
        })

    results.sort(key=lambda x: -x["score"])

    # ── Chain sequencing for complex goals ────────────────────────────
    # Simple goal → top single skill. Complex goal → sequence by role.
    is_complex = len(goal_keywords) >= 5 or any(kw in goal_lower for kw in [
        "multi", "workflow", "chain", "pipeline", "sequence", "end-to-end", "full-stack"
    ])

    chains = []
    if is_complex:
        # Build a role-ordered chain: orchestrator → researcher → generator → reviewer
        ROLE_ORDER = ["orchestrator", "researcher", "generator", "worker", "reviewer"]
        used_names = set()
        for role in ROLE_ORDER:
            candidates = [r for r in results if r["workflow_role"] == role and r["skill_name"] not in used_names]
            if candidates:
                top = candidates[0]
                top["chain_position"] = role
                chains.append(top)
                used_names.add(top["skill_name"])
    else:
        # Single skill recommendation
        top = results[0]
        top["chain_position"] = results[0]["workflow_role"]
        chains.append(top)

    # Add rank
    for i, c in enumerate(chains):
        c["rank"] = i + 1

    return chains[:top_k]


def extract_workflow_role(content: str) -> str:
    """Classify skill workflow role from content keywords and tags."""
    tags = extract_frontmatter(content).get("tags", [])
    tags_lower = [t.lower() for t in tags]
    text = content.lower()

    if "orchestrator" in tags_lower or "delegation" in tags_lower:
        return "orchestrator"
    if "generator" in tags_lower or "creation" in tags_lower or "write" in tags_lower:
        return "generator"
    if "review" in tags_lower or "qa" in tags_lower or "testing" in tags_lower:
        return "reviewer"
    if "research" in tags_lower or "search" in tags_lower:
        return "researcher"
    if "monitoring" in tags_lower or "cron" in tags_lower:
        return "scheduler"
    if "migration" in tags_lower:
        return "migrator"
    if re.search(r"(?i)delegate[_task]|spawn|orchestrat|multi\\.agent|subagent", text):
        return "orchestrator"
    if re.search(r"(?i)write_file|write.*code|generate.*code|create.*file", text):
        return "generator"
    if re.search(r"(?i)review|test.*case|assert|verify.*output|critic", text):
        return "reviewer"
    if re.search(r"(?i)search.*web|web.*search|crawl|scrape|fetch.*url", text):
        return "researcher"
    if re.search(r"(?i)cron|schedule|periodic|every.*hour|every.*min", text):
        return "scheduler"
    if re.search(r"(?i)migrat|port.*to|convert.*code|rewrite", text):
        return "migrator"
    return "worker"


def extract_author_info(content: str) -> dict:
    """Extract author info from frontmatter and content."""
    fm = extract_frontmatter(content)
    author = fm.get("author", "")
    maintainer = fm.get("maintainer", "")
    version = fm.get("version", "")
    return {
        "author": author,
        "maintainer": maintainer,
        "version": version,
    }

def extract_quality_signals(content: str) -> dict:
    """Surface quality markers: examples, pitfalls, verified, testing info."""
    has_examples = bool(re.search(r"(?:example|for instance|e\.g\.|here:?s an example)", content, re.I))
    has_pitfalls = bool(re.search(r"(?i)(?:pitfall|warning|caution|gotcha)", content))
    has_testing = bool(re.search(r"(?i)(?:test|pytest|spec|verify)", content))
    has_verified = bool(re.search(r"(?i)(?:verified|tested|working)", content))
    has_seealso = "see also" in content.lower()
    return {
        "has_examples": has_examples,
        "has_pitfalls_defined": has_pitfalls,
        "has_testing_guidance": has_testing,
        "verified": has_verified,
        "has_crossrefs": has_seealso,
    }

def extract_skill_io(content: str) -> dict:
    """Parse inputs/outputs from frontmatter."""
    fm = extract_frontmatter(content)
    return {
        "inputs": fm.get("input", fm.get("inputs", [])),
        "outputs": fm.get("output", fm.get("outputs", [])),
    }

# ── Main enrichment ───────────────────────────────────────────────────────────

def enrich_skill(name: str, content: str) -> dict:
    fm = extract_frontmatter(content)
    return {
        # Identifiers
        "name": name,
        "qualified_name": name,   # namespace/name when available
        # Category
        "category": fm.get("category", "uncategorized"),
        # Tags
        "tags": fm.get("tags", []),
        # Description
        "description": fm.get("description", fm.get("description_short", "")),
        # Author/version
        **extract_author_info(content),
        # Workflow role
        "workflow_role": extract_workflow_role(content),
        # Structural metrics
        "complexity": extract_complexity_score(content),
        "code_examples": extract_code_examples(content),
        "step_count": extract_steps_count(content),
        "pitfalls_count": extract_pitfalls_count(content),
        "lines_of_content": len(content.splitlines()),
        # Skill I/O
        **extract_skill_io(content),
        # Semantic signals
        "trigger_conditions": extract_trigger_conditions(content),
        "tools_used": extract_tools_mentioned(content),
        "skill_dependencies": extract_dependencies(content[:2000]),  # limit scan
        "output_artefacts": extract_output_artefacts(content),
        # Quality
        **extract_quality_signals(content),
    }

def build_graph(skills_data: list[dict]) -> dict:
    """Build adjacency from co-category, co-tag, co-dependency edges."""
    by_cat = defaultdict(list)
    by_tag = defaultdict(list)
    dep_graph = defaultdict(list)

    for s in skills_data:
        by_cat[s["category"]].append(s["name"])
        for tag in s["tags"]:
            by_tag[tag].append(s["name"])
        for dep in s.get("skill_dependencies", []):
            dep_graph[s["name"]].append(dep)

# Same-category edges (deduped via set)
    same_cat_edges = set()
    for cat, members in by_cat.items():
        if len(members) < 2:
            continue
        for i, a in enumerate(members):
            for b in members[i+1:]:
                same_cat_edges.add((a, b) if a < b else (b, a))
    same_cat_edges = list(same_cat_edges)

    # Same-tag edges (deduped)
    same_tag_edges = set()
    for tag, members in by_tag.items():
        if len(members) < 2:
            continue
        for i, a in enumerate(members):
            for b in members[i+1:]:
                same_tag_edges.add((a, b) if a < b else (b, a))
    same_tag_edges = list(same_tag_edges)

    dep_edges = [(name, d) for name, deps in dep_graph.items() for d in deps]

    return {
        "same_category": same_cat_edges,
        "same_tag": same_tag_edges,
        "depends_on": dep_edges,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-dir", type=Path, default=SKILLS_DIR)
    ap.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = ap.parse_args()

    print(f"Scanning {args.skills_dir} ...")
    skills_data = []
    seen = 0

    for namespace_dir in args.skills_dir.iterdir():
        if not namespace_dir.is_dir():
            continue
        if namespace_dir.name in ("index-cache", "node_modules", ".git"):
            continue
        namespace = namespace_dir.name
        for skill_md in namespace_dir.glob("*/SKILL.md"):
            skill_name = skill_md.parent.name
            qualified = f"{namespace}/{skill_name}"
            content = skill_md.read_text()
            enriched = enrich_skill(skill_name, content)
            enriched["qualified_name"] = qualified
            enriched["namespace"] = namespace
            skills_data.append(enriched)
            seen += 1

    graph = build_graph(skills_data)
    result = {
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_skills": seen,
        "categories": sorted(set(s["category"] for s in skills_data)),
        "unique_tags": sorted(set(t for s in skills_data for t in s["tags"])),
        "skills": skills_data,
        "edges": graph,
        "stats": {
            "by_category": dict(sorted(defaultdict(int, **{
                cat: sum(1 for s in skills_data if s["category"] == cat)
                for cat in set(s["category"] for s in skills_data)
            }).items())),
            "avg_lines": round(sum(s["lines_of_content"] for s in skills_data) / max(len(skills_data), 1)),
            "complexity_breakdown": {
                c: sum(1 for s in skills_data if s["complexity"] == c)
                for c in ["high", "medium", "low"]
            },
            "skills_with_examples": sum(1 for s in skills_data if s.get("has_examples")),
            "skills_with_pitfalls": sum(1 for s in skills_data if s.get("has_pitfalls_defined")),
            "total_edges": {
                "same_category": len(graph["same_category"]),
                "same_tag": len(graph["same_tag"]),
                "depends_on": len(graph["depends_on"]),
            },
        },
    }

    args.output.write_text(json.dumps(result, indent=2))
    print(f"Written {seen} enriched skills → {args.output}")
    print(f"  Categories: {len(result['categories'])}")
    print(f"  Unique tags: {len(result['unique_tags'])}")
    print(f"  Same-category edges: {len(graph['same_category'])}")
    print(f"  Same-tag edges: {len(graph['same_tag'])}")
    print(f"  Dependency edges: {len(graph['depends_on'])}")

if __name__ == "__main__":
    main()
