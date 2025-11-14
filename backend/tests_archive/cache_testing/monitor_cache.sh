#!/bin/bash

# ============================================================================
# Company Cache Monitor Script
# ============================================================================
# This script monitors backend logs for cache-related activity in real-time
# Usage: ./monitor_cache.sh [mode]
#   Modes: watch (default), summary, test
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file location
LOG_FILE="${LOG_FILE:-/tmp/backend_test.log}"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}❌ Error: Log file not found at $LOG_FILE${NC}"
    echo "Make sure the backend is running and logging to this file."
    exit 1
fi

# ============================================================================
# Mode 1: Watch Mode (Real-time monitoring)
# ============================================================================
watch_mode() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         Company Cache Monitor - Real-Time Watch Mode           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Monitoring: $LOG_FILE${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Watch for cache-related log patterns with color highlighting
    tail -f "$LOG_FILE" | while read line; do
        # Cache hits (green)
        if [[ "$line" == *"[CACHE HIT]"* ]]; then
            echo -e "${GREEN}$line${NC}"

        # Cache saves success (green)
        elif [[ "$line" == *"[CACHE] ✅ Saved"* ]]; then
            echo -e "${GREEN}$line${NC}"

        # Cache misses (yellow)
        elif [[ "$line" == *"[CACHE MISS]"* ]]; then
            echo -e "${YELLOW}$line${NC}"

        # Cache save failures (red)
        elif [[ "$line" == *"[CACHE] ❌ Failed"* ]]; then
            echo -e "${RED}$line${NC}"

        # Cache performance summary (cyan)
        elif [[ "$line" == *"Cache Performance"* ]] || [[ "$line" == *"Cache Hits:"* ]] || [[ "$line" == *"Credits Saved:"* ]]; then
            echo -e "${CYAN}$line${NC}"

        # Company ID lookup header (purple)
        elif [[ "$line" == *"Looking up CoreSignal company IDs"* ]]; then
            echo -e "${PURPLE}$line${NC}"

        # Other cache-related lines (default)
        elif [[ "$line" == *"CACHE"* ]] || [[ "$line" == *"cache"* ]]; then
            echo "$line"
        fi
    done
}

# ============================================================================
# Mode 2: Summary Mode (Recent activity summary)
# ============================================================================
summary_mode() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          Company Cache Monitor - Summary Mode                  ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Get recent cache activity
    RECENT_LINES=$(tail -200 "$LOG_FILE")

    # Count cache hits
    CACHE_HITS=$(echo "$RECENT_LINES" | grep -c "\[CACHE HIT\]" || true)

    # Count cache misses
    CACHE_MISSES=$(echo "$RECENT_LINES" | grep -c "\[CACHE MISS\]" || true)

    # Count cache saves (success)
    CACHE_SAVES=$(echo "$RECENT_LINES" | grep -c "\[CACHE\] ✅ Saved" || true)

    # Count cache save failures
    CACHE_FAILURES=$(echo "$RECENT_LINES" | grep -c "\[CACHE\] ❌ Failed" || true)

    # Calculate save success rate
    TOTAL_SAVES=$((CACHE_SAVES + CACHE_FAILURES))
    if [ $TOTAL_SAVES -gt 0 ]; then
        SAVE_SUCCESS_RATE=$(echo "scale=1; $CACHE_SAVES * 100 / $TOTAL_SAVES" | bc)
    else
        SAVE_SUCCESS_RATE="N/A"
    fi

    # Calculate hit rate
    TOTAL_LOOKUPS=$((CACHE_HITS + CACHE_MISSES))
    if [ $TOTAL_LOOKUPS -gt 0 ]; then
        HIT_RATE=$(echo "scale=1; $CACHE_HITS * 100 / $TOTAL_LOOKUPS" | bc)
    else
        HIT_RATE="N/A"
    fi

    # Extract most recent cache performance metrics from logs
    LAST_PERFORMANCE=$(echo "$RECENT_LINES" | grep -A 3 "Cache Performance:" | tail -4 || true)

    # Display summary
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Recent Activity (last 200 log lines):${NC}"
    echo ""

    if [ $CACHE_HITS -gt 0 ] || [ $CACHE_MISSES -gt 0 ]; then
        echo -e "  ${GREEN}✅ Cache Hits:${NC} $CACHE_HITS"
        echo -e "  ${YELLOW}⊗ Cache Misses:${NC} $CACHE_MISSES"
        if [ "$HIT_RATE" != "N/A" ]; then
            echo -e "  ${CYAN}📊 Hit Rate:${NC} $HIT_RATE%"
        fi
        echo ""
    fi

    if [ $TOTAL_SAVES -gt 0 ]; then
        echo -e "  ${GREEN}✅ Cache Saves (Success):${NC} $CACHE_SAVES"
        echo -e "  ${RED}❌ Cache Saves (Failed):${NC} $CACHE_FAILURES"
        if [ "$SAVE_SUCCESS_RATE" != "N/A" ]; then
            echo -e "  ${CYAN}📊 Save Success Rate:${NC} $SAVE_SUCCESS_RATE%"
        fi
        echo ""
    fi

    if [ -n "$LAST_PERFORMANCE" ]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Last Cache Performance Summary:${NC}"
        echo ""
        echo -e "${CYAN}$LAST_PERFORMANCE${NC}"
        echo ""
    fi

    # Show recent errors if any
    RECENT_ERRORS=$(echo "$RECENT_LINES" | grep "\[CACHE\] ❌ Failed" | tail -5)
    if [ -n "$RECENT_ERRORS" ]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}⚠️  Recent Cache Errors (last 5):${NC}"
        echo ""
        echo -e "${RED}$RECENT_ERRORS${NC}"
        echo ""
    fi

    # Status assessment
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Cache System Status:${NC}"
    echo ""

    if [ $CACHE_FAILURES -gt 0 ] && [ $TOTAL_SAVES -gt 0 ]; then
        FAILURE_PCT=$(echo "scale=1; $CACHE_FAILURES * 100 / $TOTAL_SAVES" | bc)
        FAILURE_PCT_INT=$(echo "$FAILURE_PCT" | cut -d. -f1)

        if [ "$FAILURE_PCT_INT" -gt 10 ]; then
            echo -e "  ${RED}❌ STATUS: CRITICAL - High save failure rate ($SAVE_SUCCESS_RATE% success)${NC}"
            echo -e "  ${RED}   Action: Check if database schema fix is applied${NC}"
            echo -e "  ${RED}   Run: ALTER TABLE company_lookup_cache ALTER COLUMN website DROP NOT NULL;${NC}"
        elif [ "$FAILURE_PCT_INT" -gt 5 ]; then
            echo -e "  ${YELLOW}⚠️  STATUS: WARNING - Moderate save failures ($SAVE_SUCCESS_RATE% success)${NC}"
            echo -e "  ${YELLOW}   Action: Monitor for increasing failures${NC}"
        else
            echo -e "  ${GREEN}✅ STATUS: GOOD - Save success rate: $SAVE_SUCCESS_RATE%${NC}"
        fi
    elif [ $TOTAL_SAVES -eq 0 ] && [ $CACHE_HITS -eq 0 ] && [ $CACHE_MISSES -eq 0 ]; then
        echo -e "  ${YELLOW}⏳ STATUS: IDLE - No recent cache activity${NC}"
        echo -e "  ${YELLOW}   Waiting for company research searches...${NC}"
    elif [ $CACHE_HITS -gt 0 ] && [ "$HIT_RATE" != "N/A" ]; then
        HIT_RATE_INT=$(echo "$HIT_RATE" | cut -d. -f1)
        if [ "$HIT_RATE_INT" -gt 90 ]; then
            echo -e "  ${GREEN}✅ STATUS: EXCELLENT - High cache hit rate ($HIT_RATE%)${NC}"
            echo -e "  ${GREEN}   Cache is working perfectly!${NC}"
        elif [ "$HIT_RATE_INT" -gt 50 ]; then
            echo -e "  ${GREEN}✅ STATUS: GOOD - Moderate cache hit rate ($HIT_RATE%)${NC}"
        else
            echo -e "  ${YELLOW}⚠️  STATUS: WARMING UP - Low hit rate ($HIT_RATE%)${NC}"
            echo -e "  ${YELLOW}   This is normal for new searches${NC}"
        fi
    else
        echo -e "  ${GREEN}✅ STATUS: OPERATIONAL${NC}"
    fi

    echo ""
}

# ============================================================================
# Mode 3: Test Mode (Quick test verification)
# ============================================================================
test_mode() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Company Cache Monitor - Test Mode                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}This mode checks for signs of successful cache testing${NC}"
    echo ""

    # Get recent cache activity
    RECENT_LINES=$(tail -500 "$LOG_FILE")

    # Look for cache performance summaries
    PERFORMANCE_BLOCKS=$(echo "$RECENT_LINES" | grep -B 2 -A 3 "Cache Performance:" || true)

    if [ -z "$PERFORMANCE_BLOCKS" ]; then
        echo -e "${RED}❌ No cache performance data found in recent logs${NC}"
        echo -e "${YELLOW}   Make sure you've run at least one company research search${NC}"
        exit 1
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Recent Cache Performance Summaries:${NC}"
    echo ""
    echo -e "${CYAN}$PERFORMANCE_BLOCKS${NC}"
    echo ""

    # Count number of searches
    NUM_SEARCHES=$(echo "$PERFORMANCE_BLOCKS" | grep -c "Cache Performance:" || true)

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test Analysis:${NC}"
    echo ""
    echo -e "  ${CYAN}Number of searches detected:${NC} $NUM_SEARCHES"

    # Extract metrics from most recent two searches
    LAST_TWO=$(echo "$PERFORMANCE_BLOCKS" | grep -A 3 "Cache Performance:" | tail -8)

    # Check if we have at least 2 searches for comparison
    if [ $NUM_SEARCHES -ge 2 ]; then
        echo ""
        echo -e "  ${GREEN}✅ Multiple searches detected - good for testing cache hits!${NC}"
        echo ""

        # Try to extract hit rates from last two searches
        HIT_RATE_1=$(echo "$LAST_TWO" | grep "Cache Hits:" | tail -2 | head -1 | grep -oP '\d+\.\d+%' || echo "N/A")
        HIT_RATE_2=$(echo "$LAST_TWO" | grep "Cache Hits:" | tail -1 | grep -oP '\d+\.\d+%' || echo "N/A")

        echo -e "  ${CYAN}Previous search hit rate:${NC} $HIT_RATE_1"
        echo -e "  ${CYAN}Latest search hit rate:${NC} $HIT_RATE_2"
        echo ""

        # If second search has high hit rate, cache is working!
        if [[ "$HIT_RATE_2" =~ ^[0-9.]+% ]]; then
            HIT_PCT=$(echo "$HIT_RATE_2" | grep -oP '\d+' | head -1)
            if [ "$HIT_PCT" -gt 90 ]; then
                echo -e "  ${GREEN}🎉 EXCELLENT! Cache is working perfectly (${HIT_RATE_2} hit rate)${NC}"
                echo -e "  ${GREEN}   This indicates successful cache accumulation!${NC}"
            elif [ "$HIT_PCT" -gt 50 ]; then
                echo -e "  ${GREEN}✅ GOOD! Cache is working (${HIT_RATE_2} hit rate)${NC}"
            else
                echo -e "  ${YELLOW}⚠️  Low hit rate (${HIT_RATE_2}) - possibly different search queries${NC}"
            fi
        fi

        # Check for cost savings
        COST_SAVED=$(echo "$LAST_TWO" | grep "Credits Saved:" | tail -1 | grep -oP '\$\d+\.\d+' || echo "N/A")
        if [ "$COST_SAVED" != "N/A" ]; then
            echo -e "  ${GREEN}💰 Cost savings in latest search:${NC} $COST_SAVED"
        fi
    else
        echo ""
        echo -e "  ${YELLOW}⏳ Only 1 search detected${NC}"
        echo -e "  ${YELLOW}   Run a second search with the same query to test cache hits${NC}"
    fi

    echo ""

    # Check for save errors
    SAVE_ERRORS=$(echo "$RECENT_LINES" | grep "\[CACHE\] ❌ Failed" | tail -3)
    if [ -n "$SAVE_ERRORS" ]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}⚠️  WARNING: Cache save errors detected${NC}"
        echo ""
        echo -e "${RED}Recent errors:${NC}"
        echo -e "${RED}$SAVE_ERRORS${NC}"
        echo ""
        echo -e "${YELLOW}If you see '23502' error code, the database schema fix is not applied.${NC}"
        echo -e "${YELLOW}Run: ALTER TABLE company_lookup_cache ALTER COLUMN website DROP NOT NULL;${NC}"
    else
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}✅ No cache save errors detected${NC}"
    fi

    echo ""
}

# ============================================================================
# Main Script
# ============================================================================

MODE="${1:-watch}"

case "$MODE" in
    watch)
        watch_mode
        ;;
    summary)
        summary_mode
        ;;
    test)
        test_mode
        ;;
    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo ""
        echo "Usage: $0 [mode]"
        echo ""
        echo "Modes:"
        echo "  watch   - Real-time monitoring of cache activity (default)"
        echo "  summary - Summary of recent cache activity"
        echo "  test    - Quick verification for cache testing"
        echo ""
        exit 1
        ;;
esac
