---
name: seed-data
description: Seed a web app's database with realistic test data via API calls. Use when populating a fresh database for testing or demos.
allowed-tools: Bash, Read, Grep
argument-hint: [api-base-url]
---

Seed the application database with realistic test data by calling its API endpoints.

API base URL: `$ARGUMENTS` (defaults to `http://localhost:8000`)

## Steps

### 1. Discover API Endpoints

Before seeding, understand the available API:

- Check if the backend is running: `curl -sf {base_url}/health`
- If not running, tell the user to start it with `just run-backend` and stop
- Discover available routes by reading the OpenAPI spec:
  ```bash
  curl -sf {base_url}/openapi.json | python3 -m json.tool
  ```
- Identify entity types and their CRUD endpoints (POST for create, GET for list)
- Identify dependencies between entities (e.g., tasks require a project to exist first)

### 2. Check Existing Data

For each entity type, call the GET list endpoint:

```bash
curl -sf {base_url}/api/{entity}/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else len(d.get('items',d.get('results',[]))))"
```

- If data already exists, report what's present and ask the user whether to skip or add more
- If the database is empty, proceed with seeding

### 3. Seed in Dependency Order

Create entities in the correct order to satisfy foreign key relationships. Common pattern:

1. **Users/Accounts** (if applicable)
2. **Projects/Categories** (top-level groupings)
3. **Tasks/Items** (entities that belong to projects)
4. **Notes/Comments** (entities that reference tasks)
5. **Tags/Labels** (many-to-many relationships)

For each entity, use `curl` to POST realistic data:

```bash
curl -sf -X POST {base_url}/api/{entity}/ \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```

**Data quality rules:**
- Use realistic names, descriptions, and dates (not "test1", "foo", "lorem ipsum")
- Vary the data — different statuses, priorities, lengths
- Use dates relative to today for time-sensitive fields
- Create enough volume to make the UI look populated (5-15 per entity type)

### 4. Verify Data Persisted

After seeding, call GET list endpoints for each entity and verify:
- Expected count matches what was created
- No errors during creation (check HTTP status codes)

### 5. Report Summary

```
Seed complete:
- {entity1}: {count} created
- {entity2}: {count} created
- ...
Total: {total} entities across {types} types
API base: {base_url}
```

## Error Handling

- **401/403 responses:** The API requires authentication. Report this and suggest the user provide an auth token or disable auth for seeding.
- **422 responses:** Validation error. Read the response body to understand required fields and adjust the payload.
- **500 responses:** Server error. Report the endpoint and payload that failed.
- **Connection refused:** Backend is not running. Tell the user to start it.

## Notes

- This skill calls real API endpoints — it modifies the database.
- For idempotency, always check existing data before creating.
- Adapt entity names and fields to the actual API schema discovered in Step 1.
