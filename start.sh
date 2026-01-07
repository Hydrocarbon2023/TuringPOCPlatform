#!/bin/bash

trap 'kill $(jobs -p); exit' SIGINT

source .venv/bin/activate || source venv/bin/activate

python backend/app.py &
cd frontend && npm start
