from __future__ import annotations

import encodings
from tokenize import TokenInfo as Token

TEMPLATE_BUILTIN = "__create_template__"
FSTRING_BUILTIN = "__create_fstring__"

CONVERSION = {-1: None, 115: "s", 114: "r", 97: "a"}


class TokenSyntaxError(SyntaxError):
    def __init__(self, e: SyntaxError, token: Token):
        super().__init__(e)
        self.e = e
        self.token = token


def tstring_prefix(token: Token, prev: Token | None) -> str | None:
    if prev is not None and prev.type == "NAME" and "t" in prev.string.lower():
        return prev.string
    return None
    # prefix, _ = parse_string_literal(token.src)
    # return "t" in prefix.lower()


_utf_8 = encodings.search_function("utf8")
if _utf_8 is None:
    raise encodings.CodecRegistryError("No utf-8 encoding in this version of python")
utf_8 = _utf_8
