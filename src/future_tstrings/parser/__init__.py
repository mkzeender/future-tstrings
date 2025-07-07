from .compiler.compile import compile_to_ast
from .tokenizer import tokenize
from .parse_grammar import parse_to_cst
import ast

__all__ = "compile_to_ast", "tokenize", "parse_to_cst", "compile_to_python"


def compile_to_python(src: str, filepath: str = "<string>"):
    return ast.unparse(compile_to_ast(src, "exec", filepath=filepath))
