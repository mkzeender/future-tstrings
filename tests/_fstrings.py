# fmt: off
from future_tstrings import _


def test_fstring():
    assert f"{"hello"}" == "hello"


def test_multiline():
    assert (
        'world' in f"""hello {
            'world'
        }"""
    )
