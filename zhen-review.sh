#!/bin/bash
# Zhen AI Code Review - Quick Runner
cd "$(dirname "$0")"
PYTHONPATH=src python3 -m zhen_ai_codereview.main "$@"
