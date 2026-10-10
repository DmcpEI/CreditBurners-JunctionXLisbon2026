#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
"${PYTHON:-python3}" -m unittest discover -s ml -p 'test_*.py' -v
echo "ML preparation/scoring smoke checks passed; API/UI and model inference are not covered yet."
