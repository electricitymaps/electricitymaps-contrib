"""
Utility Python scripts runnable using 'uv run'.

For example:
    uv run lint
    uv run format
"""

import subprocess
import sys


def _run(cmd: str):
    cmd_with_args = f"{cmd} {' '.join(sys.argv[1:])}"
    print(f"⚙︎ {cmd_with_args}")
    r = subprocess.run(cmd_with_args, shell=True).returncode
    if r != 0:
        print(f"FAILED: {cmd}")
        sys.exit(r)


def format():  # noqa: A001
    _run("ruff check . --fix")
    _run("ruff format .")


def lint():
    _run("ruff check .")


def test():
    _run("pytest")


def check():
    _run("ruff format --check .")
    lint()
    test()
