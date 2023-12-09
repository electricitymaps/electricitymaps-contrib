"""
Poetry scripts, runnable using 'poetry run'.

For example:
    poetry run lint
    poetry run format
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


def format():
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
