#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "scripts" / "_pytest_out.txt"
cmd = [
    str(root / ".venv" / "bin" / "pytest"),
    "tests/test_api.py",
    "tests/test_demo_features.py",
    "tests/test_validator.py",
    "-q",
    "--tb=short",
]
proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
out.write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
print(f"exit={proc.returncode}")
print(out.read_text(encoding="utf-8")[-4000:])
sys.exit(proc.returncode)
