from __future__ import annotations

from future_tstrings import ENCODING_NAMES, natively_supports_tstrings
import codecs


def install():
    codecs.register(create_codec_map().get)


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
