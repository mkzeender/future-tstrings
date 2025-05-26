from __future__ import annotations

import ast
import codecs
import io

from . import ENCODING_NAMES
from .utils import utf_8
from .parser import compile_to_ast

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Buffer


class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, input, errors, final):
        if final:
            return decode(input, errors)
        else:
            return "", 0


class ReadableBuffer(Protocol):
    def read(self) -> bytes: ...


class StreamReader(codecs.StreamReader):
    """decode is deferred to support better error messages"""

    _decoded = False

    @property
    def stream(self):
        if not self._decoded:
            text, _ = decode(self._stream.read())
            self._stream = io.BytesIO(text.encode("UTF-8"))
            self._decoded = True
        return self._stream

    @stream.setter
    def stream(self, stream: ReadableBuffer):  # type: ignore
        self._stream = stream
        self._decoded = False


def decode(b: Buffer, errors="strict"):
    src, length = utf_8.decode(b, errors)
    ast_ = compile_to_ast(src, mode="exec", filepath="<buffered file>")
    if errors == "strict":
        # test compilation. This will lead to better error messages in case of SyntaxError
        compile(ast_, filename="<future-fstring encoded file>", mode="exec")
    new_src = ast.unparse(ast_) + "\n"

    return new_src, length


# codec api
def create_tstring_codec_map() -> dict[str, codecs.CodecInfo]:
    return {
        name: codecs.CodecInfo(
            name=name,
            encode=utf_8.encode,
            decode=decode,
            incrementalencoder=utf_8.incrementalencoder,
            incrementaldecoder=None,
            streamreader=None,
            streamwriter=utf_8.streamwriter,
        )
        for name in ENCODING_NAMES
    }
