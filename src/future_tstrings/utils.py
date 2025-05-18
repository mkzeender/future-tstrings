from __future__ import annotations

import encodings
from tokenize_rt import Token


class TokenSyntaxError(SyntaxError):
    def __init__(self, e: SyntaxError, token: Token):
        super().__init__(e)
        self.e = e
        self.token = token


def tstring_prefix(token: Token, prev: Token | None) -> str | None:
    if prev is not None and prev.name == "NAME" and "t" in prev.src.lower():
        return prev.src
    return None
    # prefix, _ = parse_string_literal(token.src)
    # return "t" in prefix.lower()


_utf_8 = encodings.search_function("utf8")
if _utf_8 is None:
    raise encodings.CodecRegistryError("No utf-8 encoding in this version of python")
utf_8 = _utf_8
