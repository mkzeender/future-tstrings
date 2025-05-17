import sys


def natively_supports_tstrings():
    return sys.version_info >= (3, 14)


ENCODING_NAMES = ("future-tstrings", "future_tstrings")
