# from future_tstrings.main import main

# main(["experiments.py"])

import ast
from future_tstrings.parser.tokenizer.tokenize import tokenize
from future_tstrings.parser.parse_grammar import parse_to_cst
from future_tstrings.parser.compiler.compile import compile_to_ast

v = """t"hello {dude + "hi"}" """
print(*tokenize(v), sep="\n")

print(parse_to_cst(v).dump())

ast_ = compile_to_ast(v, mode="exec")

print(ast.dump(ast_, indent=2))

print(ast.unparse(ast_))
