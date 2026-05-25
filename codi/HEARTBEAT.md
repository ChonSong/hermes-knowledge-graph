# HEARTBEAT.md

## Periodic Tasks for Codi

Rotate through these checks 2-4 times per day:

### Code Library Health

1. **Check for new commits** in code-library/ (git log --oneline -5)
2. **Verify modules are importable** - spot check 2-3 modules with `python -c "import module"`
3. **Validate CODE_INDEX.md** - spot check line counts match actual files (wc -l)

### Memory Maintenance

- Update `memory/YYYY-MM-DD.md` with significant events
- Periodically consolidate notes into MEMORY.md

## When to Report

- New commits found in code-library/
- Import errors detected
- Line counts don't match in CODE_INDEX.md
- It's been >8h since last activity

## When to Stay Quiet (HEARTBEAT_OK)

- Late night (23:00-08:00) unless urgent
- Nothing new since last check
- Just checked <30 minutes ago