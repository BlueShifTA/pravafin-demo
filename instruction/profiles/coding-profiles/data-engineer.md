# DATA_ENGINEER — Coding Profile

**Role:** Data Engineer (Analytics & Data Science Focus)
**Reference:** Analyzed from 55 commits (6-month analysis)
**Primary Focus:** API + Frontend (analytics focus)
**Strength:** Data processing, iterative refinement, scientific computing
**Analysis Date:** 2026-03-19

---

## 🎯 Coding Philosophy

A data engineer is **data-driven and iterative**. This profile shows:
- Data processing pipelines (concentration prediction, outlier removal)
- Feature-rich analytics (reports, visualizations, filtering)
- Incremental feature improvements (iterate based on results)
- Domain expertise in scientific computing
- Edge case handling for algorithms

**Principle:** "Build analytics features that help users understand their data"

---

## 📊 Activity Profile

| Metric | Value |
|--------|-------|
| **Typical Commit Volume** | 50+ commits/6 months |
| **Systems** | API (50%) + Frontend (45%) + Core (5%) |
| **Focus** | Analytics, data pipelines, data science |
| **Commit Pattern** | Incremental refinement |

### Commit Categories

- **Data Processing Features:** 40-50% (prediction, transformation, filtering)
- **API Endpoints:** 20-30% (evaluation, data access)
- **Frontend/Visualization:** 15-20% (charts, reports, UI)
- **Bug Fixes:** 10-15% (edge cases, data handling)

---

## 💻 Code Style & Patterns

### 1. Iterative Feature Development

**Pattern:** Small commits that each improve one aspect

```
Commit 1: Initial implementation
"Add mologram selection for analysis"

Commit 2: Bug fix from feedback
"fix concentration prediction with 1 unknown sample error"

Commit 3: Algorithm refinement
"concentration outlier_removal less aggressive"

Commit 4: Integration
"all clean up actions should allow select molograms"
```

**Philosophy:** Ship → Measure → Feedback → Improve

### 2. Edge Case Handling First

**Pattern:** Handle boundary conditions explicitly

```python
def concentration_predict(unknown_samples, known_samples):
    """Predict concentration from calibration"""

    # Edge cases FIRST
    if len(unknown_samples) == 0:
        raise ValueError("Need at least 1 unknown sample")

    if len(known_samples) == 0:
        raise ValueError("Need calibration data")

    # Normal case
    calibration = build_calibration_curve(known_samples)
    predictions = apply_calibration(unknown_samples, calibration)

    # Output validation
    assert all(0 <= p <= 100 for p in predictions)

    return predictions
```

### 3. Domain-Specific Data Structures

**Pattern:** Model domain reality

```python
class Hologram:
    """3D volumetric holographic data"""
    data: NDArray
    wavelengths: List[float]
    timestamp: datetime

class EvaluationArtifact:
    """One output of an evaluation"""
    hologram: Hologram
    concentration: float
    purity: float
    metadata: Dict
```

### 4. Flexible Querying Over Custom Endpoints

**Pattern:** Filter-based instead of many specific endpoints

```
# Instead of many custom endpoints:
GET /evaluations/holograms
GET /evaluations/processed-images
GET /evaluations/concentrations
GET /evaluations/with-tags
GET /evaluations/high-quality
GET /evaluations/failed-tests

# Use one flexible endpoint:
GET /evaluations/artifacts?type=hologram
GET /evaluations/artifacts?type=processed_image
GET /evaluations/artifacts?tags=quality,passed
GET /evaluations/artifacts?metric=concentration&min=50&max=100
```

---

## 🧪 Testing Strategy

**Approach:** Test edge cases and algorithm behavior

**Test categories:**
```
tests/
├── test_algorithms.py
│   ├── Test normal case
│   ├── Test boundary conditions (0, 1, many)
│   ├── Test invalid inputs
│   └── Test output ranges
├── test_data_handling.py
│   ├── Test data validation
│   ├── Test data transformation
│   └── Test consistency
└── test_integration.py
    ├── Test complete pipelines
    └── Test cross-system data flow
```

### Edge Case Testing

```python
def test_concentration_prediction():
    """Test prediction with different sample counts"""

    # Edge case: 1 unknown sample (minimum)
    pred_1 = predict([sample1], [cal1, cal2, cal3])
    assert 0 <= pred_1 <= 100

    # Edge case: 0 unknown samples (invalid)
    with pytest.raises(ValueError):
        predict([], [cal1, cal2, cal3])

    # Edge case: All identical samples
    pred_same = predict([s, s, s], [c, c, c])
    assert pred_same == expected_value

    # Normal case: Multiple unknowns
    pred_multi = predict([s1, s2, s3], [c1, c2, c3])
    assert len(pred_multi) == 3
```

---

## 🏗️ Architectural Decisions

### Decision 1: Evaluation Artifact Management

**Problem:** Organize, filter, display experiment outputs (images, data, metadata)

**Solution:**
```
EvaluationArtifacts = {
    holograms: [],       # Raw volumetric data
    processed: [],       # Visualization images
    metrics: {},         # Computed values
    metadata: {},        # Conditions, timestamp
    relationships: {}    # Sample → result mapping
}

API: GET /artifacts?type=hologram&tags=passed
```

### Decision 2: Algorithm Parameter Tuning

**Pattern:** Parameters are adjustable, not hardcoded

```python
# v1: Too aggressive (removes 30% of data)
OUTLIER_THRESHOLD = mean - 2*std

# v2: Less aggressive (removes 5%), keep minimum
def remove_outliers(data, threshold_sigma=0.5, min_samples=10):
    threshold = mean - threshold_sigma * std
    result = [x for x in data if x > threshold]
    return result[-min_samples:] if len(result) < min_samples else result
```

**Then iterate based on results:**
```
Measure: "Removing too much good data"
Adjust: Reduce threshold_sigma, add min_samples
Verify: Measure improvement
Commit: "outlier_removal less aggressive"
```

### Decision 3: Iterative Algorithm Refinement

**Pattern:** Hypothesis → Test → Measure → Improve

```
Hypothesis: "Outlier removal is too aggressive"
Measurement: Baseline outlier removal (30% loss)
Adjustment: Increase tolerance, add minimum samples
New measurement: New outlier removal (5% loss)
Gain: 6x improvement in data retention
Commit: "concentration outlier_removal less aggressive"
```

---

## 📝 Commit Message Style

**Approach:** Concise, domain-specific, problem-focused

```
[Problem or action]: [Impact]

"fix concentration prediction with 1 unknown sample error"
"concentration outlier_removal less aggressive"
"all clean up actions should allow select molograms"
"Show Report Points"
"Add mologram filtering by tags"
```

---

## 🚀 Key Techniques

### Technique 1: Iterative Algorithm Development

**Workflow:**
1. Implement basic version
2. Measure results on real data
3. Identify problem ("removing too much")
4. Adjust parameters
5. Verify improvement
6. Deploy and monitor

### Technique 2: Edge Case-First Development

**Pattern:** Handle boundaries before normal case

```python
# ALWAYS handle these first:
if input is None or empty:
    raise ValueError(...)

if input out of range:
    raise ValueError(...)

# Then handle normal case
```

### Technique 3: Data Validation Everywhere

**Pattern:** Validate at boundaries

```python
@app.post("/evaluate")
def evaluate(data: EvaluationRequest):
    # Input validation
    if not data.samples:
        raise ValueError("Need samples")

    # Processing
    result = process(data)

    # Output validation
    assert 0 <= result.concentration <= 100
    assert len(result.artifacts) > 0

    return result
```

### Technique 4: Flexible Querying

**Pattern:** Filter-based over custom endpoints

```python
# Good: One endpoint, many filters
GET /artifacts?type=hologram&tags=passed&metric>50

# Bad: Many endpoints
GET /holograms
GET /holograms/passed
GET /holograms/by-metric/50
```

---

## 📋 Checklist: Code Like a Data Engineer

- [ ] Handle edge cases (0, 1, many) explicitly
- [ ] Data validation at API boundaries
- [ ] Use domain terminology (holograms, molograms, artifacts)
- [ ] Flexible filters instead of hardcoded endpoints
- [ ] Iterative refinement (commit → measure → improve)
- [ ] Comprehensive data structure modeling
- [ ] Algorithm parameters configurable (not hardcoded)
- [ ] Test algorithm behavior, not just happy path
- [ ] Document data transformations
- [ ] Measure improvements empirically

---

## 🔗 Real Examples from Codebase

See mono repo for working examples:
- Concentration prediction with edge case handling
- Outlier removal tuning based on feedback
- Flexible filtering by tags and type
- Evaluation artifact management
- Data science iteration patterns

---

**Profile Created:** 2026-03-19
**Based On:** 55+ commits over 6 months
**Confidence:** High (very consistent data science approach)
**Use This For:** Data engineers, data scientists, analytics teams
