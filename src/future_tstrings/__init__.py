from __future__ import annotations
import sys

__all__ = ["install"]

TEMPLATE_BUILTIN = "__create_template__"
FSTRING_BUILTIN = "__create_fstring__"



def install() -> None:
    """
    Install the future-tstrings cross-compiler, allowing imported modules to use t-strings.
    In most environments, future-tstrings is installed automatically.

    """
    if sys.version_info >= (3, 14):
        # Nothing to do in these versions!
        return

    from .importer import install_import_hook

    import string
    import builtins
    from . import templatelib

    # monkey-patch string.templatelib and builtins!
    string.templatelib = templatelib  # type: ignore
    sys.modules["string.templatelib"] = templatelib
    setattr(builtins, TEMPLATE_BUILTIN, templatelib.Template)

    # implement fstrings too! (this is only relevant for python <3.12)
    setattr(builtins, FSTRING_BUILTIN, templatelib._create_joined_string)

    install_import_hook()
