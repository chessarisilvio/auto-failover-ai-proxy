#!/bin/bash
# Health check script for local AI proxy
# Uses environment variables for configuration:
#   PROXY_HOST (default: localhost)
#   PROXY_PORT (default: 8090)
#   THRESHOLD_MS (default: 200)

# Set defaults if not already set
PROXY_HOST="${PROXY_HOST:-localhost}"
PROXY_PORT="${PROXY_PORT:-8090}"
THRESHOLD_MS="${THRESHOLD_MS:-200}"

# Perform curl request and capture total time in seconds
# -s: silent, -o /dev/null: discard output, -w "%{time_total}": output time total
response_time_seconds=$(curl -s -o /dev/null -w "%{time_total}" "http://${PROXY_HOST}:${PROXY_PORT}/" 2>/dev/null)
curl_exit_code=$?

# Check if curl failed
if [ $curl_exit_code -ne 0 ]; then
    # curl failed (e.g., connection refused, timeout)
    exit 1
fi

# Convert seconds to milliseconds (multiply by 1000 and round to nearest integer)
# Using bc for floating point arithmetic, then convert to integer
response_time_ms=$(echo "$response_time_seconds * 1000" | bc | cut -d'.' -f1)

# Compare with threshold
if [ "$response_time_ms" -le "$THRESHOLD_MS" ]; then
    exit 0
else
    exit 1
fi