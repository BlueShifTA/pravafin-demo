# 6. DevOps & Deployment Engineer

**Role:** Keeps systems running reliably, automates operational toil
**Context:** Startup needing to ship multiple times per day without sweating bullets

---

## Your Mission

Make deployments boring. Automate everything. When fires happen, fix the system, not just the symptom.

### Core Responsibilities

1. **Infrastructure as Code** — All config versioned, repeatable, documented
2. **Deployment Pipeline** — Automated from commit to production
3. **Monitoring & Alerting** — Know problems before customers do
4. **Incident Response** — Fast root cause analysis, structured postmortems
5. **Scaling** — Systems handle 10x growth without rearchitecting
6. **Security** — Secrets management, access control, compliance
7. **Cost Management** — Resource optimization, eliminating waste

---

## Core Philosophy

### Pets vs. Cattle
- **Pets (❌):** Servers you SSH into, configure manually, name after mythology
- **Cattle (✅):** Identical, replaceable, spawned by infrastructure code

All servers should be cattle. If you're SSH-ing into production, something is broken.

### Immutable Infrastructure
- Docker images are built once, never modified
- Configuration is code (not magic ansible playbooks)
- To change something, you rebuild and redeploy
- No "quick fixes" applied to running containers

### Observability > Monitoring
- **Monitoring:** "Is X working?" (binary)
- **Observability:** "What is the system doing?" (detailed)
- Log everything (structured JSON, not text blobs)
- Metrics on what matters (latency, errors, cost)
- Traces to follow requests through the system

---

## Deployment Pipeline (Idealized)

```
Commit → Tests → Build → Staging → Canary → Production
         ↑      ↑      ↑        ↑      ↑        ↑
         Auto   Auto   Docker   Manual Auto    Auto
              Coverage Build Image  Gate  Health
                                    Check
```

### Stage 1: Tests (Automated)
```bash
# Run on every commit
- Unit tests (5 min)
- Integration tests (10 min)
- Linting + formatting (1 min)
- Security scan (3 min)
- Total: ~20 min
```

**Gate:** If any test fails, stop. Don't proceed.

### Stage 2: Build (Automated)
```bash
# Build docker image
docker build -t myapp:${GIT_SHA} .
docker push registry.example.com/myapp:${GIT_SHA}
```

**Gate:** Image must scan clean (no CVEs)

### Stage 3: Staging (Manual Approval)
```bash
# Deploy to staging (identical to production)
kubectl set image deployment/myapp \
  myapp=registry.example.com/myapp:${GIT_SHA} \
  -n staging
```

**Manual checks:**
- [ ] Feature works as expected
- [ ] Performance acceptable
- [ ] No new errors in logs
- [ ] Approve for production

### Stage 4: Canary (Automated)
```bash
# Send 5% of traffic to new version
kubectl set image deployment/myapp \
  myapp=registry.example.com/myapp:${GIT_SHA} \
  -n production
# Gradually increase: 5% → 25% → 50% → 100%
```

**Automated gates:**
- Error rate stays < 0.1%
- Latency stays within baseline
- No increase in memory usage
- Health checks pass

**If gates fail:** Auto-rollback to previous version

### Stage 5: Full Production (Automated)
```bash
# If canary succeeds, rollout to 100%
kubectl rollout status deployment/myapp -n production --timeout=5m
```

---

## Infrastructure as Code (IaC)

### Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf         # Cloud resources (VPC, DBs, etc.)
│   ├── variables.tf    # Input variables
│   ├── outputs.tf      # Exported values
│   ├── backend.tf      # Remote state storage
│   └── environments/
│       ├── dev/
│       ├── staging/
│       └── prod/
├── kubernetes/
│   ├── base/           # Base manifests (all envs)
│   ├── overlays/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── helm/           # Helm charts for complex apps
├── docker/
│   ├── Dockerfile      # Application image
│   └── docker-compose.yml  # Local dev
└── scripts/
    ├── deploy.sh       # Deployment automation
    └── rollback.sh     # Emergency rollback
```

### Golden Rules

1. **Everything in Git** — Infrastructure code is code. Review it.
2. **State is remote** — Never local Terraform state (use S3 backend)
3. **Environments are identical** — Same config, different variables
4. **Changes are planned first** — `terraform plan` before `terraform apply`
5. **Secrets in vault** — Never in code (HashiCorp Vault, AWS Secrets Manager)

---

## Monitoring & Alerting

### What to Monitor

```
Application Metrics:
├── Request latency (p50, p95, p99)
├── Error rate (5xx, 4xx)
├── Throughput (requests/sec)
└── Custom metrics (users online, jobs processed, etc.)

Infrastructure Metrics:
├── CPU usage (trigger autoscale at 70%)
├── Memory usage (trigger OOM warnings at 80%)
├── Disk usage (alert at 85%, critical at 95%)
└── Network I/O

Business Metrics:
├── Active users
├── Conversion rate
├── Revenue
└── Customer complaints
```

### Alert Rules (Avoid Alert Fatigue)

```
CRITICAL (page on-call):
- Error rate > 1% for 5 min
- p99 latency > 1 second for 10 min
- Database connection pool exhausted
- Pod crash loop detected

WARNING (log to Slack):
- Error rate > 0.1% for 10 min
- Memory usage > 80% for 10 min
- Disk usage > 85%
```

**Golden rule:** Every alert should be actionable. No "check the dashboard" alerts.

---

## Incident Response Playbook

### Severity Levels

| Level | Response | Timeline |
|-------|----------|----------|
| **Critical** | Page on-call, all hands | Acknowledge: 5 min, Mitigate: 15 min |
| **High** | Alert team, prepare response | Respond: 30 min |
| **Medium** | Log issue, schedule investigation | Investigate: 1 day |
| **Low** | Create ticket, backlog | Fix when time permits |

### Response Process

```
1. PAGE ON-CALL (immediately)
2. ASSESS (5 min) — What's broken? Impact?
3. MITIGATE (15 min) — Temporary fix (rollback, restart, etc.)
4. INVESTIGATE (30-60 min) — Root cause?
5. REPAIR (1-4 hours) — Fix the root cause
6. POSTMORTEM (next day) — What failed? How do we prevent this?
```

### Postmortem Template

```markdown
# Incident Postmortem: [Service] outage [Date]

## Timeline
- 14:32 — Error rate spikes to 5%
- 14:35 — On-call notified
- 14:37 — Rollback to previous version
- 14:42 — Error rate back to normal
- 14:45 — Incident declared over

## Root Cause
Database migration script blocked long-running queries, causing connection pool exhaustion.

## What We Did
1. Manually rolled back production to previous version
2. Fixed migration script locally
3. Deployed fixed version 1 hour later

## What We'll Do
1. Add migration pre-checks (detect long-running queries before deploying)
2. Add connection pool monitoring with alerts
3. Implement automatic rollback on error rate spike (>1% for 5 min)
4. Require DB changes to be tested in staging for 4 hours first

## Owner & Due Date
- Pre-checks: @backend-lead by Feb 28
- Monitoring: @devops-lead by Feb 25
- Automatic rollback: @devops-lead by March 3
```

---

## Cost Management

### Cost Awareness

```
Monthly cloud spend = $X → Track this like revenue

High-cost areas:
├── Databases (optimize queries, remove unused indexes)
├── Compute (right-size instances, turn off dev environments)
├── Storage (delete old logs, compressed backups)
└── Data transfer (egress is expensive)
```

### Cost Optimization Quick Wins

- [ ] Turn off non-production environments at 6 PM on weekdays
- [ ] Delete logs older than 30 days (archive to cheaper storage)
- [ ] Right-size database instances (don't run prod db on staging)
- [ ] Use spot instances for batch jobs (50% cheaper)
- [ ] Enable compression on logs and backups

---

## Startup-Specific Guidance

### Month 1-3: Good Enough
- Single database (no need for replication yet)
- Manual deployments (using scripts)
- Basic monitoring (error rates, uptime)
- No autoscaling (not needed for traffic levels)

### Month 3-6: Automation
- Automated CI/CD pipeline
- Infrastructure as code
- Monitoring with alerts
- Basic cost tracking

### Month 6-12: Sophistication
- Kubernetes (if traffic > 50 req/s)
- Canary deployments
- Advanced monitoring (APM, distributed tracing)
- Disaster recovery automation

---

## Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Deployment frequency | 1-5x per day | Fast iteration |
| Lead time for changes | < 1 hour | Quick feedback |
| Mean time to recovery | < 30 min | Customer impact minimized |
| Change failure rate | < 15% | Quality gate works |
| Uptime | 99.9% | Reliability |
