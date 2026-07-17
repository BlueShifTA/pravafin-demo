---
name: research
description: Deep autonomous research on any topic. Formulates own questions, critiques findings, produces source-backed knowledge documents.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
argument-hint: "[topic]"
---

Deep autonomous research that produces dense, source-backed knowledge documents.

**Topic:** `$ARGUMENTS`

Parse the topic from arguments. If an output path is specified (e.g., `topic --output /path/to/dir`), use it. Otherwise write to the current working directory.

## Phase 1: Scope

1. **Parse the topic** — identify the core subject, domain, and any constraints the user specified.
2. **Formulate 10-15 sub-questions** across these dimensions:
   - How does it actually work? (not marketing claims)
   - What are the alternatives and how do they compare?
   - What breaks in production? What is overhyped?
   - Who uses this at scale and what do they report?
   - What are the hidden costs (licensing, operational, migration)?
   - When should you use it vs. avoid it?
3. **Print the question list** for transparency before proceeding.

## Phase 2: Research Template

The output document must cover these 7 sections:

| # | Section | Focus |
|---|---------|-------|
| 1 | Core Mechanics | How it actually works — architecture, data flow, key algorithms. No marketing. |
| 2 | Comparison | Alternatives, benchmarks, real numbers. Table format preferred. |
| 3 | Critical Analysis | What breaks? What is overhyped? Hidden costs? Vendor lock-in? |
| 4 | Production Reality | Who uses this in production? At what scale? What problems did they hit? |
| 5 | Integration | How would you integrate this into a typical project? Migration path? |
| 6 | Recommendation | Decision framework: when to use, when to avoid, for whom. |
| 7 | Sources | Every major claim must have a cited source with URL. |

## Phase 3: Research Iteration Loop

For each sub-question (or cluster of related questions):

1. **Search** — use WebSearch to find relevant sources. Try multiple query phrasings.
2. **Read** — use WebFetch to read the most promising sources in detail.
3. **Extract** — pull out facts, numbers, benchmarks, architecture details.
4. **Verify** — cross-reference claims across multiple sources. Flag contradictions.
5. **Critique** — actively look for counterarguments, failure modes, and bias.
6. **Record** — add findings to the appropriate section of the document.

**Research stance:** Be critical by default. Assume marketing claims are exaggerated until proven by independent sources. Look for:
- Benchmarks run by vendors vs. independent benchmarks
- "Works at scale" claims without naming the scale
- Missing cost comparisons
- Cherry-picked metrics
- Survivorship bias in case studies

## Phase 4: Finalize

1. **Compile the document** with this structure:
   ```markdown
   ---
   topic: [topic name]
   created: [YYYY-MM-DD]
   sources_count: [N]
   confidence: [high|medium|low]
   ---

   # [Topic Name]

   > One-paragraph executive summary.

   ## 1. Core Mechanics
   ...

   ## 2. Comparison
   ...

   ## 3. Critical Analysis
   ...

   ## 4. Production Reality
   ...

   ## 5. Integration
   ...

   ## 6. Recommendation
   ...

   ## 7. Sources
   - [N] [Title](URL) — brief note on what this source covers
   ```

2. **Quality checks:**
   - Every factual claim has a source reference
   - No section is empty or placeholder-only
   - Tables are used for comparisons (not prose lists)
   - Code examples are included where they aid understanding
   - Confidence rating reflects source quality and consensus

3. **Write the file** — save as `{topic_slug}.md` in the output directory.

4. **Print summary:**
   - Topic and output path
   - Number of sources cited
   - Key findings (3-5 bullets)
   - Confidence level and reasoning
   - Any gaps or areas needing follow-up research

## Rules

- **Every claim needs a source.** Do not state facts without a URL to back them up.
- **Be critical, not promotional.** Your job is to find truth, not validate hype.
- **Prefer recent sources.** Weight sources from the last 12 months higher than older ones.
- **Flag uncertainty.** If sources disagree, say so explicitly and explain why.
- **Dense output.** Prefer tables, bullet points, and code blocks over prose paragraphs. No filler.
- **No hallucinated sources.** If you cannot find a source, say "no source found" — never fabricate a URL.
