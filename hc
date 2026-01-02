#!/bin/bash
# Quick health check alias
# Usage: ./hc

# Clear terminal first
clear

python scripts/health_check.py "$@"
