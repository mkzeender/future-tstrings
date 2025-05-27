from __future__ import annotations

# Limit how much we import. This module is loaded at Python startup!!!
# Don't import things until they are needed.
import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import spec_from_loader
from pathlib import Path
from . import ENCODING_NAMES, utf_8
from tokenize import detect_encoding


TYPE_CHECKING = False
if TYPE_CHECKING:
    from os import PathLike
    from collections.abc import Buffer, Sequence
    from ast import Expression, Interactive, Module
    from types import CodeType, ModuleType

# coding_cookie = re.compile(rb"^\s*#.*coding[=:]\s*future[-_]tstrings(\s|$)")


def _decode_path(path: str | PathLike | Buffer) -> str:
    if isinstance(path, str):
        return path
    try:
        return str(Path(path))  # type: ignore
    except Exception:
        return bytes(path).decode()  # type: ignore


class TstringFileFinder(MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        try:
            if target is not None:
                return None

            name = fullname.split(".")[-1]
            if path is None:
                path = sys.path
            for dir in path:
                for file in Path(dir).glob(f"{name}.[pP][yY]"):
                    file = file.resolve()
                    with file.open("br") as f:
                        encoding, _ = detect_encoding(f.readline)
                    if encoding in ENCODING_NAMES:
                        return spec_from_loader(
                            name=fullname,
                            loader=FutureTstringsLoader(
                                fullname=fullname, path=str(file)
                            ),
                        )
                    return None
        except FileNotFoundError:
            pass
        except Exception:
            import traceback

            print("Exception ignored in importer:", sys.stderr)
            traceback.print_exc()


tstring_importer = TstringFileFinder()


class FutureTstringsLoader(SourceFileLoader):
    def __init__(self, fullname: str, path: str) -> None:
        super().__init__(fullname, path)

    def source_to_code(
        self,
        data: Buffer | str | Module | Expression | Interactive,
        path: Buffer | str | PathLike[str],
    ) -> CodeType:
        from ast import AST
        from future_tstrings.parser import compile_to_ast

        path = _decode_path(path)

        if isinstance(data, str):
            pass
        elif isinstance(data, AST):
            # already valid Python AST
            return super().source_to_code(data, path)
        else:
            data, _ = utf_8.decode(data)

        ast = compile_to_ast(data, mode="exec", filepath=path)

        return super().source_to_code(ast, path)

    def get_source(self, fullname: str) -> str | None:
        print("getting source...")
        with open(self.path, "r", newline=None, encoding="utf-8") as f:
            return f.read()


def install_import_hook():
    sys.meta_path.insert(0, tstring_importer)
