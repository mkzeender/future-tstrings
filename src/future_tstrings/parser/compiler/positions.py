from __future__ import annotations

from typing import NamedTuple, Protocol, TypedDict, overload, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypeIs


class Located(Protocol):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


def has_loc(v) -> TypeIs[Located]:
    return True  # hack
    return hasattr(v, "lineno")


@overload
def add(*a: int) -> int: ...
@overload
def add(*a: int | None) -> int | None: ...
def add(*a: int | None) -> int | None:
    return None if any(v is None for v in a) else sum(a)  # type: ignore


class OptionalPosDict(TypedDict, total=False):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


class PosDict(TypedDict, total=True):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


class PosTuple(NamedTuple):
    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


def position_of(node) -> PosDict:
    return PosDict(
        lineno=node.start_pos[0],
        col_offset=node.start_pos[1],
        end_lineno=node.end_pos[0],
        end_col_offset=node.end_pos[1],
    )
