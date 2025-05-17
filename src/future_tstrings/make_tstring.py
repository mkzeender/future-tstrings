from future_tstrings.utils import TokenSyntaxError, is_tstring


def make_tstring(tokens):
    import tokenize_rt

    new_tokens = []
    exprs = []

    for i, token in enumerate(tokens):
        if token.name == "STRING" and is_tstring(token):
            prefix, s = tokenize_rt.parse_string_literal(token.src)
            parts = []
            try:
                _tstring_parse_outer(s, 0, 0, parts, exprs)
            except SyntaxError as e:
                raise TokenSyntaxError(e, tokens[i - 1])
            if "r" in prefix.lower():
                parts = [s.replace("\\", "\\\\") for s in parts]
            token = token._replace(src="".join(parts))
        elif token.name == "STRING":
            new_src = token.src.replace("{", "{{").replace("}", "}}")
            token = token._replace(src=new_src)
        new_tokens.append(token)

    exprs = ("({})".format(expr) for expr in exprs)
    format_src = ".format({})".format(", ".join(exprs))
    new_tokens.append(tokenize_rt.Token("FORMAT", src=format_src))

    return new_tokens


def _find_literal(s, start, level, parts, exprs):
    """Roughly Python/ast.c:fstring_find_literal"""
    i = start
    parse_expr = True

    while i < len(s):
        ch = s[i]

        if ch in ("{", "}"):
            if level == 0:
                if i + 1 < len(s) and s[i + 1] == ch:
                    i += 2
                    parse_expr = False
                    break
                elif ch == "}":
                    raise SyntaxError("f-string: single '}' is not allowed")
            break

        i += 1

    parts.append(s[start:i])
    return i, parse_expr and i < len(s)


def _find_expr(s, start, level, parts, exprs):
    """Roughly Python/ast.c:fstring_find_expr"""
    i = start
    nested_depth = 0
    quote_char = None
    triple_quoted = None

    def _check_end():
        if i == len(s):
            raise SyntaxError("f-string: expecting '}'")

    if level >= 2:
        raise SyntaxError("f-string: expressions nested too deeply")

    parts.append(s[i])
    i += 1

    while i < len(s):
        ch = s[i]

        if ch == "\\":
            raise SyntaxError(
                "f-string expression part cannot include a backslash",
            )
        if quote_char is not None:
            if ch == quote_char:
                if triple_quoted:
                    if i + 2 < len(s) and s[i + 1] == ch and s[i + 2] == ch:
                        i += 2
                        quote_char = None
                        triple_quoted = None
                else:
                    quote_char = None
                    triple_quoted = None
        elif ch in ('"', "'"):
            quote_char = ch
            if i + 2 < len(s) and s[i + 1] == ch and s[i + 2] == ch:
                triple_quoted = True
                i += 2
            else:
                triple_quoted = False
        elif ch in ("[", "{", "("):
            nested_depth += 1
        elif nested_depth and ch in ("]", "}", ")"):
            nested_depth -= 1
        elif ch == "#":
            raise SyntaxError("f-string expression cannot include '#'")
        elif nested_depth == 0 and ch in ("!", ":", "}"):
            if ch == "!" and i + 1 < len(s) and s[i + 1] == "=":
                # Allow != at top level as `=` isn't a valid conversion
                pass
            else:
                break
        i += 1

    if quote_char is not None:
        raise SyntaxError("f-string: unterminated string")
    elif nested_depth:
        raise SyntaxError("f-string: mismatched '(', '{', or '['")
    _check_end()

    exprs.append(s[start + 1 : i])

    if s[i] == "!":
        parts.append(s[i])
        i += 1
        _check_end()
        parts.append(s[i])
        i += 1

    _check_end()

    if s[i] == ":":
        parts.append(s[i])
        i += 1
        _check_end()
        i = _tstring_parse(s, i, level + 1, parts, exprs)

    _check_end()
    if s[i] != "}":
        raise SyntaxError("f-string: expecting '}'")

    parts.append(s[i])
    i += 1
    return i


def _tstring_parse(s, i, level, parts, exprs):
    """Roughly Python/ast.c:fstring_find_literal_and_expr"""
    while True:
        i, parse_expr = _find_literal(s, i, level, parts, exprs)
        if i == len(s) or s[i] == "}":
            return i
        if parse_expr:
            i = _find_expr(s, i, level, parts, exprs)


def _tstring_parse_outer(s, i, level, parts, exprs):
    for q in ('"' * 3, "'" * 3, '"', "'"):
        if s.startswith(q):
            s = s[len(q) : len(s) - len(q)]
            break
    else:
        raise AssertionError("unreachable")
    parts.append(q)
    ret = _tstring_parse(s, i, level, parts, exprs)
    parts.append(q)
    return ret
