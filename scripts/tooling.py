"""
Poetry scripts, runable using 'poetry run'.
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
    _run(f"isort --profile=black .")
    _run("black .")


def lint():
    _run(
        "flake8 electricitymap tests parsers --count --select=E901,E999,F821,F822,F823 --show-source --statistics"
    )
    _run("black --check .")
    _run("isort --profile=black -c .")
    for path in ["tests", "electricitymap", "*.py"]:
        _run(
            f"pylint -E {path} -d unsubscriptable-object,unsupported-assignment-operation,unpacking-non-sequence"
        )


def test():
    _run("python -u -m unittest discover tests")
    _run("python -u -m unittest discover parsers/test")


def check():
    lint()
    test()
