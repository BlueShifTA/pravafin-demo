# 2. Workflow Orchestration

**How we work** — Core principles for effective execution in startup teams

---

## Planning & Verification

### 1. Plan Mode Default ✅
- **When:** ANY non-trivial task (3+ steps or architectural decisions)
- **How:** Write detailed specs upfront to reduce ambiguity
- **If blocked:** Stop immediately, don't keep pushing
- **Verify before building:** Run specs by peers; refine if unclear

### 2. Subagent Strategy
- Use background workers liberally for research, exploration, parallel analysis
- Keep main context window clean (don't load everything at once)
- For complex problems: throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- **After ANY correction from peers:** Update your playbooks and lessons file
- **Pattern recognition:** If you make the same mistake twice, it's a rule you need
- **Iterate ruthlessly:** Review lessons at session start; apply learning to new work

### 4. Verification Before Done ✅
- **Never mark complete without proof:** Must show logs, tests, or live demo
- **Diff behavior:** Show what changed vs. baseline
- **Staff engineer standard:** "Would a senior engineer approve this?"
- **Autonomous bug fixing:** When you spot errors, fix them. Don't hand off broken work.

### 5. Demand Elegance (Balanced)
- **Simple fixes:** Don't over-engineer
- **Non-trivial changes:** Pause and ask "is there a more elegant way?"
- **Known patterns:** If you understand the landscape, implement the clean solution
- **Skip this for:** Quick wins and obvious fixes

### 6. Autonomous Bug Fixing
- **You own it:** Don't ask for hand-holding
- **Follow the evidence:** Logs → errors → root cause → fix
- **CI integration:** Make failing tests pass without context-switching

---

## Task Management

1. **++Plan First++:** Write plan to `tasks/todo.md` with checkable items
2. **++Verify Plan++:** Check assumptions in before starting implementation
3. **++Track Progress++:** Mark items complete as you go
4. **++Explain Changes++:** High-level summary at each major step
5. **++Document Results++:** Add review section to `tasks/todo.md`
6. **++Capture Lessons++:** Update `tasks/lessons.md` after corrections

---

## Core Principles

- **++Simplicity First++:** Every change as simple as possible. Minimal impact code.
- **++No Laziness++:** Find root causes. No temporary fixes. Senior developer standards.
- **++Minimal Impact++:** Changes should only touch what's necessary. Avoid introducing bugs.

---

## Guardrails for Startup Teams

✅ **Plan mode is default** — specs prevent expensive rework
✅ **Subagents offload research** — main context stays focused
✅ **Self-correction is automatic** — lessons prevent repeated mistakes
✅ **Verification gates shipping** — no "works for me" handoffs
✅ **Elegance is expected** — but not at the cost of shipping
✅ **Bugs are owned, not delegated** — autonomous problem-solving

---

## Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| Mistakes per sprint | < 2 | Feedback loop is tight |
| Avg time to fix | < 1 hour | Root cause discipline |
| Plan → Ship time | 3-5 days | Specs prevent rework |
| Code review notes | 1-2 per PR | High initial quality |
| Peer corrections | < 1 per week | Learning is applied |
