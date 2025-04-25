#!/bin/bash

echo "Starting aGENtrader v2 pipeline..."
cd "$(dirname "$0")" || exit
python3 test_v2_pipeline.py
