---
name: ci
description: Run the full CI pipeline locally. Use before creating a PR, after finishing a feature, or to validate everything works end-to-end.
disable-model-invocation: true
allowed-tools: Bash, Read
---

Run the full CI-equivalent pipeline locally to catch issues before pushing.

## Steps

1. Run the full CI pipeline:
   ```bash
   just run-ci
   ```

2. **On failure:** Identify which stage failed (test, typecheck, lint, build), read the error, and report:
   - The failing stage
   - The specific error(s)
   - Suggested fix

3. **On success:** Report "CI pipeline passed" with a brief summary of what ran.
