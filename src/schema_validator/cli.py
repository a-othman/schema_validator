import argparse
from schema_validator.main import add

def add_cli():
    parser = argparse.ArgumentParser(description="add two numbers.")
    parser.add_argument("a", type=float, help="First number.")
    parser.add_argument("b", type=float, help="Second number.")
    args = parser.parse_args()
    result = add(args.a, args.b)
    print(f"The result of adding {args.a} and {args.b} is {result}.")

