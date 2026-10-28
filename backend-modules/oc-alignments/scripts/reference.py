"""Sets up the reference implementation of Liss et al. for the tests: their code at a pinned
commit in vendor/liss, and the Python 3.10 environment it needs in vendor/liss-venv.

The code has no license file, so it is not copied into this repository; tests that compare
against it are skipped while it is missing.

    uv run python scripts/reference.py
"""

import subprocess
import sys
from pathlib import Path

REPOSITORY = "https://github.com/LukasLiss/object-centric-alignments.git"
COMMIT = "b298303addd1ecd91f7ef5f1850c560c9e5a8ed6"
VENDOR = Path(__file__).resolve().parents[1] / "vendor"
CHECKOUT = VENDOR / "liss"
VENV = VENDOR / "liss-venv"
PYTHON = VENV / "bin" / "python"
# What its code imports, pinned as in its requirements.txt; newer versions break it.
REQUIREMENTS = [
    "numpy==1.23.3",
    "pandas==1.4.4",
    "networkx==2.8.4",
    "pm4py==2.2.32",
    "scipy==1.9.3",
    "sympy==1.11.1",
    "packaging==21.3",
    "deprecation==2.1.0",
    "jsonschema",
    "graphviz",
    "matplotlib",
]


def run(*command: str | Path) -> None:
    subprocess.run([str(part) for part in command], check=True)


def main() -> None:
    VENDOR.mkdir(exist_ok=True)
    if not CHECKOUT.exists():
        run("git", "clone", "--quiet", REPOSITORY, CHECKOUT)
    run("git", "-C", CHECKOUT, "checkout", "--quiet", COMMIT)
    if not PYTHON.exists():
        run("uv", "venv", "--quiet", "--python", "3.10", VENV)
    run("uv", "pip", "install", "--quiet", "--python", PYTHON, *REQUIREMENTS)
    print(f"Reference ready: {CHECKOUT} (Python: {PYTHON})", file=sys.stderr)


if __name__ == "__main__":
    main()
