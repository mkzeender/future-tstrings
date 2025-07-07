# fmt: off
from future_tstrings import _

def test_multiline_single_quote():
    v = (
        "world"
        in f"hello ........ {
            'world' + '................................................'
        }"
    )

    assert v

def multiline_tstring_single_quote():
    v = (
        t"well ..... {
            "done"
        }"
    )
