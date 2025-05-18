from __future__ import annotations

from collections.abc import Iterator
from itertools import zip_longest
import sys
from typing import TYPE_CHECKING, Literal, NamedTuple
from . import natively_supports_tstrings

if sys.version_info >= (3, 10) or TYPE_CHECKING:
    ConversionType = Literal["a", "r", "s"] | None
else:
    ConversionType = ...

if not TYPE_CHECKING and natively_supports_tstrings():
    from string.templatelib import (
        Template as Template,
        Interpolation as Interpolation,
    )  # type: ignore

else:

    class Template:
        __slots__ = "_strings", "_interpolations"

        @property
        def strings(self) -> tuple[str, ...]:
            """
            A non-empty tuple of the string parts of the template,
            with N+1 items, where N is the number of interpolations
            in the template.
            """
            return self._strings

        @property
        def interpolations(self) -> tuple[Interpolation, ...]:
            """
            A tuple of the interpolation parts of the template.
            This will be an empty tuple if there are no interpolations.
            """
            return self._interpolations

        def __init__(
            self, *args: str | Interpolation | tuple[object, str, ConversionType, str]
        ):
            """
            Create a new Template instance.

            Arguments can be provided in any order.
            """
            super().__init__()
            self._strings = tuple(str(x) for i, x in enumerate(args) if not i % 2)
            self._interpolations = tuple(
                Interpolation(*x)  # type: ignore
                for i, x in enumerate(args)
                if i % 2
            )

        @property
        def values(self) -> tuple[object, ...]:
            """
            Return a tuple of the `value` attributes of each Interpolation
            in the template.
            This will be an empty tuple if there are no interpolations.
            """
            return tuple(i.value for i in self.interpolations)

        def __iter__(self) -> Iterator[str | Interpolation]:
            """
            Iterate over the string parts and interpolations in the template.

            These may appear in any order. Empty strings will not be included.
            """
            for s, i in zip_longest(self.strings, self.interpolations):
                if s:
                    yield s
                if i is not None:
                    yield i

        def __repr__(self) -> str:
            return "t" + repr(
                "".join((v if isinstance(v, str) else v._create_repr()) for v in self)
            )

    class Interpolation(NamedTuple):
        value: object
        expression: str
        conversion: ConversionType
        format_spec: str

        def _create_repr(self):
            conv = ("!" + self.conversion) if self.conversion is not None else ""
            fmt = (":" + self.format_spec) if self.format_spec is not None else ""

            return "{" + self.expression + conv + fmt + "}"
