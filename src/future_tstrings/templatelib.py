from __future__ import annotations

from collections.abc import Iterator
from itertools import zip_longest
from typing import TYPE_CHECKING, Literal, NamedTuple, TypeVar, final
from . import natively_supports_tstrings

ConversionType = Literal["a", "r", "s", None]

if not TYPE_CHECKING and natively_supports_tstrings():
    from string.templatelib import (
        Template as Template,
        Interpolation as Interpolation,
    )  # type: ignore

else:

    @final
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
            self,
            *args: str | Interpolation | tuple[object, str, ConversionType, str] | None,
        ):
            """
            Create a new Template instance.

            Arguments can be provided in any order.
            """
            super().__init__()
            strings = [""]
            interps = []
            for arg in args:
                if isinstance(arg, str):
                    strings[-1] += arg
                elif isinstance(arg, tuple):
                    interps.append(Interpolation(*arg))
                    strings.append("")
                elif arg is None:
                    pass
                else:
                    raise TypeError(
                        f"Argument of type {type(arg)} is not supported by Template()"
                    )

            self._strings = tuple(strings)
            self._interpolations = tuple(interps)

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
            for s, i in zip_longest(self.strings, self.interpolations, fillvalue=None):
                if s:
                    yield s
                if i is not None:
                    yield i

        def __repr__(self) -> str:
            return (
                "t'"
                + (
                    "".join(
                        (_escape_string(v) if isinstance(v, str) else v._create_repr())
                        for v in self
                    )
                )
                + "'"
            )

        def __add__(self, other: Template) -> Template:
            if isinstance(other, Template):
                return Template(*self, *other)
            return NotImplemented

        def __radd__(self, other: Template) -> Template:
            if isinstance(other, Template):
                return Template(*other, *self)
            return NotImplemented

    class Interpolation(NamedTuple):
        value: object
        expression: str
        conversion: ConversionType
        format_spec: str

        def _create_repr(self):
            conv = ("!" + self.conversion) if self.conversion is not None else ""
            fmt = (":" + self.format_spec) if self.format_spec else ""

            return f"{{{self.value!r}{conv}{fmt}}}"


def _escape_string(s: str):
    s = repr(s)
    q = s[0]
    s = s[1:-1]
    if q == '"':
        s = s.replace("'", r"\'")

    return s


_T = TypeVar("_T")


def convert(value: _T, conversion: ConversionType = None) -> _T | str:
    """Convert a value to string based on conversion type"""
    if conversion == "a":
        return ascii(value)
    elif conversion == "r":
        return repr(value)
    elif conversion == "s":
        return str(value)
    return value


def to_fstring(template: Template) -> str:
    """Join the pieces of a template string as if it was an fstring"""
    parts = []
    for item in template:
        if isinstance(item, str):
            parts.append(item)
        else:
            value = convert(item.value, item.conversion)
            value = format(value, item.format_spec)
            parts.append(value)
    return "".join(parts)


def _create_joined_string(*args: str | tuple):
    """implements fstrings on python < 3.12"""
    return to_fstring(Template(*args))
