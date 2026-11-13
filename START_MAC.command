#!/bin/bash
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from python.org."
  read -r
  exit 1
fi
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -q -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000 &
PID=$!
sleep 2
open http://127.0.0.1:8000
wait "$PID"
