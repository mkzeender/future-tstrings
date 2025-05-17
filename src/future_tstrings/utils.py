import encodings
import encodings.utf_8
from tokenize_rt import Token, parse_string_literal


class TokenSyntaxError(SyntaxError):
    def __init__(self, e, token):
        super(TokenSyntaxError, self).__init__(e)
        self.e = e
        self.token = token


def is_tstring(token: Token):
    prefix, _ = parse_string_literal(token.src)
    return "t" in prefix.lower()


_utf_8 = encodings.search_function("utf8")
if _utf_8 is None:
    raise encodings.CodecRegistryError("No utf-8 encoding in this version of python")
utf_8 = _utf_8
