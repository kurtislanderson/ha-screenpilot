#!/bin/bash
# Test ScreenPilot API endpoints
# Usage: ./test_api.sh [HOST] [TOKEN]

HOST="${1:-localhost:8000}"
TOKEN="${2:-dev-token-12345}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Testing ScreenPilot API at $HOST"
echo "================================"
echo ""

# Function to test endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local auth="$3"
    local data="$4"
    local description="$5"
    
    echo -n "$description: "
    
    if [ "$auth" = "yes" ]; then
        AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
    else
        AUTH_HEADER=""
    fi
    
    if [ -n "$data" ]; then
        DATA_PARAM="-d '$data' -H \"Content-Type: application/json\""
    else
        DATA_PARAM=""
    fi
    
    # Build and execute curl command
    CMD="curl -s -o /dev/null -w \"%{http_code}\" -X $method $AUTH_HEADER $DATA_PARAM \"http://$HOST$endpoint\""
    RESPONSE=$(eval $CMD)
    
    if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "201" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $RESPONSE)"
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $RESPONSE)"
    fi
}

# Test health endpoint (no auth)
test_endpoint "GET" "/api/health/" "no" "" "Health check"

# Test system endpoints
test_endpoint "GET" "/api/system/info/" "yes" "" "System info"
test_endpoint "GET" "/api/system/logs/" "yes" "" "System logs"

# Test kiosk endpoints
test_endpoint "GET" "/api/kiosk/url/" "yes" "" "Get kiosk URL"
test_endpoint "GET" "/api/kiosk/startup_url/" "yes" "" "Get startup URL"
test_endpoint "GET" "/api/kiosk/health/" "yes" "" "Kiosk health"
test_endpoint "GET" "/api/kiosk/screenshot/" "no" "" "Screenshot"

# Test CEC endpoints
test_endpoint "GET" "/api/cec/status/" "yes" "" "CEC status"
test_endpoint "GET" "/api/cec/commands/" "yes" "" "CEC commands"

# Test service status
test_endpoint "GET" "/api/status/service_status/" "yes" "" "Service status"

echo ""
echo "Testing write operations..."
echo ""

# Test URL setting
test_endpoint "PUT" "/api/kiosk/url/" "yes" '{"url": "https://example.com"}' "Set kiosk URL"

# Test CEC command
test_endpoint "POST" "/api/cec/command/power_on/" "yes" "" "Send CEC command"

echo ""
echo "================================"
echo "Integration test complete!"
echo ""

# Show example data
echo "Example responses:"
echo ""

echo "System Info:"
curl -s -H "Authorization: Bearer $TOKEN" "http://$HOST/api/system/info/" | python3 -m json.tool 2>/dev/null || echo "Install python3 for pretty JSON"

echo ""
echo "Kiosk Health:"
curl -s -H "Authorization: Bearer $TOKEN" "http://$HOST/api/kiosk/health/" | python3 -m json.tool 2>/dev/null || echo "Install python3 for pretty JSON"