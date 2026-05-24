from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_basic_functionality_smoke_script() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/smoke_test.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "validation passed",
        "inspect passed",
        "compile passed",
        "mock session passed",
        "persistence passed",
        "export passed",
        "evaluation passed",
        "smoke test completed successfully",
    ]
