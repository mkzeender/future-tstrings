from __future__ import annotations
import sys

from . import (
    ENCODING_NAMES,
    natively_supports_tstrings,
    FSTRING_BUILTIN,
    TEMPLATE_BUILTIN,
    utf_8,
)
import codecs

_installed = False


def install(use_import_hook: bool = True):
    """
    Install the future-tstrings preprocessor, allowing imported modules to use t-strings.

    Args:
        use_import_hook (bool, optional): Whether to use the import hook. This leads to
        better error messages. Otherwise, uses a custom encoding. Defaults to True.

    """
    global _installed
    if _installed:
        return
    _installed = True

    codec_map_factory = create_native_codec_map

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

        if use_import_hook or (__debug__ and use_import_hook is None):
            from .importer import install_import_hook

            install_import_hook()
        else:
            from .encoding import create_tstring_codec_map

            codec_map_factory = create_tstring_codec_map

    # register codec
    codecs.register(codec_map_factory().get)


def create_native_codec_map():
    return {name: utf_8 for name in ENCODING_NAMES}
