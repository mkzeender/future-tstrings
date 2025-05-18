import ast
from collections.abc import Sequence
from typing import Any
from future_tstrings.utils import tstring_prefix
from tokenize_rt import Token, tokens_to_src, src_to_tokens
from . import parser

NAME = "NAME"
OP = "OP"

TEMPLATE_BUILTIN = "__create_template__"

CONVERSION = {-1: None, 115: "s", 114: "r", 97: "a"}

p: dict[str, Any] = dict(lineno=0, col_offset=0, end_lineno=0, end_col_offset=0)


def make_tstring(tokens: Sequence[Token], first_prefix: str) -> list[Token]:
    new_tokens = list[Token]()

    prev: Token | None = None

    for i, token in enumerate(tokens):
        if token.name == "STRING":
            if i:
                prefix = tstring_prefix(token, prev)
            else:
                prefix = first_prefix
            if prefix:
                s = token.src
                new_prefix = "f" + prefix.replace("t", "").replace("T", "")
                fstring_tokens = parser.tokenize(new_prefix + s)
                new_tokens.extend(fstring_tokens)
            else:
                new_tokens.append(token)
        else:
            pass

    as_fstring = tokens_to_src(new_tokens)

    expr = ast.parse(as_fstring, mode="eval").body

    while isinstance(expr, ast.Expr):
        expr = expr.value

    if not isinstance(expr, ast.JoinedStr):
        return list(tokens)

    args: list[ast.expr] = []
    const = True
    for val in expr.values:
        if isinstance(val, ast.Constant):
            assert const
            args.append(val)
            const = False

        elif isinstance(val, ast.FormattedValue):
            if const:
                args.append(ast.Constant(value=""))

            format_spec = (
                ast.Constant(value=None) if val.format_spec is None else val.format_spec
            )
            args.append(
                ast.Tuple(
                    elts=[
                        val.value,
                        ast.Constant(value=ast.unparse(val.value)),
                        ast.Constant(value=CONVERSION[val.conversion]),
                        format_spec,
                    ]
                )
            )

            const = True

    return src_to_tokens(
        ast.unparse(
            ast.Call(
                func=ast.Name(id=TEMPLATE_BUILTIN, ctx=ast.Load()),
                args=args,
                keywords=[],
            )
        )
    )

    # interp: list[str | list[Token]] = [""]
    # nest_level = 0
    # for i, token in enumerate(new_tokens):
    #     piece = interp[-1]
    #     if token.src in "({[" or token.name == 'FSTRING_START':
    #         nest_level += 1
    #     if token.src in ")}]" or token.name == 'FSTRING_END':
    #         nest_level = max(0, nest_level-1)
    #     if nest_level >= 2:
    #         if isinstance(piece, str):
    #             interp.append(piece := [])

    #         if nest_level == 2:

    #         piece.append(token)
    #     else:
    #         if isinstance(interp[-1], list):

    # return [Token(NAME, src=TEMPLATE_BUILTIN), Token(OP, src="("), ..., Token(OP, ")")]


# def make_tstring_old(tokens: Sequence[Token]):
#     new_tokens = list[Token]()
#     exprs = []

#     for i, token in enumerate(tokens):
#         if token.name == "STRING" and tstring_prefix(token):
#             prefix, s = parse_string_literal(token.src)
#             parts = list[str]()
#             try:
#                 _tstring_parse_outer(s, 0, 0, parts, exprs)
#             except SyntaxError as e:
#                 raise TokenSyntaxError(e, tokens[i - 1])
#             if "r" in prefix.lower():
#                 parts = [s.replace("\\", "\\\\") for s in parts]
#             token = token._replace(src="".join(parts))
#         elif token.name == "STRING":
#             new_src = token.src.replace("{", "{{").replace("}", "}}")
#             token = token._replace(src=new_src)
#         new_tokens.append(token)

#     exprs = ("({})".format(expr) for expr in exprs)
#     format_src = ".format({})".format(", ".join(exprs))
#     new_tokens.append(Token("FORMAT", src=format_src))

#     return new_tokens


# def _find_literal(s: str, start, level, parts, exprs):
#     """Roughly Python/ast.c:fstring_find_literal"""
#     i = start
#     parse_expr = True

#     while i < len(s):
#         ch = s[i]

#         if ch in ("{", "}"):
#             if level == 0:
#                 if i + 1 < len(s) and s[i + 1] == ch:
#                     i += 2
#                     parse_expr = False
#                     break
#                 elif ch == "}":
#                     raise SyntaxError("f-string: single '}' is not allowed")
#             break

#         i += 1

#     parts.append(s[start:i])
#     return i, parse_expr and i < len(s)


# def _find_expr(s, start, level, parts, exprs):
#     """Roughly Python/ast.c:fstring_find_expr"""
#     i = start
#     nested_depth = 0
#     quote_char = None
#     triple_quoted = None

#     def _check_end():
#         if i == len(s):
#             raise SyntaxError("f-string: expecting '}'")

#     if level >= 2:
#         raise SyntaxError("f-string: expressions nested too deeply")

#     parts.append(s[i])
#     i += 1

#     while i < len(s):
#         ch = s[i]

#         if ch == "\\":
#             raise SyntaxError(
#                 "f-string expression part cannot include a backslash",
#             )
#         if quote_char is not None:
#             if ch == quote_char:
#                 if triple_quoted:
#                     if i + 2 < len(s) and s[i + 1] == ch and s[i + 2] == ch:
#                         i += 2
#                         quote_char = None
#                         triple_quoted = None
#                 else:
#                     quote_char = None
#                     triple_quoted = None
#         elif ch in ('"', "'"):
#             quote_char = ch
#             if i + 2 < len(s) and s[i + 1] == ch and s[i + 2] == ch:
#                 triple_quoted = True
#                 i += 2
#             else:
#                 triple_quoted = False
#         elif ch in ("[", "{", "("):
#             nested_depth += 1
#         elif nested_depth and ch in ("]", "}", ")"):
#             nested_depth -= 1
#         elif ch == "#":
#             raise SyntaxError("f-string expression cannot include '#'")
#         elif nested_depth == 0 and ch in ("!", ":", "}"):
#             if ch == "!" and i + 1 < len(s) and s[i + 1] == "=":
#                 # Allow != at top level as `=` isn't a valid conversion
#                 pass
#             else:
#                 break
#         i += 1

#     if quote_char is not None:
#         raise SyntaxError("f-string: unterminated string")
#     elif nested_depth:
#         raise SyntaxError("f-string: mismatched '(', '{', or '['")
#     _check_end()

#     exprs.append(s[start + 1 : i])

#     if s[i] == "!":
#         parts.append(s[i])
#         i += 1
#         _check_end()
#         parts.append(s[i])
#         i += 1

#     _check_end()

#     if s[i] == ":":
#         parts.append(s[i])
#         i += 1
#         _check_end()
#         i = _tstring_parse(s, i, level + 1, parts, exprs)

#     _check_end()
#     if s[i] != "}":
#         raise SyntaxError("f-string: expecting '}'")

#     parts.append(s[i])
#     i += 1
#     return i


# def _tstring_parse(s, i, level, parts, exprs):
#     """Roughly Python/ast.c:fstring_find_literal_and_expr"""
#     while True:
#         i, parse_expr = _find_literal(s, i, level, parts, exprs)
#         if i == len(s) or s[i] == "}":
#             return i
#         if parse_expr:
#             i = _find_expr(s, i, level, parts, exprs)


# def _tstring_parse_outer(s: str, i: int, level: int, parts, exprs):
#     for q in ('"' * 3, "'" * 3, '"', "'"):
#         if s.startswith(q):
#             s = s[len(q) : len(s) - len(q)]
#             break
#     else:
#         raise AssertionError("unreachable")
#     parts.append(q)
#     ret = _tstring_parse(s, i, level, parts, exprs)
#     parts.append(q)
#     return ret
