#!/bin/bash
cd /home/mosama/frappe-bench/apps/arabic-editorial-proofreading || exit 1
.venv/bin/python -c 'from app.main import app; print("import-ok")'
.venv/bin/pytest tests/test_api.py tests/test_demo_features.py tests/test_validator.py -q
