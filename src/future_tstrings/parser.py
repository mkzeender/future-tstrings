from collections.abc import Buffer
from future_tstrings.utils import TokenSyntaxError, is_tstring
from .make_tstring import make_tstring
from .utils import utf_8
from tokenize_rt import (
    src_to_tokens,
    NON_CODING_TOKENS,
    tokens_to_src,
)


def decode(b: Buffer, errors="strict"):
    u, length = utf_8.decode(b, errors)
    tokens = src_to_tokens(u)

    to_replace = []
    start = end = seen_t = None

    for i, token in enumerate(tokens):
        if start is None:
            if token.name == "STRING":
                start, end = i, i + 1
                seen_t = is_tstring(token)
        elif token.name == "STRING":
            end = i + 1
            seen_t = seen_t or is_tstring(token)
        elif token.name not in NON_CODING_TOKENS:
            if seen_t:
                to_replace.append((start, end))
            start = end = seen_t = None

    for start, end in reversed(to_replace):
        try:
            tokens[start:end] = make_tstring(tokens[start:end])
        except TokenSyntaxError as e:
            msg = str(e.e)
            line = u.splitlines()[e.token.line - 1]
            bts = line.encode("UTF-8")[: e.token.utf8_byte_offset]
            indent = len(bts.decode("UTF-8"))
            raise SyntaxError(msg + "\n\n" + line + "\n" + " " * indent + "^")
    return tokens_to_src(tokens), length
