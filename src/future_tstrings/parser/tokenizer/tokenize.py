# ruff: noqa: F821
# pyright: reportPossiblyUnboundVariable=false
from __future__ import annotations
from collections.abc import Iterable, Iterator
from re import Pattern
import re

from parso.python.token import PythonTokenTypes as TOKS
from parso.python.tokenize import (
    PythonToken,
    FStringNode,
    BOM_UTF8_STRING,
)
from parso.utils import split_lines
from ._tokens_util import close_fstring_if_necessary, split_illegal_unicode_name


from future_tstrings.parser.tokenizer._tokens_re import (
    create_token_collection,
    find_fstring_string,
)


def tokenize(
    code: str, *, start_pos: tuple[int, int] = (1, 0)
) -> Iterator[PythonToken]:
    """Generate tokens from a the source code (string)."""
    lines = split_lines(code, keepends=True)
    return tokenize_lines(lines, start_pos=start_pos)


def tokenize_lines(
    lines: Iterable[str],
    *,
    indents: list[int] | None = None,
    start_pos: tuple[int, int] = (1, 0),
    is_first_token=True,
) -> Iterator[PythonToken]:
    """
    A heavily modified Python standard library tokenizer.

    Additionally to the default information, yields also the prefix of each
    token. This idea comes from lib2to3. The prefix contains all information
    that is irrelevant for the parser like newlines in parentheses or comments.
    """
    if indents is None:
        indents = [0]

    def dedent_if_necessary(start):
        while start < indents[-1]:
            if start > indents[-2]:
                yield PythonToken(TOKS.ERROR_DEDENT, "", (lnum, start), "")
                indents[-1] = start
                break
            indents.pop()
            yield PythonToken(TOKS.DEDENT, "", spos, "")

    (
        pseudo_token,
        single_quoted,
        triple_quoted,
        endpats,
        whitespace,
        fstring_pattern_map,
        always_break_tokens,
    ) = create_token_collection()
    paren_level = 0  # count parentheses

    max_ = 0
    numchars = "0123456789"
    contstr = ""
    contline: str
    contstr_start: tuple[int, int]
    endprog: Pattern
    # We start with a newline. This makes indent at the first position
    # possible. It's not valid Python, but still better than an INDENT in the
    # second line (and not in the first). This makes quite a few things in
    # Jedi's fast parser possible.
    new_line = True
    lnum = start_pos[0] - 1

    prefix = ""  # Should never be required, but here for safety
    additional_prefix = ""
    fstring_stack: list[FStringNode] = []
    for line in lines:  # loop over lines in stream
        lnum += 1
        pos = 0
        max_ = len(line)
        if is_first_token:
            if line.startswith(BOM_UTF8_STRING):
                additional_prefix = BOM_UTF8_STRING
                line = line[1:]
                max_ = len(line)

            # Fake that the part before was already parsed.
            line = "^" * start_pos[1] + line
            pos = start_pos[1]
            max_ += start_pos[1]

            is_first_token = False

        if contstr:  # continued string
            endmatch = endprog.match(line)  # noqa: F821
            if endmatch:
                pos = endmatch.end(0)
                yield PythonToken(
                    TOKS.STRING, contstr + line[:pos], contstr_start, prefix
                )  # noqa: F821
                contstr = ""
                contline = ""
            else:
                contstr = contstr + line
                contline = str(contline) + line
                continue

        while pos < max_:
            if fstring_stack:
                tos = fstring_stack[-1]
                if not tos.is_in_expr():
                    string, pos = find_fstring_string(
                        endpats, fstring_stack, line, lnum, pos
                    )
                    if string:
                        yield PythonToken(
                            TOKS.FSTRING_STRING,
                            string,
                            tos.last_string_start_pos,  # type: ignore
                            # Never has a prefix because it can start anywhere and
                            # include whitespace.
                            prefix="",
                        )
                        tos.previous_lines = ""
                        continue
                    if pos == max_:
                        break

                rest = line[pos:]
                fstring_end_token, additional_prefix, quote_length = (
                    close_fstring_if_necessary(
                        fstring_stack,
                        rest,
                        lnum,
                        pos,
                        additional_prefix,
                    )
                )
                pos += quote_length
                if fstring_end_token is not None:
                    yield fstring_end_token
                    continue

            # # in an f-string, match until the end of the string
            # if fstring_stack:
            #     string_line = line
            #     for fstring_stack_node in fstring_stack:
            #         quote = fstring_stack_node.quote
            #         end_match = endpats[quote].match(line, pos)
            #         if end_match is not None:
            #             end_match_string = end_match.group(0)
            #             if len(end_match_string) - len(quote) + pos < len(string_line):
            #                 string_line = line[:pos] + end_match_string[: -len(quote)]
            #     pseudomatch = pseudo_token.match(string_line, pos)
            # else:
            pseudomatch = pseudo_token.match(line, pos)

            if pseudomatch:
                prefix = additional_prefix + pseudomatch.group(1)
                additional_prefix = ""
                start, pos = pseudomatch.span(2)
                spos = (lnum, start)
                token = pseudomatch.group(2)
                if token == "":
                    assert prefix
                    additional_prefix = prefix
                    # This means that we have a line with whitespace/comments at
                    # the end, which just results in an endmarker.
                    break
                initial = token[0]
            else:
                match = whitespace.match(line, pos)
                assert match
                initial = line[match.end()]
                start = match.end()
                spos = (lnum, start)

            if (
                new_line
                and initial not in "\r\n#"
                and (initial != "\\" or pseudomatch is None)
            ):
                new_line = False
                if paren_level == 0 and not fstring_stack:
                    indent_start = start
                    if indent_start > indents[-1]:
                        yield PythonToken(TOKS.INDENT, "", spos, "")
                        indents.append(indent_start)
                    yield from dedent_if_necessary(indent_start)

            if not pseudomatch:  # scan for tokens
                match = whitespace.match(line, pos)
                assert match
                if new_line and paren_level == 0 and not fstring_stack:
                    yield from dedent_if_necessary(match.end())
                pos = match.end()
                new_line = False
                yield PythonToken(
                    TOKS.ERRORTOKEN,
                    line[pos],
                    (lnum, pos),
                    additional_prefix + match.group(0),
                )
                additional_prefix = ""
                pos += 1
                continue

            if (
                initial in numchars  # ordinary number
                or (initial == "." and token != "." and token != "...")
            ):
                yield PythonToken(TOKS.NUMBER, token, spos, prefix)
            elif pseudomatch.group(3) is not None:  # ordinary name
                if token in always_break_tokens and (fstring_stack or paren_level):
                    fstring_stack[:] = []
                    paren_level = 0
                    # We only want to dedent if the token is on a new line.
                    m = re.match(r"[ \f\t]*$", line[:start])
                    if m is not None:
                        yield from dedent_if_necessary(m.end())
                if token.isidentifier():
                    yield PythonToken(TOKS.NAME, token, spos, prefix)
                else:
                    yield from split_illegal_unicode_name(token, spos, prefix)
            elif initial in "\r\n":
                if any(not f.allow_multiline() for f in fstring_stack):
                    fstring_stack.clear()

                if not new_line and paren_level == 0 and not fstring_stack:
                    yield PythonToken(TOKS.NEWLINE, token, spos, prefix)
                else:
                    additional_prefix = prefix + token
                new_line = True
            elif initial == "#":  # Comments
                assert not token.endswith("\n") and not token.endswith("\r")
                if fstring_stack and fstring_stack[-1].is_in_expr():
                    # `#` is not allowed in f-string expressions
                    yield PythonToken(TOKS.ERRORTOKEN, initial, spos, prefix)
                    pos = start + 1
                else:
                    additional_prefix = prefix + token
            elif token in triple_quoted:
                endprog = endpats[token]
                endmatch = endprog.match(line, pos)
                if endmatch:  # all on one line
                    pos = endmatch.end(0)
                    token = line[start:pos]
                    yield PythonToken(TOKS.STRING, token, spos, prefix)
                else:
                    contstr_start = spos  # multiple lines
                    contstr = line[start:]
                    contline = line
                    break

            # Check up to the first 3 chars of the token to see if
            #  they're in the single_quoted set. If so, they start
            #  a string.
            # We're using the first 3, because we're looking for
            #  "rb'" (for example) at the start of the token. If
            #  we switch to longer prefixes, this needs to be
            #  adjusted.
            # Note that initial == token[:1].
            # Also note that single quote checking must come after
            #  triple quote checking (above).
            elif (
                initial in single_quoted
                or token[:2] in single_quoted
                or token[:3] in single_quoted
            ):
                if token[-1] in "\r\n":  # continued string
                    # This means that a single quoted string ends with a
                    # backslash and is continued.
                    contstr_start = lnum, start
                    endprog = (
                        endpats.get(initial)
                        or endpats.get(token[1])
                        or endpats[token[2]]
                    )
                    contstr = line[start:]
                    contline = line
                    break
                else:  # ordinary string
                    yield PythonToken(TOKS.STRING, token, spos, prefix)
            elif token in fstring_pattern_map:  # The start of an fstring.
                fstring_stack.append(FStringNode(fstring_pattern_map[token]))
                yield PythonToken(TOKS.FSTRING_START, token, spos, prefix)
            elif initial == "\\" and line[start:] in (
                "\\\n",
                "\\\r\n",
                "\\\r",
            ):  # continued stmt
                additional_prefix += prefix + line[start:]
                break
            else:
                if token in "([{":
                    if fstring_stack:
                        fstring_stack[-1].open_parentheses(token)
                    else:
                        paren_level += 1
                elif token in ")]}":
                    if fstring_stack:
                        fstring_stack[-1].close_parentheses(token)
                    else:
                        if paren_level:
                            paren_level -= 1
                elif (
                    token.startswith(":")
                    and fstring_stack
                    and fstring_stack[-1].parentheses_count
                    - fstring_stack[-1].format_spec_count
                    == 1
                ):
                    # `:` and `:=` both count
                    fstring_stack[-1].format_spec_count += 1
                    token = ":"
                    pos = start + 1

                yield PythonToken(TOKS.OP, token, spos, prefix)

    if contstr:
        yield PythonToken(TOKS.ERRORTOKEN, contstr, contstr_start, prefix)
        if contstr.endswith("\n") or contstr.endswith("\r"):
            new_line = True

    if fstring_stack:
        tos = fstring_stack[-1]
        if tos.previous_lines:
            yield PythonToken(
                TOKS.FSTRING_STRING,
                tos.previous_lines,
                tos.last_string_start_pos,  # type: ignore
                # Never has a prefix because it can start anywhere and
                # include whitespace.
                prefix="",
            )

    end_pos = lnum, max_
    # As the last position we just take the maximally possible position. We
    # remove -1 for the last new line.
    for indent in indents[1:]:
        indents.pop()
        yield PythonToken(TOKS.DEDENT, "", end_pos, "")
    yield PythonToken(TOKS.ENDMARKER, "", end_pos, additional_prefix)
