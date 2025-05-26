from __future__ import annotations
import ast
from collections.abc import Mapping
from typing import Any, Literal, overload
from ..parse_grammar import parse_to_cst

from .ast import CstToAstCompiler, CstNode

_NULL_LOCATION: dict = dict(
    lineno=1,
    col_offset=0,
    end_lineno=1,
    end_col_offset=0,
)


class AstModifier(ast.NodeTransformer):
    def __init__(self, replacements: Mapping[tuple[int, int], ast.AST]):
        self.replacements = replacements

    def visit_Tuple(self, node: ast.Tuple) -> Any:
        if (v := self.replacements.get((node.lineno, node.col_offset))) is not None:
            return v
        return node


@overload
def compile_to_ast(
    code: str | CstNode, mode: Literal["exec"], filepath: str = "<string>"
) -> ast.Module: ...
@overload
def compile_to_ast(
    code: str | CstNode, mode: Literal["eval"], filepath: str = "<string>"
) -> ast.Expression: ...
@overload
def compile_to_ast(
    code: str | CstNode, mode: Literal["single"], filepath: str = "<string>"
) -> ast.Interactive: ...
@overload
def compile_to_ast(
    code: str | CstNode, mode: Literal["func_type"], filepath: str = "<string>"
) -> ast.FunctionType: ...
def compile_to_ast(
    code: str | CstNode,
    mode: Literal["exec", "eval", "single", "func_type"],
    filepath: str = "<string>",
) -> ast.AST:
    cst_node: CstNode
    src: str | None
    if isinstance(code, str):
        cst_node = parse_to_cst(code)
        src = code
    else:
        cst_node = code
        src = None

    compiler = CstToAstCompiler(filename=filepath, code=src)
    compiler.visit(cst_node)
    ast_: ast.AST = ast.parse(
        cst_node.get_code(), mode=mode, filename=filepath, type_comments=True
    )

    ast_ = AstModifier(compiler.locs_to_override).visit(ast_)

    return ast_
