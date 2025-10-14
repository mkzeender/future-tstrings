from __future__ import annotations

from collections.abc import Iterator
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, TypeVar, final
from sys import version_info

__all__ = ["Template", "Interpolation", "convert"]
__name__ = 'string.templatelib'

ConversionType = Literal["a", "r", "s", None]

if TYPE_CHECKING:
    from typing import Never

if not TYPE_CHECKING and version_info >= (3, 14):
        from string.templatelib import ( # type: ignore
            Template as Template,
            Interpolation as Interpolation,
            convert as convert
        )

else:

    @final
    class Template:
        
        strings: tuple[str, ...]
        interpolations: tuple[Interpolation, ...]

        __slots__ = "strings", "interpolations"


        def __init__(
            self,
            *args: str | Interpolation,
        ) -> None:
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
                elif isinstance(arg, Interpolation):
                    interps.append(arg)
                    strings.append("")
                elif isinstance(arg, tuple):
                    interps.append(Interpolation(*arg)) # type: ignore
                    strings.append("")
                elif arg is None:
                    pass
                else:
                    raise TypeError(
                        f"Argument of type {type(arg)} is not supported by Template()"
                    )

            _set_strings(self, tuple(strings))
            _set_interpolations(self, tuple(interps))

        
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
                'Template('
                    'strings=' + repr(self.strings) + ', ' +
                    'interpolations=' + repr(self.interpolations) +
                ')'
            )

        def __add__(self, other: Template) -> Template:
            if isinstance(other, Template):
                return Template(*self, *other)
            return NotImplemented

        def __radd__(self, other: Template) -> Template:
            if isinstance(other, Template):
                return Template(*other, *self)
            return NotImplemented
        
        def __setattr__(self, name: str, value: Any) -> Never:
            raise AttributeError('Template object is immutable', name=name, obj=self)
        
    _set_strings = Template.strings.__set__ # type: ignore
    _set_interpolations = Template.interpolations.__set__ # type: ignore

    class Interpolation(NamedTuple):
        value: object
        expression: str
        conversion: ConversionType
        format_spec: str

        def __repr__(self) -> str:
            return (
                'Interpolation(' +
                    repr(self.value) + ', ' +
                    repr(self.expression) + ', ' +
                    repr(self.conversion) + ', ' +
                    repr(self.format_spec) +
                ')'
            )


    _ConvertT = TypeVar("_ConvertT")


    def convert(value: _ConvertT, /, conversion: ConversionType) -> _ConvertT | str:
        """Convert a value to string based on conversion type"""
        if conversion is None:
            return value
        if conversion == "a":
            return ascii(value)
        if conversion == "r":
            return repr(value)
        if conversion == "s":
            return str(value)
        raise ValueError('invalid conversion specifier: ' + str(conversion))


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


    def _create_joined_string(*args):
        """implements fstrings on python < 3.12"""
        return to_fstring(Template(*args))
