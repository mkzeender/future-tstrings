from __future__ import annotations

from collections.abc import Iterator
from itertools import zip_longest
from typing import TYPE_CHECKING, Literal, NamedTuple, TypeVar, final
from sys import version_info

ConversionType = Literal["a", "r", "s", None]

if not TYPE_CHECKING and version_info >= (3, 14):
    from string.templatelib import (
        Template as Template,
        Interpolation as Interpolation,
    )

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
            return 't"' + ("".join(_repr_piece(v) for v in self)) + '"'

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


def _repr_piece(v: str | Interpolation) -> str:
    if isinstance(v, str):
        return (
            v.encode("unicode_escape", errors="ignore")
            .decode("utf-8", errors="ignore")
            .replace('"', '\\"')
        )
    conv = ("!" + v.conversion) if v.conversion is not None else ""
    fmt = (":" + v.format_spec) if v.format_spec else ""

    return "{" + repr(v.value) + conv + fmt + "}"


_ConvertT = TypeVar("_ConvertT")


def convert(value: _ConvertT, conversion: ConversionType = None) -> _ConvertT | str:
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
