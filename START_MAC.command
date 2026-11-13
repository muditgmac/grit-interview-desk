#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -q -r requirements.txt
(sleep 2; open http://127.0.0.1:8000) &
python -m uvicorn app:app --host 127.0.0.1 --port 8000
