# coding: future-tstrings
def test_nested_tstring():
    world = 'World'
    template = t"Value: {t'hello {world}'}"

    assert template.interpolations[0].value.interpolations[0].value == world