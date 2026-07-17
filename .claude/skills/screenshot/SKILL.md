---
name: screenshot
description: Take Playwright screenshots of a running web app. Desktop + mobile viewports. Use for visual QA or before UX review.
allowed-tools: Bash, Read, Write
argument-hint: [url] [--pages /path1,/path2]
---

Take screenshots of a running web application at desktop and mobile viewports.

Arguments: `$ARGUMENTS`

Parse arguments:
- First positional arg = base URL (defaults to `http://localhost:3000`)
- `--pages` = comma-separated list of paths (defaults to `/`)

## Steps

### 1. Ensure Playwright is Available

```bash
pnpm exec playwright --version 2>/dev/null || pnpm add -g playwright
pnpm exec playwright install chromium 2>/dev/null || true
```

If Playwright cannot be installed, report the error and stop.

### 2. Create Screenshot Script

Write a temporary Node.js script (`/tmp/screenshot.mjs`) that:

- Launches Chromium in headless mode
- For each page path, captures two screenshots:
  - **Desktop:** 1440x900 viewport
  - **Mobile:** 390x844 viewport
- Settings for each screenshot:
  - `fullPage: true`
  - Wait for `networkidle` (or `load` if networkidle times out after 10s)
  - Additional 3-second delay after load for hydration/animations
- Names files: `{page-slug}_desktop.png` and `{page-slug}_mobile.png`
  - Root `/` becomes `home`
  - `/tasks` becomes `tasks`
  - `/settings/profile` becomes `settings-profile`
- Saves all screenshots to `./screenshots/` relative to the current working directory

### 3. Run the Script

```bash
mkdir -p ./screenshots
node /tmp/screenshot.mjs
```

### 4. Report Results

List all captured screenshots with their file paths and dimensions. Example:

```
Screenshots saved to ./screenshots/:
- home_desktop.png (1440x900)
- home_mobile.png (390x844)
- tasks_desktop.png (1440x900)
- tasks_mobile.png (390x844)
```

## Error Handling

- If the base URL is unreachable, report that the app does not appear to be running and suggest starting it with `just run-frontend`.
- If a specific page returns 404, skip it and note it in the report.
- If Chromium fails to launch, suggest checking that the environment supports headless browsers.

## Notes

- The app must be running before invoking this skill.
- Screenshots are overwritten on each run (no versioning).
- For CI environments, ensure `--no-sandbox` is passed to Chromium if running as root.
