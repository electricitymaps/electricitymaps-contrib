"""
Poetry scripts, runable using 'poetry run'.
"""
import subprocess
import sys


def lint():
    subprocess.run(
        ['pylint', '-E', 'tests', 'electricitymap'] + sys.argv[1:]
    )

def test():
    subprocess.run(
        ['python', '-u', '-m', 'unittest', 'discover', 'tests'] + sys.argv[1:]
    )
