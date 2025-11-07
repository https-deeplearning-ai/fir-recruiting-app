# Migration Guide: From Shallow to Deep Company Research

## Overview

This guide provides a safe, gradual migration path from the current shallow research (LLM-only) to the enhanced deep research pipeline (5-phase with real data).

## Migration Strategy

### Phase 0: Current State (Baseline)

**What we have:**
- Tavily discovery finding company names
- LLM evaluation based on names only
- No real data validation
- ~60% accuracy

**Cost:** ~$3 LLM per research session

### Phase 1: Add Feature Flag (Day 1)

Add a feature flag to control which research method is used:

```python
# In company_research_service.py
class CompanyResearchConfig:
    # Add new flag
    USE_ENHANCED_RESEARCH = os.getenv("USE_ENHANCED_RESEARCH", "false").lower() == "true"
    ENHANCED_RESEARCH_PERCENTAGE = int(os.getenv("ENHANCED_RESEARCH_PERCENTAGE", "0"))
```

Modify the research method:

```python
async def _deep_research_companies(self, companies, jd_context, jd_id):
    # Check if we should use enhanced research
    if self.config.USE_ENHANCED_RESEARCH:
        # Use random sampling for gradual rollout
        import random
        if random.randint(1, 100) <= self.config.ENHANCED_RESEARCH_PERCENTAGE:
            return await self._enhanced_deep_research(companies, jd_context, jd_id)

    # Default to existing shallow research
    return await self._shallow_research_companies(companies, jd_context, jd_id)
```

### Phase 2: A/B Testing (Week 1)

**Goal:** Compare accuracy and user satisfaction

1. **Enable for 10% of requests:**
```bash
export USE_ENHANCED_RESEARCH=true
export ENHANCED_RESEARCH_PERCENTAGE=10
```

2. **Log metrics for comparison:**
```python
# Add logging to track which method was used
async def _log_research_metrics(self, method, companies, duration, cost):
    self.supabase.table("research_metrics").insert({
        "method": method,  # "shallow" or "enhanced"
        "company_count": len(companies),
        "duration_seconds": duration,
        "estimated_cost": cost,
        "timestamp": datetime.now().isoformat()
    }).execute()
```

3. **Monitor key metrics:**
- Research duration
- API costs
- Result quality
- Cache hit rates

### Phase 3: Gradual Rollout (Week 2-3)

**Progressive increase based on metrics:**

| Day | Percentage | Expected Load | Monitoring Focus |
|-----|------------|---------------|------------------|
| 1-2 | 10% | Light | Errors, timeouts |
| 3-4 | 25% | Moderate | API costs, cache hits |
| 5-7 | 50% | Half | User feedback, accuracy |
| 8-10 | 75% | Heavy | Performance, optimization |
| 11+ | 100% | Full | Stability, cost control |

**Rollout commands:**
```bash
# Day 1-2
export ENHANCED_RESEARCH_PERCENTAGE=10

# Day 3-4
export ENHANCED_RESEARCH_PERCENTAGE=25

# Day 5-7
export ENHANCED_RESEARCH_PERCENTAGE=50

# Day 8-10
export ENHANCED_RESEARCH_PERCENTAGE=75

# Day 11+ (full rollout)
export ENHANCED_RESEARCH_PERCENTAGE=100
```

### Phase 4: Optimization (Week 3-4)

**1. Implement Caching Layers:**

```python
# Add multi-level caching
class CacheManager:
    def __init__(self):
        self.memory_cache = {}  # In-memory for current session
        self.redis_cache = None  # Redis for cross-session (optional)
        self.supabase_cache = None  # Persistent cache

    async def get_company(self, company_id):
        # Check memory first (instant)
        if company_id in self.memory_cache:
            return self.memory_cache[company_id]

        # Check Redis (milliseconds)
        if self.redis_cache:
            cached = await self.redis_cache.get(f"company:{company_id}")
            if cached:
                return json.loads(cached)

        # Check Supabase (seconds)
        return await self._get_from_supabase(company_id)
```

**2. Implement Request Batching:**

```python
# Batch multiple company lookups
async def batch_validate_companies(self, company_names):
    # Group into batches of 10
    batches = [company_names[i:i+10] for i in range(0, len(company_names), 10)]

    all_results = []
    for batch in batches:
        # Parallel validation within batch
        tasks = [self._validate_single_company(name) for name in batch]
        results = await asyncio.gather(*tasks)
        all_results.extend(results)

        # Rate limit between batches
        await asyncio.sleep(0.5)

    return all_results
```

**3. Implement Progressive Loading:**

```python
# Stream results as they become available
async def stream_research_results(self, companies, jd_context):
    for company in companies:
        # Research one company
        result = await self._research_single_company(company, jd_context)

        # Stream immediately to client
        yield {
            "type": "company_result",
            "data": result,
            "progress": f"{i}/{len(companies)}"
        }
```

### Phase 5: Full Migration (Week 4+)

**1. Disable shallow research:**

```python
# Remove old code path
async def _deep_research_companies(self, companies, jd_context, jd_id):
    # Always use enhanced research
    return await self._enhanced_deep_research(companies, jd_context, jd_id)
```

**2. Clean up old code:**
- Remove `_shallow_research_companies` method
- Remove LLM-only evaluation prompts
- Update documentation

**3. Optimize defaults:**
```python
class CompanyResearchConfig:
    # Optimized settings after migration
    MAX_COMPANIES_TO_RESEARCH = 50  # Increased from 25
    CACHE_FRESHNESS_DAYS = 30  # Company data cache
    COMPETITOR_CACHE_DAYS = 7  # Competitor lists
    MAX_CONCURRENT_VALIDATIONS = 10  # Parallel operations
    USE_PROGRESSIVE_LOADING = True  # Stream results
```

## Rollback Procedures

### Quick Rollback (< 1 minute)

```bash
# Immediately disable enhanced research
export USE_ENHANCED_RESEARCH=false

# Or reduce percentage
export ENHANCED_RESEARCH_PERCENTAGE=0
```

### Gradual Rollback

```python
# Add circuit breaker pattern
class ResearchCircuitBreaker:
    def __init__(self):
        self.failure_count = 0
        self.failure_threshold = 5
        self.is_open = False

    async def call_enhanced_research(self, *args):
        if self.is_open:
            # Circuit open, use shallow research
            return await self._shallow_research(*args)

        try:
            result = await self._enhanced_research(*args)
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.is_open = True  # Open circuit
                print(f"Circuit breaker opened after {self.failure_count} failures")

            # Fallback to shallow
            return await self._shallow_research(*args)
```

## Monitoring Dashboard

### Key Metrics to Track

```sql
-- Research method distribution
SELECT
    method,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration,
    AVG(estimated_cost) as avg_cost
FROM research_metrics
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY method;

-- Cache hit rates
SELECT
    cache_type,
    SUM(hits) as total_hits,
    SUM(misses) as total_misses,
    (SUM(hits)::float / (SUM(hits) + SUM(misses))) * 100 as hit_rate
FROM cache_metrics
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY cache_type;

-- API credit usage
SELECT
    DATE(created_at) as date,
    SUM(coresignal_credits) as total_credits,
    SUM(coresignal_credits) * 0.20 as estimated_cost_usd
FROM api_usage
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at);
```

### Alert Thresholds

```yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 5%
    action: reduce_enhanced_percentage

  - name: slow_response
    condition: p95_latency > 30s
    action: investigate_bottleneck

  - name: high_cost
    condition: daily_cost > $100
    action: review_caching_strategy

  - name: low_cache_hits
    condition: cache_hit_rate < 70%
    action: investigate_cache_invalidation
```

## Success Criteria

### Week 1 Goals
- ✅ Enhanced research working for 10% of traffic
- ✅ No increase in error rates
- ✅ P95 latency < 30 seconds

### Week 2 Goals
- ✅ 50% traffic on enhanced research
- ✅ Cache hit rate > 70%
- ✅ User satisfaction score improved

### Week 3 Goals
- ✅ 100% traffic migrated
- ✅ Cost per research < $5 (with caching)
- ✅ Accuracy improved to > 90%

### Week 4 Goals
- ✅ Old code removed
- ✅ Documentation updated
- ✅ Team trained on new system

## Troubleshooting Guide

### Common Issues

**1. Claude Agent SDK Timeouts**
- **Symptom:** WebSearch phase times out frequently
- **Solution:** Increase timeout to 20s, implement retry with exponential backoff
- **Fallback:** Skip WebSearch phase, use Tavily data only

**2. CoreSignal Rate Limits**
- **Symptom:** 429 errors from CoreSignal API
- **Solution:** Add 0.5s delay between requests
- **Fallback:** Use cached data or skip validation

**3. High Costs**
- **Symptom:** Daily costs exceed budget
- **Solution:** Increase cache TTL to 60 days
- **Fallback:** Reduce sample size to 3 employees per company

**4. Slow Performance**
- **Symptom:** Research takes > 60 seconds
- **Solution:** Implement progressive loading
- **Fallback:** Reduce max_companies to 15

## Post-Migration Enhancements

### Future Improvements

1. **Machine Learning Ranking**
   - Train model on user feedback
   - Predict company relevance before deep research
   - Reduce unnecessary API calls

2. **Batch Processing API**
   - Create dedicated batch endpoint
   - Process overnight for better rates
   - Email results when complete

3. **Knowledge Graph**
   - Build persistent company relationships
   - Track company pivots and acquisitions
   - Provide historical insights

4. **Real-time Updates**
   - WebSocket for streaming results
   - Push notifications for new discoveries
   - Live collaboration features

## Conclusion

This migration plan provides a safe, measured approach to upgrading from shallow to deep company research. By following these phases, you can:

1. Minimize risk through gradual rollout
2. Maintain fallback options at each stage
3. Optimize based on real metrics
4. Achieve 10x better data quality
5. Build a foundation for future AI features

Expected timeline: 4 weeks from start to full migration
Expected improvement: 60% → 95% accuracy
Expected cost: $3 → $5 per research (with 90% cache hits)