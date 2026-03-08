#!/bin/bash
set -e
export PYTHONPATH=/home/ubuntu/github/3dshape:$PYTHONPATH
source venv/bin/activate

echo "Running Backend Unit Tests..."
pytest tests/phase1_database/ tests/phase2_ingestion/ tests/phase3_rendering/ -v

echo "Running Frontend Visual UI Tests..."
pytest tests/phase4_viewer/test_visual.py -v
