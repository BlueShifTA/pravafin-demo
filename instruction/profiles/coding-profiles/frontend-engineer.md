# FRONTEND_ENGINEER — Coding Profile

**Role:** Frontend Engineer (Feature Completeness & UX Focus)
**Reference:** Analyzed from 48 commits (6-month analysis)
**Primary Focus:** React/Next.js + API integration
**Strength:** Feature completeness, UX focus, comprehensive error handling
**Analysis Date:** 2026-03-19

---

## 🎯 Coding Philosophy

A frontend engineer is **user-focused and feature-driven**. This profile shows:
- Ticket-driven development (track to requirements)
- User-facing features are complete (UI + API + state + errors)
- Data visualization (images, reports, carousels)
- Framework management (Next.js version control)
- Permission-based UX (frontend reflects backend rules)

**Principle:** "Every feature must be complete: UI + API + state + error handling"

---

## 📊 Activity Profile

| Metric | Value |
|--------|-------|
| **Typical Commit Volume** | 45+ commits/6 months |
| **Systems** | Frontend (primary) + API integration |
| **Avg Commit Size** | Medium |
| **Commit Pattern** | Ticket-driven ([TICKET-XXXX] prefix) |

### Commit Categories

- **UI Features:** 40-50% (buttons, dialogs, workflows)
- **Data Visualization:** 15-20% (image carousel, report display)
- **File Handling:** 15-20% (import/export, compression)
- **Framework/Tooling:** 10-15% (Next.js upgrade, dependencies)
- **Bug Fixes:** 10-15% (UI inconsistencies, state management)

---

## 💻 Code Style & Patterns

### 1. Ticket-Driven Development

**Pattern:** Link code to requirements

```
[TICKET-2825] - Feedback: New Button "Combine Vials"
[TICKET-2918] Prevent control actions during experiment
[TICKET-3009] Bug - Project Import - Study artifacts missing
[TICKET-2982] Fix UI inconsistency part 2
[TICKET-2925] Update NextJS to 16.0
```

**Format:** `[TICKET-XXXX] Description`

**Why:**
- Links code to requirements
- Helps with traceability
- Issue history in git log
- Cross-team communication

### 2. Feature Completeness Pattern

**Pattern:** Every feature includes ALL parts

```
[TICKET-2825] New Button "Combine Vials"
├── Frontend: New button + modal dialog
├── State: Modal open/close + selection state
├── API: POST /evaluations/{id}/combine-vials
├── Error Handling: Invalid selections, API failures
├── Testing: User can combine vials
└── Release Notes: Document feature
```

**NEVER partial features:**
- ❌ "Added button but API not done"
- ❌ "API endpoint exists but no UI"
- ✅ "Button + API + state + errors + tests"

### 3. Permission-Based UX

**Pattern:** Backend enforces, frontend reflects

```typescript
// Backend
POST /experiments/{id}/start
  → Check user.can('control_experiment')
  → Check experiment.state !== 'running'
  → If not permitted: 403 Forbidden

// Frontend
if (user.can('control_experiment')) {
    <button onClick={startExperiment}>Start</button>
}
```

### 4. Data Format Optimization

**Pattern:** Use right format for right purpose

```
Images: HDF5 with compression (50% smaller)
Metadata: JSON (human-readable)
Large data: CSV or Parquet
Config: YAML
```

### 5. Error Handling Completeness

**Pattern:** Each error has specific message

```typescript
try {
    await api.post('/combine-vials', { vials: selected });
} catch (error) {
    if (error.status === 403) {
        setError("You don't have permission");
    } else if (error.status === 409) {
        setError("Selection invalid (mismatched types?)");
    } else if (error.status === 400) {
        setError("Invalid request: " + error.detail);
    } else {
        setError("Server error, please try again");
    }
}
```

---

## 🧪 Testing Strategy

**Approach:** Test user interactions, not implementation

**Test categories:**
```
tests/
├── unit/
│   ├── Button renders when enabled
│   ├── Modal opens on click
│   ├── Selection state updates
├── integration/
│   ├── API called with correct params
│   ├── Error message shows on failure
│   └── Success closes modal
└── e2e/
    ├── User can complete feature workflow
    └── Handles all error cases
```

### Component Test Pattern

```typescript
describe('CombineVialsButton', () => {
    it('renders when enabled', () => {
        render(<CombineVialsButton enabled={true} />);
        expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('disabled when no selection', () => {
        render(<CombineVialsButton selected={[]} />);
        expect(screen.getByRole('button')).toBeDisabled();
    });

    it('calls API with selected vials', async () => {
        const mockApi = mock();
        render(<CombineVialsButton api={mockApi} selected={[1,2]} />);

        await userEvent.click(screen.getByRole('button'));

        expect(mockApi.post).toHaveBeenCalledWith('/combine', {vials: [1,2]});
    });

    it('shows error on API failure', async () => {
        const mockApi = mockFailed(409);
        render(<CombineVialsButton api={mockApi} />);

        await userEvent.click(screen.getByRole('button'));

        expect(screen.getByText(/invalid/i)).toBeInTheDocument();
    });
});
```

---

## 🏗️ Architectural Decisions

### Decision 1: File Format for Large Data

**Problem:** Study artifacts are large (many images), storage expensive

**Solution:**
```
Old: Individual PNG files, no compression
New: HDF5 (Hierarchical Data Format)
  ├── Compression (GZIP)
  ├── Metadata embedded
  ├── Hierarchical organization
  └── Result: 50% smaller

Frontend: Decode HDF5 on load, cache, display
```

### Decision 2: Import/Export Completeness

**Pattern:** Full round-trip capability

```
[TICKET-2896] Project Export/Import
├── Export: Zip all artifacts + JSON manifest
├── Format: Standard HDF5 + JSON structure
├── Import: Unzip, validate, restore
├── Verification: Check all artifacts present
```

### Decision 3: Permission System UI

**Pattern:** Backend enforces, frontend disables

```
Backend: Only allow control if user.can('control_experiment')
Frontend: Disable button if not permitted
Message: "Experiment in progress" (no permission shown as 403)
UX: Graceful degradation (buttons disabled, not hidden)
```

---

## 📝 Commit Message Style

**Approach:** Ticket ID + context + description

```
[TICKET-XXXX] Issue type: Description

[TICKET-2825] - Feedback: New Button "Combine Vials"
[TICKET-2918] Prevent control actions during experiment
[TICKET-3009] Bug - Project Import - Study artifacts missing
```

---

## 🚀 Key Techniques

### Technique 1: Ticket-Driven Workflow

**Steps:**
1. Ticket created: [TICKET-2825] New Button
2. Implement feature (UI + API + state + errors)
3. Commit with ticket: `[TICKET-2825] ...`
4. Code review references ticket
5. Testing references ticket
6. Deploy references ticket

**Result:** Complete traceability

### Technique 2: Comprehensive Error Handling

**Pattern:** Each error code → specific message

```typescript
const errorMessages = {
    400: "Invalid input",
    403: "You don't have permission",
    404: "Not found",
    409: "Selection conflict (try again)",
    500: "Server error (try again later)",
};

catch (error) {
    setError(errorMessages[error.status] || "Unknown error");
}
```

### Technique 3: State Management for UI

**Pattern:** Separate concerns

```typescript
// UI state
const [isModalOpen, setIsModalOpen] = useState(false);
const [selected, setSelected] = useState([]);

// Form state
const [formData, setFormData] = useState({});

// API state
const { data, isLoading, error } = useQuery(...);

// User state
const { user } = useAuth();
```

### Technique 4: Feature Gating

**Pattern:** Permissions checked in UI

```typescript
if (user.can('export_project')) {
    <button onClick={exportProject}>Export</button>
}

if (user.can('control_experiment')) {
    <button onClick={startExperiment}>Start</button>
}
```

---

## 📋 Checklist: Code Like a Frontend Engineer

- [ ] Use ticket tracking in commits: `[TICKET-XXXX]`
- [ ] Every feature has UI + API + state + error handling
- [ ] Error messages are specific (not generic)
- [ ] Permissions checked frontend + enforced backend
- [ ] File formats optimized for use case
- [ ] User feedback documented in commit messages
- [ ] Framework/dependencies kept current
- [ ] Image handling is performant (compression, lazy loading)
- [ ] Modal/dialog flows tested
- [ ] Export/import features validated

---

## 🔗 Real Examples from Codebase

See mono repo for working examples:
- Complete features (UI + API + state + errors)
- Permission-based UI (frontend reflects backend rules)
- File format optimization (HDF5 compression)
- Import/export workflows
- Ticket-tracked development

---

**Profile Created:** 2026-03-19
**Based On:** 48+ commits over 6 months
**Confidence:** High (very consistent ticket-driven approach)
**Use This For:** Frontend engineers, UI developers, product engineers
