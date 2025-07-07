from __future__ import annotations
from ast import (
    AST,
    Call,
    Load,
    Name,
)
import ast
from collections.abc import Iterator
import sys
from parso.python.tree import (
    PythonBaseNode as CstBaseNode,
    PythonNode as CstNode,
    Operator as CstOperator,
    PythonErrorLeaf as CstErrorLeaf,
    PythonErrorNode as CstErrorNode,
    FStringString as CstFstringString,
    FStringStart as CstFstringStart,
    FStringEnd as CstFstringEnd,
)
from parso.tree import NodeOrLeaf as CstNodeOrLeaf


from future_tstrings import FSTRING_BUILTIN
from future_tstrings import TEMPLATE_BUILTIN

from .ast_apply_offset import (
    apply_offset,
    syntaxerror_offset,
)
from . import compile as future_compiler
from .positions import (
    OptionalPosDict,
    PosDict,
    PosTuple,
    position_of,
)

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Never, Unpack


def _compile_with_offset(
    code: str,
    filepath: str,
    pos: PosDict,
    root_pos: OptionalPosDict = OptionalPosDict(),
) -> ast.expr:
    try:
        expr = future_compiler.compile_to_ast(code, mode="eval", filepath=filepath).body
    except SyntaxError as e:
        syntaxerror_offset(e, pos)
        raise

    apply_offset(expr, pos, root_offset=root_pos)

    return expr


def compile_subexpr(node: CstNodeOrLeaf, filepath: str) -> ast.expr:
    code: str = node.get_code(include_prefix=False)  # type: ignore
    return _compile_with_offset(code, filepath, position_of(node))


# def compile_fstring_expr(node: CstNode, filepath: str) -> ast.expr:
#     code: str = node.get_code(include_prefix=False)
#     code = 'f"' + code + '"'

#     pos = position_of(node)

#     # account for the f" at the start of code
#     pos["col_offset"] -= 2
#     pos["end_col_offset"] = add(pos["end_col_offset"], -2)

#     return _compile_with_offset(code, filepath, pos)


class CstToAstCompiler:
    def __init__(self, code: str | None = None, filename: str = "<string>") -> None:
        self.locs_to_override = dict[tuple[int, int], AST]()
        self.filename = filename
        self.code = code

    def generic_visit(self, node: CstNodeOrLeaf) -> CstNodeOrLeaf:
        if isinstance(node, (CstErrorLeaf, CstErrorNode)):
            self.generic_error(node)
        if isinstance(node, (CstBaseNode, CstNode)):
            for i, child in enumerate(node.children):
                node.children[i] = self.visit(child)
        return node

    def generic_error(
        self, node: CstNodeOrLeaf, msg=None, **position: Unpack[OptionalPosDict]
    ) -> Never:
        if isinstance(node, (CstErrorNode, CstErrorLeaf)):
            child: CstNodeOrLeaf = node
            while children := getattr(child, "children", None):
                for child in children:
                    if isinstance(child, (CstErrorNode, CstErrorLeaf)):
                        break
                else:
                    child = node
                    break
            if not isinstance(child, (CstErrorLeaf, CstErrorNode)):
                bad_child = child.get_next_leaf()
            else:
                bad_child = child
            msg = f"""{
                repr(
                    bad_child.get_code(include_prefix=False)
                    if bad_child is not None
                    else "EOF"
                )
            } is not understood here."""
            if bad_child is not node and bad_child is not None:
                self.generic_error(bad_child, msg=msg)

        pos = position_of(node)
        pos.update(position)
        lineno, col_offset, end_lineno, end_col_offset = PosTuple(**pos)

        if self.code is None:
            code_line = None
        else:
            code_line = self.code.splitlines()[lineno - 1]
            if lineno != end_lineno:
                end_col_offset = len(code_line) - 1
                end_lineno = lineno
        if msg is None:
            msg = f"Unexpected {node.type} here."

        if end_col_offset is None:
            end_col_offset = col_offset + 1

        if end_lineno is None:
            end_lineno = lineno

        if sys.version_info >= (3, 10):
            details = (
                self.filename,
                lineno,
                col_offset + 1,
                code_line,
                lineno,
                end_col_offset + 1,
            )
        else:
            details = (
                self.filename,
                lineno,
                col_offset + 1,
                code_line,
            )

        raise SyntaxError(msg, details)

    def visit(self, node: CstNodeOrLeaf) -> CstNodeOrLeaf:
        return getattr(self, "visit_" + node.type, self.generic_visit)(node)

    def visit_fstring(self, node: CstNode) -> CstNodeOrLeaf:
        is_tstring: bool = "t" in node.children[0].get_code(include_prefix=False)  # type: ignore
        if not is_tstring and sys.version_info >= (3, 12):
            # unmodified fstring
            return node

        self.locs_to_override[node.start_pos] = self.create_joined_string(
            node, is_tstring=is_tstring
        )

        prefix: str = node.get_first_leaf().prefix  # type: ignore
        code = node.get_code(include_prefix=False)
        lines = code.splitlines()
        filler: str = ("\n" * (len(lines) - 1)) + (" ") * len(lines[-1])

        return CstNode(
            "atom",
            [
                CstOperator("(", start_pos=node.start_pos, prefix=prefix),
                CstOperator(
                    ")", start_pos=(node.end_pos[0], node.end_pos[1] - 1), prefix=filler
                ),
            ],
        )

    def create_fmt_expression(
        self, node: CstNode
    ) -> Iterator[ast.Tuple | ast.Constant]:
        pos = position_of(node)
        conversion = ast.Constant(None, **pos)
        fmt_spec: ast.expr = ast.Constant("", **pos)
        expr_node: CstNodeOrLeaf | None = None
        for child in node.children:
            if isinstance(child, CstOperator):
                if child.value == "=":
                    suffix: str = child.get_next_sibling().get_first_leaf().prefix  # type: ignore

                    eq_text: str = expr_node.get_code() + child.get_code() + suffix  # type: ignore
                    yield ast.Constant(value=eq_text, **position_of(child))
            elif isinstance(child, CstNode) and child.type == "fstring_conversion":
                conversion = ast.Constant(child.children[1].value, **position_of(child))  # type: ignore
            elif isinstance(child, CstNode) and child.type == "fstring_format_spec":
                fmt_spec = self.create_joined_string(child, is_tstring=False)
            elif isinstance(child, (CstErrorLeaf, CstErrorNode)):
                self.generic_error(node)
            else:
                expr_node = child

        assert expr_node is not None
        expr_pos = position_of(expr_node)
        yield ast.Tuple(
            elts=[
                compile_subexpr(expr_node, self.filename),
                ast.Constant(value=expr_node.get_code(), **expr_pos),
                conversion,
                fmt_spec,
            ],
            ctx=ast.Load(),
            **pos,
        )

    def create_joined_string(
        self, node: CstNode, is_tstring: bool
    ) -> Call | ast.Constant:
        factory_name = TEMPLATE_BUILTIN if is_tstring else FSTRING_BUILTIN
        pos = position_of(node)
        parts = list[ast.expr]()
        for child in node.children:
            if isinstance(child, CstOperator) and child.value == ":":
                pass
            elif isinstance(child, (CstFstringStart, CstFstringEnd)):
                pass
            elif isinstance(child, CstFstringString):
                parts.append(ast.Constant(value=child.value, **pos))
            elif isinstance(child, CstNode) and child.type == "fstring_expr":
                parts.extend(self.create_fmt_expression(child))
            else:
                self.generic_error(child)

        if not is_tstring and len(parts) == 1 and isinstance(parts[0], ast.Constant):
            return parts[0]

        expr = Call(
            func=Name(id=factory_name, ctx=Load(), **pos),
            args=parts,
            keywords=[],
            **pos,
        )

        return expr
