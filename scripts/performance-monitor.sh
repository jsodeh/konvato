#!/bin/bash

# Performance Monitoring Script for Betslip Converter
# Monitors API performance, cache efficiency, and system resources

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:5000}"
MONITOR_DURATION="${MONITOR_DURATION:-300}" # 5 minutes default
RESULTS_DIR="./performance-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "📊 Starting Performance Monitoring for Betslip Converter"
echo "📍 Target: $API_BASE_URL"
echo "⏱️  Duration: ${MONITOR_DURATION}s"
echo "📅 Timestamp: $TIMESTAMP"
echo "----------------------------------------"

# Performance metrics storage
declare -a response_times=()
declare -a cache_hit_rates=()
declare -a memory_usage=()
declare -a success_rates=()

# Function to log performance data
log_performance() {
    local metric="$1"
    local value="$2"
    local timestamp="$3"
    
    echo "[$timestamp] $metric: $value" >> "$RESULTS_DIR/performance_$TIMESTAMP.log"
}

# Function to test API response time
test_response_time() {
    local start_time=$(date +%s.%N)
    
    response=$(curl -s -w "%{http_code}" -X POST "$API_BASE_URL/api/convert" \
        -H "Content-Type: application/json" \
        -d '{"betslipCode":"PERF123","sourceBookmaker":"bet9ja","destinationBookmaker":"sportybet"}' \
        -o /tmp/perf_test.json 2>/dev/null || echo "000")
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l)
    
    echo "$duration:$response"
}

# Function to get cache statistics
get_cache_stats() {
    cache_response=$(curl -s "$API_BASE_URL/api/cache/stats" 2>/dev/null || echo '{"hitRate":0}')
    hit_rate=$(echo "$cache_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('hitRate', 0))" 2>/dev/null || echo "0")
    echo "$hit_rate"
}

# Function to get system health
get_system_health() {
    health_response=$(curl -s "$API_BASE_URL/api/health" 2>/dev/null || echo '{"memory":{"rss":0}}')
    memory_rss=$(echo "$health_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('memory', {}).get('rss', 0))" 2>/dev/null || echo "0")
    memory_mb=$(echo "scale=2; $memory_rss / 1024 / 1024" | bc -l 2>/dev/null || echo "0")
    echo "$memory_mb"
}

# Function to calculate statistics
calculate_stats() {
    local -n arr=$1
    local sum=0
    local count=${#arr[@]}
    
    if [ $count -eq 0 ]; then
        echo "0:0:0" # avg:min:max
        return
    fi
    
    local min=${arr[0]}
    local max=${arr[0]}
    
    for value in "${arr[@]}"; do
        sum=$(echo "$sum + $value" | bc -l)
        if (( $(echo "$value < $min" | bc -l) )); then
            min=$value
        fi
        if (( $(echo "$value > $max" | bc -l) )); then
            max=$value
        fi
    done
    
    local avg=$(echo "scale=3; $sum / $count" | bc -l)
    echo "$avg:$min:$max"
}

# Main monitoring loop
echo "🚀 Starting performance monitoring..."
start_time=$(date +%s)
end_time=$((start_time + MONITOR_DURATION))
test_count=0
success_count=0

while [ $(date +%s) -lt $end_time ]; do
    current_time=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Test API response time
    result=$(test_response_time)
    response_time=$(echo "$result" | cut -d':' -f1)
    http_code=$(echo "$result" | cut -d':' -f2)
    
    response_times+=("$response_time")
    test_count=$((test_count + 1))
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "400" ]; then
        success_count=$((success_count + 1))
    fi
    
    # Get cache statistics
    cache_hit_rate=$(get_cache_stats)
    cache_hit_rates+=("$cache_hit_rate")
    
    # Get memory usage
    memory_mb=$(get_system_health)
    memory_usage+=("$memory_mb")
    
    # Log current metrics
    log_performance "RESPONSE_TIME" "$response_time" "$current_time"
    log_performance "HTTP_CODE" "$http_code" "$current_time"
    log_performance "CACHE_HIT_RATE" "$cache_hit_rate" "$current_time"
    log_performance "MEMORY_MB" "$memory_mb" "$current_time"
    
    # Display real-time stats
    printf "\r⏱️  Time: %.1fs | Tests: %d | Success: %d | Avg Response: %.2fs | Cache Hit: %.1f%% | Memory: %.1fMB" \
        "$response_time" "$test_count" "$success_count" \
        "$(echo "scale=2; $response_time" | bc -l)" \
        "$(echo "scale=1; $cache_hit_rate * 100" | bc -l)" \
        "$memory_mb"
    
    sleep 5
done

echo ""
echo ""
echo "📈 Performance Analysis Complete"
echo "----------------------------------------"

# Calculate final statistics
response_stats=$(calculate_stats response_times)
cache_stats=$(calculate_stats cache_hit_rates)
memory_stats=$(calculate_stats memory_usage)

response_avg=$(echo "$response_stats" | cut -d':' -f1)
response_min=$(echo "$response_stats" | cut -d':' -f2)
response_max=$(echo "$response_stats" | cut -d':' -f3)

cache_avg=$(echo "$cache_stats" | cut -d':' -f1)
cache_min=$(echo "$cache_stats" | cut -d':' -f2)
cache_max=$(echo "$cache_stats" | cut -d':' -f3)

memory_avg=$(echo "$memory_stats" | cut -d':' -f1)
memory_min=$(echo "$memory_stats" | cut -d':' -f2)
memory_max=$(echo "$memory_stats" | cut -d':' -f3)

success_rate=$(echo "scale=1; $success_count * 100 / $test_count" | bc -l)

# Display results
echo "🎯 Performance Summary"
echo "----------------------------------------"
echo "Total Tests: $test_count"
echo "Successful Tests: $success_count"
echo -e "Success Rate: ${GREEN}${success_rate}%${NC}"
echo ""

echo "⚡ Response Time Analysis"
echo "Average: ${response_avg}s"
echo "Minimum: ${response_min}s"
echo "Maximum: ${response_max}s"

# Response time assessment
if (( $(echo "$response_avg < 20" | bc -l) )); then
    echo -e "Assessment: ${GREEN}EXCELLENT${NC} (< 20s)"
elif (( $(echo "$response_avg < 30" | bc -l) )); then
    echo -e "Assessment: ${GREEN}GOOD${NC} (< 30s)"
elif (( $(echo "$response_avg < 45" | bc -l) )); then
    echo -e "Assessment: ${YELLOW}ACCEPTABLE${NC} (< 45s)"
else
    echo -e "Assessment: ${RED}NEEDS IMPROVEMENT${NC} (> 45s)"
fi

echo ""
echo "💾 Cache Performance"
cache_avg_percent=$(echo "scale=1; $cache_avg * 100" | bc -l)
echo "Average Hit Rate: ${cache_avg_percent}%"
echo "Minimum Hit Rate: $(echo "scale=1; $cache_min * 100" | bc -l)%"
echo "Maximum Hit Rate: $(echo "scale=1; $cache_max * 100" | bc -l)%"

# Cache assessment
if (( $(echo "$cache_avg > 0.8" | bc -l) )); then
    echo -e "Assessment: ${GREEN}EXCELLENT${NC} (> 80%)"
elif (( $(echo "$cache_avg > 0.6" | bc -l) )); then
    echo -e "Assessment: ${GREEN}GOOD${NC} (> 60%)"
elif (( $(echo "$cache_avg > 0.4" | bc -l) )); then
    echo -e "Assessment: ${YELLOW}ACCEPTABLE${NC} (> 40%)"
else
    echo -e "Assessment: ${RED}NEEDS IMPROVEMENT${NC} (< 40%)"
fi

echo ""
echo "🧠 Memory Usage"
echo "Average: ${memory_avg}MB"
echo "Minimum: ${memory_min}MB"
echo "Maximum: ${memory_max}MB"

# Memory assessment
if (( $(echo "$memory_avg < 512" | bc -l) )); then
    echo -e "Assessment: ${GREEN}EXCELLENT${NC} (< 512MB)"
elif (( $(echo "$memory_avg < 1024" | bc -l) )); then
    echo -e "Assessment: ${GREEN}GOOD${NC} (< 1GB)"
elif (( $(echo "$memory_avg < 2048" | bc -l) )); then
    echo -e "Assessment: ${YELLOW}ACCEPTABLE${NC} (< 2GB)"
else
    echo -e "Assessment: ${RED}HIGH USAGE${NC} (> 2GB)"
fi

# Generate performance score
score=0

# Response time score (40% weight)
if (( $(echo "$response_avg < 20" | bc -l) )); then
    score=$((score + 40))
elif (( $(echo "$response_avg < 30" | bc -l) )); then
    score=$((score + 30))
elif (( $(echo "$response_avg < 45" | bc -l) )); then
    score=$((score + 20))
fi

# Cache hit rate score (30% weight)
cache_score=$(echo "scale=0; $cache_avg * 30" | bc -l)
score=$((score + cache_score))

# Success rate score (20% weight)
success_score=$(echo "scale=0; $success_rate * 20 / 100" | bc -l)
score=$((score + success_score))

# Memory efficiency score (10% weight)
if (( $(echo "$memory_avg < 512" | bc -l) )); then
    score=$((score + 10))
elif (( $(echo "$memory_avg < 1024" | bc -l) )); then
    score=$((score + 8))
elif (( $(echo "$memory_avg < 2048" | bc -l) )); then
    score=$((score + 5))
fi

echo ""
echo "🏆 Overall Performance Score: ${score}/100"

if [ $score -ge 90 ]; then
    echo -e "Performance Grade: ${GREEN}A (EXCELLENT)${NC}"
elif [ $score -ge 80 ]; then
    echo -e "Performance Grade: ${GREEN}B (GOOD)${NC}"
elif [ $score -ge 70 ]; then
    echo -e "Performance Grade: ${YELLOW}C (ACCEPTABLE)${NC}"
elif [ $score -ge 60 ]; then
    echo -e "Performance Grade: ${YELLOW}D (NEEDS IMPROVEMENT)${NC}"
else
    echo -e "Performance Grade: ${RED}F (POOR)${NC}"
fi

# Recommendations
echo ""
echo "💡 Performance Recommendations"
echo "----------------------------------------"

if (( $(echo "$response_avg > 30" | bc -l) )); then
    echo "• Consider optimizing browser automation timeouts"
    echo "• Enable parallel processing for multiple selections"
fi

if (( $(echo "$cache_avg < 0.6" | bc -l) )); then
    echo "• Improve cache warming strategies"
    echo "• Increase cache TTL for popular combinations"
fi

if (( $(echo "$memory_avg > 1024" | bc -l) )); then
    echo "• Monitor for memory leaks in browser instances"
    echo "• Consider reducing browser pool size"
fi

if (( $(echo "$success_rate < 90" | bc -l) )); then
    echo "• Investigate causes of failed requests"
    echo "• Improve error handling and retry logic"
fi

# Save summary report
cat > "$RESULTS_DIR/performance_summary_$TIMESTAMP.txt" << EOF
Performance Monitoring Summary
Generated: $(date)
Duration: ${MONITOR_DURATION}s
Tests: $test_count

Response Time:
- Average: ${response_avg}s
- Min: ${response_min}s
- Max: ${response_max}s

Cache Performance:
- Average Hit Rate: ${cache_avg_percent}%
- Min Hit Rate: $(echo "scale=1; $cache_min * 100" | bc -l)%
- Max Hit Rate: $(echo "scale=1; $cache_max * 100" | bc -l)%

Memory Usage:
- Average: ${memory_avg}MB
- Min: ${memory_min}MB
- Max: ${memory_max}MB

Success Rate: ${success_rate}%
Performance Score: ${score}/100
EOF

echo ""
echo "📄 Detailed results saved to:"
echo "   - $RESULTS_DIR/performance_$TIMESTAMP.log"
echo "   - $RESULTS_DIR/performance_summary_$TIMESTAMP.txt"

# Exit with appropriate code based on performance
if [ $score -ge 70 ]; then
    echo -e "${GREEN}✅ Performance is acceptable for production use.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Performance needs improvement before production deployment.${NC}"
    exit 1
fi