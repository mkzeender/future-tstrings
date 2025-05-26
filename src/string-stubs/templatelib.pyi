from collections.abc import Iterator
from typing import Literal, NamedTuple, final

__all__ = ["Template", "Interpolation"]

ConversionType = Literal["a", "r", "s", None]

@final
class Template:
    @property
    def strings(self) -> tuple[str, ...]:
        """
        A non-empty tuple of the string parts of the template,
        with N+1 items, where N is the number of interpolations
        in the template.
        """

    @property
    def interpolations(self) -> tuple[Interpolation, ...]:
        """
        A tuple of the interpolation parts of the template.
        This will be an empty tuple if there are no interpolations.
        """

    def __init__(
        self,
        *args: str | Interpolation | tuple[object, str, ConversionType, str] | None,
    ):
        """
        Create a new Template instance.

        Arguments can be provided in any order.
        """

    @property
    def values(self) -> tuple[object, ...]:
        """
        Return a tuple of the `value` attributes of each Interpolation
        in the template.
        This will be an empty tuple if there are no interpolations.
        """

    def __iter__(self) -> Iterator[str | Interpolation]:
        """
        Iterate over the string parts and interpolations in the template.

        These may appear in any order. Empty strings will not be included.
        """

    def __add__(self, other: Template) -> Template: ...
    def __radd__(self, other: Template) -> Template: ...

class Interpolation(NamedTuple):
    value: object
    expression: str
    conversion: ConversionType
    format_spec: str
