#!/usr/bin/env bash
# Usage: BASE_URL=https://your-app.onrender.com USERNAME=you PASSWORD=yourpass ./smoke_test.sh
set -uo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
USERNAME="${USERNAME:?Set USERNAME env var}"
PASSWORD="${PASSWORD:?Set PASSWORD env var}"

pass=0
fail=0

check() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS  $label"
    pass=$((pass+1))
  else
    echo "  FAIL  $label (expected $expected, got $actual)"
    fail=$((fail+1))
  fi
}

echo "== TerraShield smoke test against $BASE_URL =="

echo -e "\n[1] POST /login"
LOGIN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")
LOGIN_CODE=$(echo "$LOGIN_RESP" | tail -1)
LOGIN_BODY=$(echo "$LOGIN_RESP" | sed '$d')
check "login returns 200" "200" "$LOGIN_CODE"
TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
if [[ -z "$TOKEN" ]]; then
  echo "  Could not get token, stopping. Response was: $LOGIN_BODY"
  exit 1
fi

echo -e "\n[2] POST /login with wrong password (error shape check)"
BAD_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"wrong-on-purpose\"}")
BAD_CODE=$(echo "$BAD_RESP" | tail -1)
check "bad login returns 401" "401" "$BAD_CODE"

echo -e "\n[3] POST /risk-assess"
RA_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/risk-assess" \
  -H "Content-Type: application/json" -H "Authorization: Token $TOKEN" \
  -d '{"pipeline_id":"PL-05","segment_code":"SG-12","latitude":4.815,"longitude":7.049,"environmental_data":{"elevation":18,"flood_risk":"High"},"incident_history":[{"type":"Vandalism","date":"2026-03-12"}]}')
RA_CODE=$(echo "$RA_RESP" | tail -1)
RA_BODY=$(echo "$RA_RESP" | sed '$d')
check "risk-assess returns 201" "201" "$RA_CODE"
echo "  Response: $RA_BODY"

echo -e "\n[4] POST /risk-assess with missing field (validation error shape)"
BADRA_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/risk-assess" \
  -H "Content-Type: application/json" -H "Authorization: Token $TOKEN" -d '{}')
BADRA_CODE=$(echo "$BADRA_RESP" | tail -1)
check "missing-field risk-assess returns 400" "400" "$BADRA_CODE"

echo -e "\n[5] GET /segments"
SEG_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/segments" -H "Authorization: Token $TOKEN")
SEG_CODE=$(echo "$SEG_RESP" | tail -1)
check "segments list returns 200" "200" "$SEG_CODE"

echo -e "\n[6] GET /segments/1"
DET_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/segments/1" -H "Authorization: Token $TOKEN")
DET_CODE=$(echo "$DET_RESP" | tail -1)
check "segment detail returns 200" "200" "$DET_CODE"

echo -e "\n[7] GET /segments/99999 (404 check)"
NF_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/segments/99999" -H "Authorization: Token $TOKEN")
NF_CODE=$(echo "$NF_RESP" | tail -1)
check "nonexistent segment returns 404" "404" "$NF_CODE"

echo -e "\n[8] GET /dashboard"
DASH_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/dashboard" -H "Authorization: Token $TOKEN")
DASH_CODE=$(echo "$DASH_RESP" | tail -1)
check "dashboard returns 200" "200" "$DASH_CODE"

echo -e "\n[9] GET /dashboard with no auth (should be blocked)"
NOAUTH_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/dashboard")
NOAUTH_CODE=$(echo "$NOAUTH_RESP" | tail -1)
check "unauthenticated dashboard returns 401" "401" "$NOAUTH_CODE"

echo -e "\n== $pass passed, $fail failed =="
[[ $fail -eq 0 ]] && exit 0 || exit 1
