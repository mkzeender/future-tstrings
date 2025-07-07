import argparse
from .parser import compile_to_python


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Prints transformed source.")
    parser.add_argument("filename")
    args = parser.parse_args(argv)

    with open(args.filename, "r", encoding="utf-8") as f:
        text = compile_to_python(f.read(), filepath=args.filename)
    print(text)


if __name__ == "__main__":
    main()
