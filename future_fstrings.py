# from future_tstrings.main import main

# main(["experiments.py"])

from future_tstrings.parser.tokenizer.tokenize import tokenize
from future_tstrings.parser.parse_grammar import parse_to_cst

v = """t"hello {world}" """
print(*tokenize(v), sep="\n")

print(parse_to_cst(v).dump())
