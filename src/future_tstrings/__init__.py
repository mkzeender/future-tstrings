import sys


__all__ = "natively_supports_tstrings", "ENCODING_NAMES"


def natively_supports_tstrings():
    return sys.version_info >= (3, 14)


ENCODING_NAMES = ("future-tstrings", "future_tstrings")
