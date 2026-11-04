#!/usr/bin/env bash
set -e

echo "=== Testing Juice Shop Assistant Endpoint ==="
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What juices do you have and what are their prices?"}' | jq .
