"""
Poetry scripts, runable using 'poetry run'.
"""
import subprocess
import sys


def _run(cmd):
    assert isinstance(cmd, str)
    r = subprocess.run(cmd + " ".join(sys.argv[1:]), shell=True).returncode
    if r != 0:
        sys.exit(r)


def lint():
    _run("flake8 electricitymap tests parsers --count --select=E901,E999,F821,F822,F823 --show-source --statistics")
    for path in ["tests", "electricitymap", "*.py"]:
        _run(f"pylint -E {path} -d unsubscriptable-object,unsupported-assignment-operation,unpacking-non-sequence")


def test():
    _run("python -u -m unittest discover tests")
    _run("python -u -m unittest discover parsers/test")
