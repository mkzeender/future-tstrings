import argparse
from .encoding import decode


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Prints transformed source.")
    parser.add_argument("filename")
    args = parser.parse_args(argv)

    with open(args.filename, "rb") as f:
        text, _ = decode(f.read())
    print(text)


if __name__ == "__main__":
    main()
