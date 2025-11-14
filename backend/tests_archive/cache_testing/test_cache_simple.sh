#!/bin/bash
# Simple cache integration test using API calls

echo "================================================================================"
echo "Testing Company ID Cache Integration"
echo "================================================================================"
echo

# Test JD payload
JD_PAYLOAD='{
  "jd_text": "Looking for ML Engineer with Voice AI experience. Companies like Deepgram, AssemblyAI are ideal.",
  "requirements": {
    "role_title": "ML Engineer",
    "domain_expertise": ["Voice AI", "Speech Recognition"],
    "key_skills": ["Python", "Machine Learning"],
    "industries": ["AI/ML"],
    "seed_companies": ["Deepgram", "AssemblyAI"]
  }
}'

echo "TEST 1: First domain search (cold cache)"
echo "--------------------------------------------------------------------------------"
echo "Sending request to /api/domain-search..."

# Run first search
RESPONSE1=$(curl -s -X POST http://localhost:5001/api/domain-search \
  -H "Content-Type: application/json" \
  -d "$JD_PAYLOAD")

# Extract session ID
SESSION_ID1=$(echo "$RESPONSE1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('jd_id', 'unknown'))" 2>/dev/null)

echo "Session ID: $SESSION_ID1"
echo

# Wait for search to complete (check session status)
echo "Waiting for search to complete..."
sleep 15

# Get session status
STATUS1=$(curl -s "http://localhost:5001/api/research-session/$SESSION_ID1")

# Extract cache metrics
CACHE_METRICS1=$(echo "$STATUS1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(json.dumps(data.get('status_data', {}).get('cache_metrics', {}), indent=2))" 2>/dev/null)

echo
echo "FIRST SEARCH CACHE METRICS:"
echo "$CACHE_METRICS1"
echo

echo "================================================================================"
echo "TEST 2: Second search (warm cache - should have more cache hits)"
echo "================================================================================"
echo

# Run second search with same data
RESPONSE2=$(curl -s -X POST http://localhost:5001/api/domain-search \
  -H "Content-Type: application/json" \
  -d "$JD_PAYLOAD")

SESSION_ID2=$(echo "$RESPONSE2" | python3 -c "import sys, json; print(json.load(sys.stdin).get('jd_id', 'unknown'))" 2>/dev/null)

echo "Session ID: $SESSION_ID2"
echo

# Wait for search to complete
echo "Waiting for search to complete..."
sleep 15

# Get session status
STATUS2=$(curl -s "http://localhost:5001/api/research-session/$SESSION_ID2")

# Extract cache metrics
CACHE_METRICS2=$(echo "$STATUS2" | python3 -c "import sys, json; data = json.load(sys.stdin); print(json.dumps(data.get('status_data', {}).get('cache_metrics', {}), indent=2))" 2>/dev/null)

echo
echo "SECOND SEARCH CACHE METRICS:"
echo "$CACHE_METRICS2"
echo

# Extract hit counts for comparison
HITS1=$(echo "$STATUS1" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('status_data', {}).get('cache_metrics', {}).get('cache_hits', 0))" 2>/dev/null)
HITS2=$(echo "$STATUS2" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('status_data', {}).get('cache_metrics', {}).get('cache_hits', 0))" 2>/dev/null)

echo
echo "================================================================================"
echo "COMPARISON:"
echo "  First search cache hits:  $HITS1"
echo "  Second search cache hits: $HITS2"
echo "  Improvement:             +$((HITS2 - HITS1)) cache hits"
echo "================================================================================"
echo

if [ "$HITS2" -gt "$HITS1" ]; then
    echo "✅ PASS: Cache integration working! Second search had more cache hits."
    exit 0
else
    echo "⚠️  WARNING: Expected cache hit improvement on second search."
    exit 1
fi
