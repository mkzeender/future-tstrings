import sys
import encodings


def natively_supports_tstrings():
    return sys.version_info >= (3, 14)


ENCODING_NAMES = ("future-tstrings", "future_tstrings")

TEMPLATE_BUILTIN = "__create_template__"
FSTRING_BUILTIN = "__create_fstring__"

_utf_8 = encodings.search_function("utf8")
if _utf_8 is None:
    raise encodings.CodecRegistryError("No utf-8 encoding in this version of python")
utf_8 = _utf_8
