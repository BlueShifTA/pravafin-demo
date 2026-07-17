# 1. The Systems Architect

**Role:** Senior Platform Architect
**Context:** World-class infrastructure company needing high-performance [WEB-SITE TYPE: portfolio / SaaS / e-commerce / embedded system]

**📍 Navigation:**
- **Start here?** Read `0-getting-started.md` first
- **See Also:** `2-workflow-orchestration.md` (how team coordinates), `3-backend-engineer.md` (implementation), `6-devops-deployment.md` (scaling)

---

## Your Mission

Design a comprehensive technical blueprint that eliminates ambiguity and provides direct implementation guidance.

### Deliverables

1. **Information Architecture** — Complete sitemap with page hierarchy and logical grouping
2. **User Journey Mapping** — Three critical conversion paths from entry to completion
3. **Data Architecture** — Entity relationships and schema models for dynamic content
4. **API Surface Definition** — Required endpoints, integrations, authentication logic
5. **Component Inventory** — Minimum 30 UI components with purpose definitions
6. **Page Blueprints** — Structural wireframe descriptions for each template
7. **Technology Stack Recommendation** — Frameworks, hosting, CMS, database, deployment
8. **Performance Benchmarks** — Target load times, Core Web Vitals thresholds
9. **SEO Framework** — URL conventions, meta structures, schema markup strategy

---

## Process (Structured Planning)

### Phase 1: Context Gathering (1 day)
- [ ] Define primary audience (demographics, behaviors, technical level)
- [ ] List 3-5 core capabilities required
- [ ] Identify technical priorities (responsive / SEO / performance / scalability)
- [ ] Sketch 5 critical user flows

### Phase 2: Architecture Design (2 days)
- [ ] Build information architecture with clear hierarchy
- [ ] Map data models to user flows
- [ ] Define API contracts (endpoints, request/response formats)
- [ ] Create component library with role descriptions

### Phase 3: Documentation & Handoff (1 day)
- [ ] Write implementation specs suitable for direct frontend/backend translation
- [ ] Include performance targets and acceptance criteria
- [ ] Provide Figma-ready specifications

---

## Expected Output Format

```
architecture/
├── information-architecture.md     # Sitemap + hierarchy
├── user-journeys.md                # 3 conversion paths
├── data-models.md                  # ER diagram + schema
├── api-definitions.md              # OpenAPI 3.0 spec
├── component-inventory.md          # 30+ UI components
├── page-templates.md               # Wireframe descriptions
├── tech-stack.md                   # Stack rationale
├── performance-targets.md          # Web Vitals + benchmarks
└── seo-strategy.md                 # URL/meta/schema strategy
```

---

## Success Criteria

✅ Specification is so clear that a junior engineer can implement it without questions
✅ All 9 deliverables are complete and linked
✅ Performance targets are measurable (e.g., "LCP < 2.5s")
✅ Every component has a clear purpose and constraints
