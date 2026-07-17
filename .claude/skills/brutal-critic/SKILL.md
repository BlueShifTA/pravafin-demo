---
name: brutal-critic
description: Spawn a brutally honest code/UX/architecture/security reviewer. Use when user says "critique", "review", "brutal critic", or "roast this code".
allowed-tools: Bash, Read, Grep, Glob, Agent
argument-hint: [target-path] [--type code|ux|architecture|security]
---

Spawn a brutally honest reviewer to critique the target path. No sugar-coating.

Target: `$ARGUMENTS`

Parse arguments:
- First positional arg = target path (defaults to project root)
- `--type` = review type (defaults to `code`)

## Review Types and Personas

| Type | Persona(s) | Focus |
|------|-----------|-------|
| `code` | Staff Engineer (10+ yrs) | Bugs, architecture rot, dead code, type safety, error handling, performance |
| `ux` | Senior UX Designer + Solo Founder | Usability, visual hierarchy, mobile responsiveness, conversion, first impressions |
| `architecture` | Principal Engineer | System design, coupling, scaling bottlenecks, dependency risks, tech debt trajectory |
| `security` | Security Auditor | Injection, auth bypass, secrets exposure, CORS, input validation, dependency vulns |

## Steps

### For `code`, `architecture`, or `security` types:

1. Spawn a **critic agent** (`subagent_type: Explore` — read-only by design) with the appropriate persona.

2. The agent must review the target path and produce output in this exact format:

   ```
   ## VERDICT: [PASS | PASS WITH CONCERNS | NEEDS WORK | FAIL]

   ## P0 — Showstoppers (must fix before shipping)
   - [file:line] Description of the issue and why it matters

   ## P1 — Significant Issues (fix soon)
   - [file:line] Description

   ## P2 — Minor Improvements (nice to have)
   - [file:line] Description

   ## P3 — Nits (style, naming, minor cleanup)
   - [file:line] Description

   ## What's Good (be specific — no empty praise)
   - Concrete things done well, with file references

   ## Brutal Summary
   One paragraph, no hedging. Would you ship this? Would you hire someone who wrote this?
   ```

3. Report the results to the user.

### For `ux` type:

1. **Screenshots first.** Before any review, take screenshots of the running app:
   - 4 key pages at desktop viewport (1440x900)
   - 4 key pages at mobile viewport (390x844)
   - Use Playwright or equivalent (see `/screenshot` skill)
   - If the app is not running, tell the user to start it first

2. Spawn **two critic agents** sequentially with different personas:

   **Reviewer 1 — Senior UX Designer:**
   - Visual hierarchy, spacing, typography, color contrast
   - Navigation flow, information architecture
   - Mobile responsiveness, touch targets
   - Accessibility (WCAG basics)

   **Reviewer 2 — Solo Founder (first-time user perspective):**
   - "Would I understand what this does in 5 seconds?"
   - "Would I trust this enough to enter my data?"
   - "Where would I get stuck or confused?"
   - "What would make me close this tab?"

3. Each reviewer produces the same VERDICT/P0-P3/Brutal Summary format.

4. Synthesize both reviews into a combined report.

## Rules

- **No softening language.** "This is concerning" means "this is broken."
- **Every issue needs a file and line reference** (except UX issues which reference screenshots/pages).
- **P0 = the user should not ship this.** Reserve P0 for genuine showstoppers.
- **"What's Good" must be specific.** "Clean code" is not acceptable — cite the specific pattern or decision that's good.
- **Brutal Summary is mandatory.** One honest paragraph.
