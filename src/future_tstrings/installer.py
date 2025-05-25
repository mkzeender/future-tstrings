from __future__ import annotations
import sys

from future_tstrings import ENCODING_NAMES, natively_supports_tstrings
import codecs

from future_tstrings.utils import FSTRING_BUILTIN, TEMPLATE_BUILTIN


def install():
    codecs.register(create_codec_map().get)

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


def create_codec_map():
    if natively_supports_tstrings():
        return create_native_codec_map()
    else:
        from .encoding import create_tstring_codec_map

        return create_tstring_codec_map()


def create_native_codec_map():
    import encodings

    utf_8 = encodings.search_function("utf8")

    return {name: utf_8 for name in ENCODING_NAMES}
