# PATTERNS.md — Engineering Behavioral & Technical Patterns

---

## Confirmed Patterns

### 1. Anti-Hallucination Protocol is Primary Directive
AI agents fabricate progress ("87% production-ready" with seeded data). Always validate end-to-end before signaling completion. "Code exists" ≠ "it works" — run it and prove it.

### 2. Pragmatic Solutions Beat Perfect Code
Compose working pieces rather than rebuilding from scratch. Prefer battle-tested solutions (subprocess wrappers, proven libraries) even if not custom-fit. "Compose working pieces > rebuild from scratch."

### 3. Memory Acts as Distributed State Machine
Daily logs and persistent memory enable context recovery across sessions. Without them, work duplicates and diverges. Always search memory before committing to new work.

### 4. Hardware Embodiment Unlocks New Problem Classes
Each new capability layer (move → stream → control → record → infer) introduces a new problem class. Can't reuse prior debugging patterns. Expect: safety constraints → sensor fusion → inference timing as emerging problem classes.

### 5. Cost Structure Drives Architecture Decisions
When costs become visible, they change priorities. Context-loading costs can dominate total spend (e.g., 98%+ of token cost). Make costs visible early — they shift architectural decisions.

### 6. Template-Driven Development Compresses MVP Time
Reusable templates skip scaffolding overhead and deliver working software in hours, not days. Template ROI is confirmed — this repo is the template.

### 7. Safety-First Testing is Non-Negotiable for Physical Systems
When controlling physical hardware via UI, write safety tests FIRST, ship AFTER all pass. The test-coverage threshold doubles when hardware actuation is involved. A UI bug that sends wrong values isn't a crash — it's broken hardware.

---

## Emerging Patterns

### 8. Sub-Agent Refactoring Works But Needs Audit
Multi-agent parallel refactoring is fast but leaves cross-cutting issues: dead code, stale references, migration order violations. Structural work happens fast; integration testing must follow.

### 9. Tracing to Data Source Beats Debugging the Pipeline
When a pipeline breaks, don't debug backwards from the sink — trace to where data ORIGINATES. The root cause is usually at the source, not in the middle.

### 10. Measure the Metric You're Selling
If a change is sold as "simpler", "smaller", "faster", or "more maintainable", measure that metric at every iteration — not just at the end. `wc -l src/` before and after, or the equivalent for complexity / perf / read-time. If the metric moves the wrong direction, name the trade-off upfront and get explicit sign-off. "Simpler" without a number is a claim, not a result. The most common process failure in a refactor is the silent drift — a 30% LOC growth that nobody notices because nobody measured.

### 11. Verify State Before Reporting It
Git state, file counts, scope numbers, bug claims, test counts — all decay between the moment you read them and the moment you present them. Re-run the command before quoting the number. The cost of verifying is 5 seconds; the cost of misleading the user with cached state is 30 minutes of rework when the mismatch is discovered. Never quote a number from memory when a command can produce it fresh.

### 12. Ask One Clarifying Question Per Terse Instruction
Short user instructions are ambiguous by construction — "always require", "absolute imports", "use TypedDict", "ban X" each have 2-3 plausible interpretations. Ask **one** clarifying question before restructuring code around your interpretation. "Do you mean X applies to A or B?" costs 10 seconds and prevents 30 minutes of misdirected work. Two clarifying questions per instruction is annoying; zero is expensive. The cost asymmetry makes one question the default answer.

### 13. Design the Construction Call First
Before writing a type, helper, or abstraction, draft the three most common call sites that will use it. If any call site looks uglier with the new abstraction than without it, don't extract. If a TypedDict forces callers to pass `None` for more than half the fields, the schema is wrong. **The shape of the CALL matters more than the shape of the DEFINITION.** This catches over-abstracted helpers, under-constrained types, and premature interfaces before you've committed to implementing them.

---

## Decision-Making Template

When deciding between options:
1. Strong preference for **working pragmatic** over elegant theoretical
2. Demand for **end-to-end validation** before closure
3. Comfort with **deferral** over perfect execution
4. Reference to **memory files** before committing to new work (always search first)
