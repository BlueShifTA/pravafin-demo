# FRONTEND_NEXTJS_CODING_PROFILE.md

Coding profile for template-safe React/Next.js frontend development (MUI + Tailwind hybrid)

Generated: 2026-02-23
Scope: `coresat` frontend alignment inspired by `mono/projects/frontend` patterns

---

## Who This Profile Is For

Use this profile when building or evolving a reusable Next.js frontend template that should:

- stay product-agnostic
- enforce a modular component structure
- package reusable controls (buttons, text fields, layout shells) at a shared module level
- keep strong developer ergonomics (`just`, pnpm scripts, lint/typecheck)

This profile extracts patterns, not product logic.

---

## Architecture Patterns

### 1. App Router + Shared Module Foundation

Keep Next.js App Router for the template and build a shared module layer under `src/components`:

- `components/layout`: providers, page shell, section containers
- `components/ui/buttons`: shared button wrappers and loading variants
- `components/ui/fields`: shared text field wrappers
- `components/ui/feedback`: spinners and status helpers
- feature modules later under `components/<feature>` or `features/<feature>`

Do not start by putting app-specific UI directly in `src/app/page.tsx`.

### 2. Provider Composition (Single Entry Point)

Use one provider component (for example `AppProviders`) to centralize:

- MUI `ThemeProvider`
- `CssBaseline`
- React Query `QueryClientProvider`

This prevents provider setup duplication across pages and keeps `src/app/layout.tsx` minimal.

Example:

```tsx
import {FormControl, FormControlLabel, Checkbox} from '@mui/material'

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(() => createAppQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={appTheme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
```

### 3. Theme/Tokens First

Define design tokens once, then flow them into:

- TypeScript theme tokens (`src/theme/tokens.ts`)
- CSS variables (`src/styles/variables.css`)
- MUI theme overrides (`src/theme/mui-theme.ts`)

This keeps Tailwind utility usage and MUI component styling visually aligned.

### 4. Placeholder-First Template Demos

Template pages should demonstrate structure with placeholders:

- generic labels (`Template Name`, `Target Environment`)
- generic actions (`Run Dry Check`, `Save Placeholder Config`)
- generic cards (`Backend`, `Commands`, `Bootstrap`)

Never ship template demos with product-specific terms or internal feature names copied from a real app.

---

## Component Structure Conventions

Recommended baseline:

```text
src/
  app/
  components/
    layout/
    ui/
      buttons/
      fields/
      feedback/
    demo/
  lib/
  styles/
  theme/
```

### Shared vs Feature Components

Put a component in `components/ui` when:

- it is reusable across pages/features
- it standardizes styling/behavior (button, text field, spinner)
- it represents a template-level convention

Put a component in a feature module when:

- it depends on feature-specific data or workflow
- it is unlikely to be reused
- its props are tied to a single domain model

---

## Styling Strategy (MUI + Tailwind Hybrid)

### Division of Responsibility

Use MUI for:

- interactive controls (buttons, inputs, selects, dialogs)
- theme-driven defaults and component overrides
- typography and paper/card surfaces when consistency matters

Use Tailwind for:

- page layout (`grid`, `flex`, spacing, responsive wrappers)
- utility composition inside page assembly
- fast scaffolding of structure around shared components

Avoid duplicating component styles in both MUI overrides and Tailwind classes.

### Token Rules

Use generic token names:

- `brand.primary`
- `surface.card`
- `border.subtle`
- `status.success`

Do not copy product-specific token names into a template.

---

## Reusable Controls Standards

### Buttons

Create a base wrapper (`AppButton`) and specialized wrappers (`ButtonWithSpinner`) instead of repeating inline button config.

Requirements:

- default variant/color/size
- predictable disabled behavior
- loading state support without layout shift
- passthrough props for flexibility

Example:

```tsx
export function ButtonWithSpinner({
  isLoading = false,
  children,
  disabled,
  ...props
}: ButtonWithSpinnerProps) {
  return (
    <AppButton {...props} disabled={disabled || isLoading}>
      <Box sx={{ position: "relative" }}>
        <Box sx={isLoading ? { visibility: "hidden" } : undefined}>{children}</Box>
        {isLoading ? <Spinner color="inherit" /> : null}
      </Box>
    </AppButton>
  );
}
```

### Text Fields

Create `AppTextField` to standardize:

- `variant`
- `size`
- `fullWidth`
- helper text spacing
- default theming behavior

Use raw MUI `TextField` directly only when a page needs uncommon behavior not suitable for the shared wrapper.

---

## Naming Conventions

### Files and Components

- `PascalCase.tsx` for React components (`AppButton.tsx`, `PageShell.tsx`)
- `kebab-case` or `camelCase` only when existing repo conventions require it
- `tokens.ts`, `mui-theme.ts`, `query-client.ts` for infrastructure modules

### Props Types

- `ComponentNameProps`
- export props types for shared modules (`AppButtonProps`, `AppTextFieldProps`)

### Template Demos

Use names that communicate placeholder intent:

- `TemplateSetupForm`
- `ExampleStatusCard`
- `DemoActionPanel`

Avoid names that imply a real product module.

---

## Data and State Guidelines

### React Query

Use a shared query client factory in `src/lib/query-client.ts`.

Defaults should favor template ergonomics:

- `refetchOnWindowFocus: false`
- low retry counts

### OpenAPI / Orval (FastAPI -> Generated Hooks)

For template frontends that pair with FastAPI, prefer generated API hooks over ad-hoc fetch wrappers:

- generate OpenAPI schema from the backend (`/openapi.json`)
- generate frontend types + React Query hooks with Orval
- keep generated outputs under a dedicated source folder (for example `src/lib/generated/`)
- import generated hooks in small client components (example: `useHealthHealthGet`) instead of calling `fetch` inline in page files

Recommended shape (coresat pattern):

- Orval `client: "react-query"`
- `httpClient: "fetch"` (built-in) unless a shared mutator is required
- `mode: "split"` with `endpoints.ts` + `models/*` output

#### Relative URL Caveat (Next.js rewrites)

When Orval emits relative fetch URLs (for example `/health`, `/ready`), add Next.js rewrites so browser requests reach the backend in local dev. Do not assume only `/api/*` needs proxying.

#### Git Ignore Caveat (Monorepo Templates)

Python-oriented root `.gitignore` rules like `lib/` can accidentally ignore frontend source paths such as `projects/frontend/src/lib/generated/**`. Add explicit unignore rules when generated frontend source is intended to be tracked.

### Page Data

- Server components fetch static or initial page data when possible.
- Client components handle interactive form state and transient UI behavior.

This split keeps examples realistic without overcomplicating the template.

---

## Testing Philosophy (Frontend Template)

Focus on fast checks that protect the template shape:

- lint and typecheck must pass
- build must pass
- shared wrappers compile and render
- example page remains functional after refactors

For regressions:

- add tests when a shared component bug affects multiple pages/modules
- prioritize behavior and rendering semantics over implementation details

---

## Commit Style (Frontend-Friendly)

Keep the same disciplined commit structure used in backend-oriented workflows, adapted for frontend changes.

Format:

```text
<action> <what>

- problem: <root cause>
- <change summary>
- <testing/verification>
```

Example:

```text
Add shared frontend UI foundation for template

- problem: frontend template only had page-level Tailwind markup with no reusable controls
- add MUI theme/tokens/providers and shared button/text-field wrappers
- refactor home page to use placeholder-first modular demo components
- add just/pnpm convenience aliases for frontend checks and API generation
```

---

## Development Workflow (`just` + pnpm)

Template baseline commands:

- `just run-frontend`
- `just test-frontend`
- `just typecheck`
- `just lint`
- `just generate-frontend-types`
- `cd projects/frontend && pnpm run api`

Keep command alignment additive:

- preserve existing commands
- add convenience aliases rather than renaming commands users already rely on

---

## Anti-Patterns to Avoid

- Copying business/domain pages from production apps into the template
- Copying branded token names/colors without generalizing
- Using raw buttons/inputs everywhere instead of shared wrappers
- Putting provider setup directly into each page
- Mixing Tailwind and MUI styles for the same component behavior
- Shipping demo text that looks like internal product terminology

---

## Template Extraction Rules (Important)

When aligning a template to a real app:

1. Extract structural patterns first:
   - providers
   - theme architecture
   - reusable controls
   - component folder layout
2. Replace domain-specific labels and workflows with placeholders.
3. Generalize tokens before adding them to the template.
4. Keep examples demonstrative, not product-representative.
5. Document what is intentionally omitted (auth flows, telemetry, product logic).

Short rule:

Pattern yes, product no.

---

## Template Baseline Checklist

- Shared `AppProviders` exists and wraps App Router layout
- Theme tokens exist in TS + CSS variables
- MUI theme overrides are defined in one file
- Shared button wrappers exist (`AppButton`, `ButtonWithSpinner`)
- Shared text field wrapper exists (`AppTextField`)
- Page shell/section components exist for layout composition
- Home page demonstrates placeholder-first modular UI usage
- `just` frontend convenience aliases exist
- pnpm script aliases exist without breaking existing commands
- Docs explain extraction and placeholder rules
