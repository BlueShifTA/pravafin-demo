# SOLID Principles — Reference Guide

> **Authoritative rules:** See root [CLAUDE.md](../../CLAUDE.md) § "SOLID Principles — Mandatory".
> This document provides extended examples, real-world scenarios, and testing guidance.

---

## Why SOLID Matters for This Stack

Our stack (FastAPI + Next.js + multi-agent orchestration) has three scaling pressures that SOLID directly addresses:

1. **Agent code runs unsupervised.** A god class that works today silently drifts when an agent adds features. SRP prevents accumulation of responsibilities.
2. **Client codebases vary wildly.** OCP and DIP ensure our tooling adapts to new backends/infra without rewriting core logic.
3. **Testing is the safety net.** ISP keeps mocks minimal. DIP makes dependency injection natural. Without them, test suites become fragile and slow.

---

## S — Single Responsibility Principle

> A class has exactly one reason to change.

### Extended Example: API Route Handler

```python
# WRONG — route handler does validation, business logic, persistence, and notification
@router.post("/tasks")
async def create_task(request: CreateTaskRequest, db: Session = Depends(get_db)):
    if len(request.title) > 200:
        raise HTTPException(400, "Title too long")
    task = Task(title=request.title, status="todo", priority=request.priority)
    db.add(task)
    db.commit()
    await send_slack_notification(f"New task: {task.title}")
    return TaskOut.model_validate(task)

# CORRECT — handler is thin, delegates to focused services
@router.post("/tasks")
async def create_task(
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service),
) -> TaskOut:
    return await task_service.create(request)

# Each service has ONE job
class TaskService:
    def __init__(self, repo: TaskRepository, notifier: Notifier) -> None:
        self.repo: TaskRepository = repo
        self.notifier: Notifier = notifier

    async def create(self, request: CreateTaskRequest) -> TaskOut:
        task = await self.repo.save(Task.from_request(request))
        await self.notifier.notify(f"New task: {task.title}")
        return TaskOut.model_validate(task)
```

### How to Test SRP

```python
# If your test file needs to mock 5+ unrelated dependencies, the class violates SRP
def test_create_task():
    repo = FakeTaskRepository()
    notifier = FakeNotifier()
    service = TaskService(repo=repo, notifier=notifier)  # only 2 deps = good SRP

    result = await service.create(CreateTaskRequest(title="Fix bug", priority="high"))

    assert result.title == "Fix bug"
    assert repo.saved_count == 1
    assert notifier.last_message == "New task: Fix bug"
```

### SRP Smell Checklist

- [ ] Class name contains "Manager", "Handler", "Utils", or "Helper" — likely doing too much
- [ ] Module imports from 5+ unrelated packages — mixed responsibilities
- [ ] `__init__` accepts 6+ dependencies — class has too many concerns
- [ ] Test setup requires mocking 4+ unrelated systems — split the class

---

## O — Open/Closed Principle

> Open for extension, closed for modification.

### Extended Example: Report Formatters

```python
import typing as tp
import dataclasses as dc

class ReportFormatter(tp.Protocol):
    def format(self, data: dict[str, float]) -> str: ...

@dc.dataclass(frozen=True)
class MarkdownFormatter:
    """Formats report as Markdown table."""
    def format(self, data: dict[str, float]) -> str:
        rows = [f"| {k} | {v:.2f} |" for k, v in data.items()]
        return "| Metric | Value |\n|--------|-------|\n" + "\n".join(rows)

@dc.dataclass(frozen=True)
class CSVFormatter:
    """Formats report as CSV."""
    def format(self, data: dict[str, float]) -> str:
        rows = [f"{k},{v:.2f}" for k, v in data.items()]
        return "metric,value\n" + "\n".join(rows)

@dc.dataclass(frozen=True)
class JSONFormatter:
    """Formats report as JSON."""
    def format(self, data: dict[str, float]) -> str:
        import json
        return json.dumps(data, indent=2)

# Adding HTMLFormatter requires ZERO changes to existing code
# Just create a new class that satisfies ReportFormatter protocol

class ReportEngine:
    """Closed for modification — never edited when adding new formats."""
    def __init__(self, formatter: ReportFormatter) -> None:
        self.formatter: ReportFormatter = formatter

    def generate(self, data: dict[str, float]) -> str:
        return self.formatter.format(data)
```

### OCP Smell Checklist

- [ ] Adding a new variant requires editing an existing `if/elif/else` chain
- [ ] `isinstance()` checks grow with each new type
- [ ] Core module is modified in every PR (it should be stable)
- [ ] Configuration changes require code changes (should be data-driven)

---

## L — Liskov Substitution Principle

> Subtypes must be substitutable for their base type without surprises.

### Extended Example: Storage Backends

```python
import typing as tp

class CacheBackend(tp.Protocol):
    async def get(self, key: str) -> bytes | None: ...
    async def set(self, key: str, value: bytes, ttl_seconds: int = 300) -> None: ...
    async def delete(self, key: str) -> None: ...

class RedisCache:
    """Full implementation — satisfies the contract completely."""
    async def get(self, key: str) -> bytes | None:
        return await self._client.get(key)

    async def set(self, key: str, value: bytes, ttl_seconds: int = 300) -> None:
        await self._client.setex(key, ttl_seconds, value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

class InMemoryCache:
    """Test double — also satisfies the contract completely."""
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def get(self, key: str) -> bytes | None:
        return self._store.get(key)

    async def set(self, key: str, value: bytes, ttl_seconds: int = 300) -> None:
        self._store[key] = value  # TTL ignored in test — acceptable simplification

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

# WRONG — violates LSP by narrowing behavior
class BrokenCache:
    async def get(self, key: str) -> bytes | None:
        return None  # always returns None — breaks callers expecting cached data

    async def set(self, key: str, value: bytes, ttl_seconds: int = 300) -> None:
        raise NotImplementedError("Read-only cache")  # VIOLATION: narrows the contract

    async def delete(self, key: str) -> None:
        pass  # silently does nothing — callers can't trust the operation
```

### LSP Smell Checklist

- [ ] Subclass raises `NotImplementedError` for a parent method
- [ ] Subclass silently narrows accepted input types
- [ ] Subclass returns `None` where base returns a value
- [ ] Callers need `isinstance` checks to handle different subtypes

---

## I — Interface Segregation Principle

> Clients depend only on methods they use.

### Extended Example: Agent Capabilities

```python
import typing as tp

# WRONG — every agent must implement all 6 methods even if they only use 2
class AgentCapabilities(tp.Protocol):
    def read_file(self, path: str) -> str: ...
    def write_file(self, path: str, content: str) -> None: ...
    def search_web(self, query: str) -> list[str]: ...
    def send_message(self, text: str) -> None: ...
    def run_bash(self, cmd: str) -> str: ...
    def query_database(self, sql: str) -> list[dict]: ...

# CORRECT — segregated by capability
class FileReader(tp.Protocol):
    def read_file(self, path: str) -> str: ...

class FileWriter(tp.Protocol):
    def write_file(self, path: str, content: str) -> None: ...

class WebSearcher(tp.Protocol):
    def search_web(self, query: str) -> list[str]: ...

class Messenger(tp.Protocol):
    def send_message(self, text: str) -> None: ...

# Each agent declares only what it needs
class ResearchAgent:
    def __init__(self, searcher: WebSearcher, reader: FileReader) -> None:
        self.searcher: WebSearcher = searcher
        self.reader: FileReader = reader

class WriterAgent:
    def __init__(self, writer: FileWriter, messenger: Messenger) -> None:
        self.writer: FileWriter = writer
        self.messenger: Messenger = messenger
```

### ISP Smell Checklist

- [ ] Protocol has 6+ methods but most callers use 2-3
- [ ] Mock objects stub out methods with `pass` or `raise NotImplementedError`
- [ ] Adding a method to an interface requires updating 5+ implementations
- [ ] Test setup creates large fake objects with mostly unused methods

---

## D — Dependency Inversion Principle

> High-level modules depend on abstractions, not concretions. Inject dependencies at the composition root.

### Extended Example: FastAPI Composition Root

```python
import typing as tp
import dataclasses as dc

# Abstractions (Protocols)
class TokenTracker(tp.Protocol):
    async def record(self, agent_id: str, tokens: int, cost_usd: float) -> None: ...

class TaskRepository(tp.Protocol):
    async def get_all(self) -> list[Task]: ...
    async def save(self, task: Task) -> Task: ...

# High-level service — depends ONLY on abstractions
@dc.dataclass
class DashboardService:
    tokens: TokenTracker
    tasks: TaskRepository

    async def get_summary(self) -> DashboardSummary:
        all_tasks = await self.tasks.get_all()
        return DashboardSummary(
            total_tasks=len(all_tasks),
            active=sum(1 for t in all_tasks if t.status == "active"),
        )

# Low-level concretions
class SQLTokenTracker:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db

    async def record(self, agent_id: str, tokens: int, cost_usd: float) -> None:
        self.db.add(TokenUsage(agent_id=agent_id, tokens=tokens, cost_usd=cost_usd))
        await self.db.commit()

class SQLTaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db: AsyncSession = db

    async def get_all(self) -> list[Task]:
        result = await self.db.execute(select(TaskModel))
        return [Task.from_orm(r) for r in result.scalars()]

    async def save(self, task: Task) -> Task:
        model = TaskModel(**task.to_dict())
        self.db.add(model)
        await self.db.commit()
        return Task.from_orm(model)

# Composition root — the ONLY place that knows about concretions
def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(
        tokens=SQLTokenTracker(db),
        tasks=SQLTaskRepository(db),
    )
```

### DIP Smell Checklist

- [ ] `self.x = ConcreteClass()` inside `__init__` — should be injected
- [ ] Service imports a specific database/HTTP/cloud client at module level
- [ ] Changing the database engine requires editing business logic files
- [ ] Tests need to monkeypatch module-level globals to swap implementations

---

## SOLID in Frontend (TypeScript/React)

SOLID applies to frontend code too, adapted for React patterns:

### SRP — One Component, One Job

```tsx
// WRONG — component fetches data, formats it, and renders charts
function DashboardPage() {
  const [data, setData] = useState(null);
  useEffect(() => { fetch("/api/stats").then(r => r.json()).then(setData); }, []);
  const formatted = data ? Object.entries(data).map(/* ... */) : [];
  return <Chart data={formatted} />;
}

// CORRECT — separated into hook + formatter + component
function useDashboardStats() {
  return useQuery({ queryKey: ["stats"], queryFn: statsApi.getAll });
}

function formatChartData(stats: StatsOut): ChartData[] {
  return Object.entries(stats).map(/* ... */);
}

function DashboardPage() {
  const { data } = useDashboardStats();
  return data ? <Chart data={formatChartData(data)} /> : <Loading />;
}
```

### DIP — Depend on API Interfaces, Not Implementations

```tsx
// WRONG — component directly calls fetch with hardcoded URL
async function loadTasks() {
  const res = await fetch("http://localhost:8000/api/tasks");
  return res.json();
}

// CORRECT — abstracted API layer injected via module boundary
// src/lib/api.ts — the abstraction
export const tasksApi = {
  getAll: (): Promise<Task[]> => request<Task[]>("/tasks"),
  create: (data: CreateTask): Promise<Task> => request<Task>("/tasks", { method: "POST", body: data }),
};

// src/components/TaskList.tsx — depends on the abstraction
import { tasksApi } from "@/lib/api";

function TaskList() {
  const { data } = useQuery({ queryKey: ["tasks"], queryFn: tasksApi.getAll });
  return /* ... */;
}
```

### OCP — Extensible Component Patterns

```tsx
// WRONG — adding a new status requires editing this component
function StatusBadge({ status }: { status: string }) {
  if (status === "active") return <Chip color="success" label="Active" />;
  if (status === "blocked") return <Chip color="error" label="Blocked" />;
  if (status === "done") return <Chip color="default" label="Done" />;
  return <Chip label={status} />;
}

// CORRECT — data-driven, open for extension
const STATUS_CONFIG: Record<string, { color: ChipColor; label: string }> = {
  active:  { color: "success", label: "Active" },
  blocked: { color: "error",   label: "Blocked" },
  done:    { color: "default", label: "Done" },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? { color: "default", label: status };
  return <Chip color={config.color} label={config.label} />;
}
// Adding new status = add one line to STATUS_CONFIG, zero component changes
```

---

## Testing SOLID Compliance

### Unit Test Indicators

| Principle | Test Smell (Violation) | Healthy Test Pattern |
|-----------|----------------------|---------------------|
| SRP | Test requires 5+ mocks | Test needs 1-2 mocks |
| OCP | Test breaks when adding new variant | New variant = new test file only |
| LSP | Test uses `isinstance` to branch assertions | Same assertions for all implementations |
| ISP | Mock stubs 8 methods, test calls 2 | Mock has exactly the methods tested |
| DIP | Test monkeypatches module globals | Test injects deps via constructor |

### Integration Test Indicators

```python
# If you can swap the entire persistence layer in tests without changing
# business logic, your architecture satisfies DIP + LSP + ISP:

async def test_dashboard_with_in_memory_repo():
    service = DashboardService(
        tokens=InMemoryTokenTracker(),    # swap SQL for in-memory
        tasks=InMemoryTaskRepository(),   # zero business logic changes
    )
    summary = await service.get_summary()
    assert summary.total_tasks == 0
```

---

## Quick Reference Card

| Principle | One-liner | Violation Keyword | Fix Pattern |
|-----------|-----------|-------------------|-------------|
| **S**RP | One class = one job | "God class", "Utils" | Extract class |
| **O**CP | Extend, don't edit | `isinstance` chain | Strategy/Protocol |
| **L**SP | Subtypes = drop-in | `NotImplementedError` | Honor full contract |
| **I**SP | Small interfaces | "Fat Protocol" | Split Protocol |
| **D**IP | Inject, don't create | `self.x = Concrete()` | Constructor injection |

## See also

- Root [`CLAUDE.md`](../../CLAUDE.md) § "SOLID Principles — Mandatory" — authoritative rules
- [`CODING_PRINCIPLES.md`](CODING_PRINCIPLES.md) — Karpathy-inspired behavioral guidelines
- [`PATTERNS.md`](PATTERNS.md) — engineering behavioral and technical patterns
- [`CHECKLIST.md`](CHECKLIST.md) — quarterly audit scorecard
