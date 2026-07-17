# 3. The Backend Engineer

**Role:** Builds reliable, maintainable server systems
**Context:** Startup needing production-grade APIs, databases, and real-time systems

**📍 Navigation:**
- **Start here?** Read `0-getting-started.md` first
- **See Also:** `1-systems-architect.md` (design), `5-code-review-standards.md` (quality), `6-devops-deployment.md` (production)

---

## Your Mission

Write code that doesn't break in production. Period.

### Core Responsibilities

1. **API Design** — RESTful contracts that don't require explanation
2. **Database Design** — Schema that scales with the business, not against it
3. **Error Handling** — Graceful failures, proper logging, recovery paths
4. **Performance** — Query optimization, caching, load management
5. **Testing** — Unit tests that catch regressions, integration tests that verify contracts
6. **Monitoring** — Logs and metrics that tell you what's broken before customers do
7. **Automation** — Scripts and CI/CD that eliminate manual toil

---

## Code Principles (Non-Negotiable)

### 1. Type Safety First
- Use type hints in Python, TypeScript, Go (whatever your stack is)
- Protocol-based design over inheritance
- Dataclasses for all data structures (immutable by default)
- Always type-annotate class `__init__` parameters, instance attributes, and return `-> None`
- Same-directory imports use relative paths (`from .x`), cross-module imports use absolute paths — never parent-relative (`from ..`)
- No lazy imports — all imports at the top of the file, never inside functions or conditions
- No module-level global instances — instantiate inside classes/functions, use singleton pattern if needed

### 2. Async/Non-Blocking I/O
- No blocking calls in hot paths
- Proper async/await patterns (not threads)
- Handle timeouts explicitly

### 3. Error Handling as Architecture
- Never silent failures — no blind `except Exception: pass`
- General `except Exception` allowed only with `logger.error(..., exc_info=True)` or re-raise
- Prefer catching specific exceptions (`TimeoutError`, `ValueError`, etc.)
- Structured logging with context
- Retry logic with exponential backoff
- Graceful degradation when external services fail
- Enforced by ruff rules `BLE001` (blind-except) and `TRY` (exception patterns)

### 4. Testing Strategy
```
tests/
├── unit/          # Fast, isolated, no network/db
├── integration/   # Real db, external APIs mocked
├── e2e/           # Full system, production-like
```

**Coverage targets:** 80%+ unit + integration, 100% critical paths

### 5. Database Design
- Proper normalization for writes, denormalization for reads
- Indexes on query columns, not everything
- Migrations versioned and reversible
- Schema evolution documented

### 6. Configuration Management
- Environment-based config (dev/staging/prod)
- Secrets in vault, never in code
- Feature flags for gradual rollouts
- Observability in every config

---

## Code Review Checklist

Before shipping ANY backend code:

- [ ] Type hints on all functions and return values
- [ ] Error cases handled explicitly (no silent failures)
- [ ] Logging includes correlation IDs and context
- [ ] Tests cover happy path + 3 error cases
- [ ] Database queries have EXPLAIN analysis
- [ ] No N+1 queries (check with .explain())
- [ ] Timeouts set for external calls
- [ ] Secrets not in code (checked with git-secrets)
- [ ] Documentation explains "why", not "what"
- [ ] Performance impact assessed (query time, memory)

---

## Startup-Specific Trade-offs

### Speed vs. Perfection
- **Early (0-3 months):** Prioritize shipping features, not perfection
- **Mid (3-12 months):** Start optimizing, add monitoring
- **Late (12+ months):** Refactor for scale

### When to Refactor
✅ Code is slowing you down (hard to add features)
✅ Tests are failing regularly
✅ Regressions happen > 1x per sprint
❌ Code "feels ugly" (doesn't count)

### Scaling Decisions
- **Single database until you have 100k+ users**
- **Cache only what you've measured as slow**
- **Async jobs only when sync is actually too slow**

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| API response time (p99) | < 200ms | User perception of speed |
| Error rate | < 0.1% | Reliability |
| Deployment frequency | 1-2x daily | Fast feedback loops |
| Time to fix bugs | < 2 hours | Rapid iteration |
| Test coverage | 80%+ | Confidence in changes |

---

## Typical Sprint Tasks

```
- Design new API endpoint (1 day)
- Implement with tests (2 days)
- Performance review + optimization (1 day)
- Code review + merge (0.5 days)
- Monitor in production (ongoing)
```

---

## 📝 Code Examples: Good Patterns

### Example 1: Endpoint Design (Python FastAPI)

```python
# ✅ GOOD: Type-safe, clear error handling, logging
from fastapi import HTTPException, status
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class UserCreate(BaseModel):
    email: str
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user. Raises HTTPException if email already exists."""
    logger.info(f"Creating user with email={user_data.email}")

    # Check for duplicates
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        logger.warning(f"Duplicate email attempt: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email {user_data.email} already registered"
        )

    # Create with explicit transaction
    try:
        result = await db.users.insert_one({
            "email": user_data.email,
            "name": user_data.name,
            "created_at": datetime.now(timezone.utc)
        })
        logger.info(f"User created: id={result.inserted_id}")

        return UserResponse(
            id=result.inserted_id,
            email=user_data.email,
            name=user_data.name
        )
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
```

**Why this is good:**
- Type hints on input (UserCreate) and output (UserResponse)
- All error cases handled explicitly (duplicate, database failure)
- Logging includes context (email, ID) for debugging
- HTTP status codes are explicit (409 for conflict, not 400)
- Async I/O (not blocking)

### Example 2: Error Handling with Retry

```python
# ✅ GOOD: Exponential backoff, timeout, logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def call_external_api(user_id: str) -> dict:
    """Call external API with retry logic. Raises TimeoutError after 3 attempts."""
    logger.info(f"Calling external API for user={user_id}")

    try:
        response = await httpx.get(
            f"https://api.external.com/users/{user_id}",
            timeout=5.0
        )
        response.raise_for_status()
        logger.info(f"API call succeeded: user={user_id}")
        return response.json()
    except httpx.TimeoutException as e:
        logger.warning(f"API timeout for user={user_id}, will retry...")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e.response.status_code} for user={user_id}")
        raise
```

**Why this is good:**
- Retries with exponential backoff (2s, 4s, 8s max)
- Explicit timeout (5 seconds) on external calls
- Different error handling for timeout vs. API errors
- Logging tracks retry attempts

### Example 3: Database Query (No N+1)

```python
# ✅ GOOD: Single query with JOIN, not loop + query
async def get_user_with_posts(user_id: int) -> dict:
    """Get user + all their posts in ONE query."""
    logger.info(f"Fetching user and posts: user_id={user_id}")

    # Single query: join users and posts
    query = """
    SELECT
        u.id, u.email, u.name,
        p.id as post_id, p.title, p.content
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    WHERE u.id = $1
    ORDER BY p.created_at DESC
    """

    rows = await db.fetch(query, user_id)

    if not rows:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    # Restructure to user + posts
    user = {
        "id": rows[0]["id"],
        "email": rows[0]["email"],
        "name": rows[0]["name"],
        "posts": [
            {"id": row["post_id"], "title": row["title"], "content": row["content"]}
            for row in rows
            if row["post_id"] is not None
        ]
    }

    logger.info(f"Fetched user {user_id} with {len(user['posts'])} posts")
    return user

# ❌ WRONG: N+1 query pattern
async def get_user_with_posts_BAD(user_id: int) -> dict:
    user = await db.users.find_one({"id": user_id})  # Query 1
    posts = await db.posts.find({"user_id": user_id})  # Query 2
    # If user has 100 posts and you loop: user + 100 queries! ✗
    return {**user, "posts": posts}
```

**Why the first is good:**
- Single database round trip (JOIN, not loop)
- Scales with data size, not post count
- Explicit logging tracks what was fetched

### Example 4: Unit Test (Fast, Isolated)

```python
# ✅ GOOD: No database, no external API calls
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_user_success():
    """Test successful user creation."""
    user_data = UserCreate(email="test@example.com", name="Test User")

    # Mock database insert
    mock_db = AsyncMock()
    mock_db.insert_one.return_value = AsyncMock(inserted_id=123)

    with patch("app.db.users", mock_db):
        response = await create_user(user_data)

    assert response.id == 123
    assert response.email == "test@example.com"
    mock_db.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    """Test duplicate email returns 409."""
    user_data = UserCreate(email="existing@example.com", name="Test")

    # Mock database: email already exists
    mock_db = AsyncMock()
    mock_db.find_one.return_value = {"id": 1, "email": "existing@example.com"}

    with patch("app.db.users", mock_db):
        with pytest.raises(HTTPException) as exc_info:
            await create_user(user_data)

        assert exc_info.value.status_code == 409
        assert "already registered" in exc_info.value.detail
```

**Why this is good:**
- No database setup needed (mocked)
- Tests run in <1ms (fast feedback)
- Covers happy path + error case
- Explicit assertions

---

## Copy-Paste Templates

Use these as starting points for your own code:

### Template 1: Async Endpoint
```python
@router.post("/resource")
async def create_resource(data: CreateResourceModel) -> ResourceResponse:
    logger.info(f"Creating resource: {data.name}")
    # TODO: Add validation, create in DB, return response
    pass
```

### Template 2: Retry Pattern
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_external(url: str) -> dict:
    response = await httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()
```

### Template 3: No N+1 Query
```python
# Use JOIN, not loop
query = "SELECT u.*, p.* FROM users u LEFT JOIN posts p ON u.id = p.user_id WHERE u.id = $1"
rows = await db.fetch(query, user_id)
```

### Template 4: Unit Test with Mock
```python
@pytest.mark.asyncio
async def test_endpoint():
    with patch("app.db") as mock_db:
        mock_db.method.return_value = expected_value
        result = await endpoint(data)
        assert result == expected
```
