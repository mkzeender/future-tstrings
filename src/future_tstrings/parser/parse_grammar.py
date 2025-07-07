from parso.grammar import PythonGrammar
from parso.python.parser import Parser
from parso.python.diff import DiffParser
from parso.utils import parse_version_string
from importlib.resources import read_text

from parso.python.tree import PythonNode as CstNode
from parso.utils import PythonVersionInfo

from .tokenizer.tokenize import tokenize_lines

from . import __name__ as pkg_anchor


def parse_to_cst(src: str) -> CstNode:
    gram = load_grammar()
    return gram.parse(src)


class FutureGrammar(PythonGrammar):
    def __init__(self, version_info: PythonVersionInfo, bnf_text: str):
        super(PythonGrammar, self).__init__(
            bnf_text,
            tokenizer=self._tokenize_lines,
            parser=Parser,
            diff_parser=DiffParser,
        )
        self.version_info = version_info

    def _tokenize_lines(self, lines, **kwargs):
        return tokenize_lines(lines, **kwargs)


_gram = None


def load_grammar() -> FutureGrammar:
    global _gram
    if _gram is None:
        version = parse_version_string("3.13")
        gram_text = read_text(
            pkg_anchor,
            "xgrammar313.txt",
        )
        _gram = FutureGrammar(version_info=version, bnf_text=gram_text)

    return _gram
