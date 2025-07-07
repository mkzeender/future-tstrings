from __future__ import annotations
from ast import AST, NodeTransformer


from .positions import (
    OptionalPosDict,
    PosDict,
    PosTuple,
    add,
    has_loc,
)

TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Any, Unpack


class AstOffsetApplier(NodeTransformer):
    def __init__(self, **offset: Unpack[OptionalPosDict]) -> None:
        super().__init__()
        self.offset = offset

    def visit(self, node: AST) -> Any:
        _apply_offset_to_ast_node(node, **self.offset)

        return super().visit(node)


def apply_offset(
    root_node: AST, offset: PosDict, root_offset: OptionalPosDict = OptionalPosDict()
) -> None:
    AstOffsetApplier(**offset).visit(root_node)
    _apply_offset_to_ast_node(root_node, **root_offset)


def _apply_offset_to_ast_node(node: AST, **offset: Unpack[OptionalPosDict]):
    try:
        assert has_loc(node)
        if "lineno" in offset:
            node.lineno += offset["lineno"] - 1
            node.end_lineno = add(node.end_lineno, offset["lineno"], -1)
        if "col_offset" in offset:
            node.col_offset += offset["col_offset"]
            node.end_col_offset = add(node.end_col_offset, offset["col_offset"])
    except (AttributeError, AssertionError):
        pass


def syntaxerror_offset(e: SyntaxError, pos: PosDict):
    line_offset, col_offset, _, _ = PosTuple(**pos)
    col_offset -= 1

    e.lineno = add(line_offset, e.lineno)
    e.offset = add(col_offset, e.offset)
    e.end_lineno = add(line_offset, e.end_lineno)
    e.end_offset = add(col_offset, e.end_offset)
