"""
Poetry scripts, runable using 'poetry run'.
"""
import subprocess
import sys


def lint():
    subprocess.run([
        'flake8', 'electricitymap', 'tests', 'parsers', '--count', '--select=E901,E999,F821,F822,F823', '--show-source', '--statistics'
    ])
    for paths in ['tests', 'electricitymap']:
        subprocess.run(
            ['pylint', '-E', paths, '-d', 'unsubscriptable-object,unsupported-assignment-operation,unpacking-non-sequence']
        )

def test():
    subprocess.run(
        ['python', '-u', '-m', 'unittest', 'discover', 'tests'] + sys.argv[1:]
    )
    subprocess.run(
        ['python', '-u', '-m', 'unittest', 'discover', 'parsers/test'] + sys.argv[1:]
    )
