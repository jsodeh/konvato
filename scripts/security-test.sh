#!/bin/bash

# Security Testing Script for Betslip Converter
# This script performs basic security tests on the API endpoints

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:5000}"
TEST_RESULTS_DIR="./security-test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "$TEST_RESULTS_DIR"

echo "🔒 Starting Security Tests for Betslip Converter API"
echo "📍 Target: $API_BASE_URL"
echo "📅 Timestamp: $TIMESTAMP"
echo "----------------------------------------"

# Function to log test results
log_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    echo "[$TIMESTAMP] $test_name: $status - $details" >> "$TEST_RESULTS_DIR/security_test_$TIMESTAMP.log"
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $test_name: PASS${NC}"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ $test_name: FAIL${NC}"
    else
        echo -e "${YELLOW}⚠️  $test_name: WARNING${NC}"
    fi
    
    if [ -n "$details" ]; then
        echo "   Details: $details"
    fi
}

# Test 1: Input Validation - SQL Injection
echo "🧪 Testing SQL Injection Protection..."
response=$(curl -s -w "%{http_code}" -X POST "$API_BASE_URL/api/convert" \
    -H "Content-Type: application/json" \
    -d '{"betslipCode":"ABC123'\'' OR 1=1--","sourceBookmaker":"bet9ja","destinationBookmaker":"sportybet"}' \
    -o /tmp/sql_injection_test.json)

if [ "$response" = "400" ]; then
    log_result "SQL_INJECTION_PROTECTION" "PASS" "Malicious SQL input properly rejected"
else
    log_result "SQL_INJECTION_PROTECTION" "FAIL" "SQL injection attempt not properly handled (HTTP $response)"
fi

# Test 2: Input Validation - XSS
echo "🧪 Testing XSS Protection..."
response=$(curl -s -w "%{http_code}" -X POST "$API_BASE_URL/api/convert" \
    -H "Content-Type: application/json" \
    -d '{"betslipCode":"<script>alert(\"xss\")</script>","sourceBookmaker":"bet9ja","destinationBookmaker":"sportybet"}' \
    -o /tmp/xss_test.json)

if [ "$response" = "400" ]; then
    log_result "XSS_PROTECTION" "PASS" "XSS payload properly rejected"
else
    log_result "XSS_PROTECTION" "FAIL" "XSS payload not properly handled (HTTP $response)"
fi

# Test 3: Input Validation - Oversized Input
echo "🧪 Testing Input Size Limits..."
large_input=$(python3 -c "print('A' * 1000)")
response=$(curl -s -w "%{http_code}" -X POST "$API_BASE_URL/api/convert" \
    -H "Content-Type: application/json" \
    -d "{\"betslipCode\":\"$large_input\",\"sourceBookmaker\":\"bet9ja\",\"destinationBookmaker\":\"sportybet\"}" \
    -o /tmp/size_limit_test.json)

if [ "$response" = "400" ]; then
    log_result "INPUT_SIZE_LIMITS" "PASS" "Oversized input properly rejected"
else
    log_result "INPUT_SIZE_LIMITS" "FAIL" "Oversized input not properly handled (HTTP $response)"
fi

# Test 4: Rate Limiting
echo "🧪 Testing Rate Limiting..."
rate_limit_failures=0
for i in {1..15}; do
    response=$(curl -s -w "%{http_code}" -X POST "$API_BASE_URL/api/convert" \
        -H "Content-Type: application/json" \
        -d '{"betslipCode":"TEST123","sourceBookmaker":"bet9ja","destinationBookmaker":"sportybet"}' \
        -o /dev/null)
    
    if [ "$response" = "429" ]; then
        break
    elif [ $i -gt 10 ] && [ "$response" != "429" ]; then
        rate_limit_failures=$((rate_limit_failures + 1))
    fi
    
    sleep 1
done

if [ $rate_limit_failures -eq 0 ]; then
    log_result "RATE_LIMITING" "PASS" "Rate limiting properly enforced"
else
    log_result "RATE_LIMITING" "FAIL" "Rate limiting not working as expected"
fi

# Test 5: Error Information Disclosure
echo "🧪 Testing Error Information Disclosure..."
response=$(curl -s -X POST "$API_BASE_URL/api/convert" \
    -H "Content-Type: application/json" \
    -d '{"invalid":"json","structure":"test"}')

# Check if response contains sensitive information
if echo "$response" | grep -qi "stack\|trace\|internal\|server\|database\|password\|secret"; then
    log_result "ERROR_DISCLOSURE" "FAIL" "Error response may contain sensitive information"
else
    log_result "ERROR_DISCLOSURE" "PASS" "Error responses do not disclose sensitive information"
fi

# Test 6: HTTP Security Headers
echo "🧪 Testing Security Headers..."
headers=$(curl -s -I "$API_BASE_URL/api/health")

security_headers=(
    "X-Content-Type-Options"
    "X-Frame-Options"
    "X-XSS-Protection"
)

missing_headers=()
for header in "${security_headers[@]}"; do
    if ! echo "$headers" | grep -qi "$header"; then
        missing_headers+=("$header")
    fi
done

if [ ${#missing_headers[@]} -eq 0 ]; then
    log_result "SECURITY_HEADERS" "PASS" "All required security headers present"
else
    log_result "SECURITY_HEADERS" "WARNING" "Missing headers: ${missing_headers[*]}"
fi

# Test 7: HTTPS Redirect (if testing production)
if [[ "$API_BASE_URL" == https://* ]]; then
    echo "🧪 Testing HTTPS Redirect..."
    http_url=$(echo "$API_BASE_URL" | sed 's/https:/http:/')
    response=$(curl -s -w "%{http_code}" -I "$http_url/api/health" -o /dev/null)
    
    if [ "$response" = "301" ] || [ "$response" = "302" ]; then
        log_result "HTTPS_REDIRECT" "PASS" "HTTP properly redirects to HTTPS"
    else
        log_result "HTTPS_REDIRECT" "FAIL" "HTTP does not redirect to HTTPS (HTTP $response)"
    fi
fi

# Test 8: Invalid HTTP Methods
echo "🧪 Testing Invalid HTTP Methods..."
invalid_methods=("DELETE" "PUT" "PATCH")
method_failures=0

for method in "${invalid_methods[@]}"; do
    response=$(curl -s -w "%{http_code}" -X "$method" "$API_BASE_URL/api/convert" -o /dev/null)
    if [ "$response" != "405" ] && [ "$response" != "404" ]; then
        method_failures=$((method_failures + 1))
    fi
done

if [ $method_failures -eq 0 ]; then
    log_result "HTTP_METHODS" "PASS" "Invalid HTTP methods properly rejected"
else
    log_result "HTTP_METHODS" "WARNING" "Some invalid HTTP methods not properly handled"
fi

# Test 9: Content-Type Validation
echo "🧪 Testing Content-Type Validation..."
response=$(curl -s -w "%{http_code}" -X POST "$API_BASE_URL/api/convert" \
    -H "Content-Type: text/plain" \
    -d "invalid content type test" \
    -o /dev/null)

if [ "$response" = "400" ] || [ "$response" = "415" ]; then
    log_result "CONTENT_TYPE_VALIDATION" "PASS" "Invalid content-type properly rejected"
else
    log_result "CONTENT_TYPE_VALIDATION" "WARNING" "Content-type validation may be insufficient"
fi

# Test 10: Path Traversal
echo "🧪 Testing Path Traversal Protection..."
response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/../../../etc/passwd" -o /dev/null)

if [ "$response" = "404" ] || [ "$response" = "400" ]; then
    log_result "PATH_TRAVERSAL" "PASS" "Path traversal attempts properly blocked"
else
    log_result "PATH_TRAVERSAL" "FAIL" "Path traversal protection may be insufficient (HTTP $response)"
fi

# Generate Summary Report
echo ""
echo "📊 Security Test Summary"
echo "----------------------------------------"

total_tests=$(grep -c ":" "$TEST_RESULTS_DIR/security_test_$TIMESTAMP.log")
passed_tests=$(grep -c "PASS" "$TEST_RESULTS_DIR/security_test_$TIMESTAMP.log")
failed_tests=$(grep -c "FAIL" "$TEST_RESULTS_DIR/security_test_$TIMESTAMP.log")
warning_tests=$(grep -c "WARNING" "$TEST_RESULTS_DIR/security_test_$TIMESTAMP.log")

echo "Total Tests: $total_tests"
echo -e "${GREEN}Passed: $passed_tests${NC}"
echo -e "${RED}Failed: $failed_tests${NC}"
echo -e "${YELLOW}Warnings: $warning_tests${NC}"

# Calculate security score
if [ $total_tests -gt 0 ]; then
    score=$(( (passed_tests * 100) / total_tests ))
    echo ""
    echo "🏆 Security Score: $score%"
    
    if [ $score -ge 90 ]; then
        echo -e "${GREEN}Security Status: EXCELLENT${NC}"
    elif [ $score -ge 80 ]; then
        echo -e "${GREEN}Security Status: GOOD${NC}"
    elif [ $score -ge 70 ]; then
        echo -e "${YELLOW}Security Status: ACCEPTABLE${NC}"
    else
        echo -e "${RED}Security Status: NEEDS IMPROVEMENT${NC}"
    fi
fi

echo ""
echo "📄 Detailed results saved to: $TEST_RESULTS_DIR/security_test_$TIMESTAMP.log"

# Exit with appropriate code
if [ $failed_tests -gt 0 ]; then
    echo -e "${RED}⚠️  Security tests failed. Please review and fix issues before production deployment.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All critical security tests passed.${NC}"
    exit 0
fi