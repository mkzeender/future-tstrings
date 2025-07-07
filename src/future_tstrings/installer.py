from __future__ import annotations
import sys

import codecs

from .utils import (
    FSTRING_BUILTIN,
    TEMPLATE_BUILTIN,
    natively_supports_tstrings,
    get_native_codec,
)


_active_mode = None


def install(use_import_hook: bool = False) -> None:
    """
    Install the future-tstrings preprocessor, allowing imported modules to use t-strings.

    Args:
        use_import_hook (bool, optional): Whether to use the import hook. This leads to
        better error messages. Otherwise, uses a custom codec.

    """
    from .importer import install_import_hook, uninstall_import_hook

    global _active_mode

    if _active_mode == use_import_hook:
        # nothing to do!
        return

    if not natively_supports_tstrings():
        import string
        import builtins
        from . import templatelib

        # monkey-patch string.templatelib and builtins!
        string.templatelib = templatelib  # type: ignore
        sys.modules["string.templatelib"] = templatelib
        setattr(builtins, TEMPLATE_BUILTIN, templatelib.Template)

        # implement fstrings too! (this is only relevant for python <3.12)
        setattr(builtins, FSTRING_BUILTIN, templatelib._create_joined_string)

        if use_import_hook:
            install_import_hook()

            if _active_mode is not None:
                from .encoding import get_tstring_codec

                codecs.unregister(get_tstring_codec)

            codecs.register(get_native_codec)

        else:
            if _active_mode is not None:
                uninstall_import_hook()
                codecs.unregister(get_native_codec)

            from .encoding import get_tstring_codec

            codecs.register(get_tstring_codec)

    _active_mode = use_import_hook
