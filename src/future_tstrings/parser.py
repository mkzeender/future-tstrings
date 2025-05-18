from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Buffer
from future_tstrings.utils import TokenSyntaxError, tstring_prefix
from .make_tstring import make_tstring
from .utils import utf_8
from tokenize_rt import src_to_tokens, tokens_to_src, NON_CODING_TOKENS, Token


def decode(b: Buffer, errors="strict"):
    src, length = utf_8.decode(b, errors)
    tokens = tokenize(src)
    return tokens_to_src(tokens), length


def tokenize(src: str) -> list[Token]:
    tokens = src_to_tokens(src)
    to_replace = list[tuple[int, int, str]]()
    start = end = t_prefix = None
    prev: Token | None = None

    for i, token in enumerate(tokens):
        if start is None:
            if token.name == "STRING":
                start, end = i, i + 1
                t_prefix = tstring_prefix(token, prev)

        elif token.name == "STRING":
            end = i + 1
            t_prefix = t_prefix or tstring_prefix(token, prev)
        elif token.name not in NON_CODING_TOKENS:
            assert end is not None
            if t_prefix:
                to_replace.append((start, end, t_prefix))
            start = end = t_prefix = None
        prev = token

    for start, end, t_prefix in reversed(to_replace):
        try:
            start_incl = start - bool(t_prefix)
            tokens[start_incl:end] = make_tstring(tokens[start:end], t_prefix)
        except TokenSyntaxError as e:
            if src:
                msg = str(e.e)
                line = (
                    src.splitlines()[e.token.line - 1]
                    if e.token.line is not None
                    else ""
                )
                bts = line.encode("UTF-8")[: e.token.utf8_byte_offset]
                indent = len(bts.decode("UTF-8"))
                raise SyntaxError(msg + "\n\n" + line + "\n" + " " * indent + "^")
            else:
                raise e.e

    return tokens
