from schema_validator.main import add
from schema_validator.cli import add_cli
import os 
import sys
from io import StringIO


def test_add():
    assert add(2, 3) == 5

def test_cli_entry_point():
    # Set up the command-line arguments
    os.environ['PYTHONPATH'] = os.getcwd()  # Ensure the current directory is in PYTHONPATH
    original_stdout = sys.stdout
    original_argv = sys.argv
    try:
        sys.stdout = StringIO()
        sys.argv = ['pv', '20', '13']  # Simulate command-line arguments
        add_cli()
        # Get the output and check if it contains the expected result
        output = sys.stdout.getvalue()

        assert "The result of adding 20.0 and 13.0 is 33.0." in output
    finally:
        # Restore original stdout and argv
        sys.stdout = original_stdout
        sys.argv = original_argv
