from parso.python.token import PythonTokenTypes as TOKS
from parso.python.tokenize import (
    PythonToken,
)


def split_illegal_unicode_name(token, start_pos, prefix):
    def create_token():
        return PythonToken(
            TOKS.ERRORTOKEN if is_illegal else TOKS.NAME, found, pos, prefix
        )

    found = ""
    is_illegal = False
    pos = start_pos
    for i, char in enumerate(token):
        if is_illegal:
            if char.isidentifier():
                yield create_token()
                found = char
                is_illegal = False
                prefix = ""
                pos = start_pos[0], start_pos[1] + i
            else:
                found += char
        else:
            new_found = found + char
            if new_found.isidentifier():
                found = new_found
            else:
                if found:
                    yield create_token()
                    prefix = ""
                    pos = start_pos[0], start_pos[1] + i
                found = char
                is_illegal = True

    if found:
        yield create_token()


def close_fstring_if_necessary(
    fstring_stack, string, line_nr, column, additional_prefix
):
    for fstring_stack_index, node in enumerate(fstring_stack):
        lstripped_string = string.lstrip()
        len_lstrip = len(string) - len(lstripped_string)
        if lstripped_string.startswith(node.quote):
            token = PythonToken(
                TOKS.FSTRING_END,
                node.quote,
                (line_nr, column + len_lstrip),
                prefix=additional_prefix + string[:len_lstrip],
            )
            additional_prefix = ""
            assert not node.previous_lines
            del fstring_stack[fstring_stack_index:]
            return token, "", len(node.quote) + len_lstrip
    return None, additional_prefix, 0
