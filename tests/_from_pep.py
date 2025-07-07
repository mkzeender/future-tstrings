from future_tstrings import _


def test_creation():
    from string.templatelib import Template

    template = t"This is a template string."
    assert isinstance(template, Template)


def test_strings_and_interp():
    name = "World"
    template = t"Hello {name}"
    assert template.strings[0] == "Hello "
    assert template.interpolations[0].value == "World"


def test_interpolation():
    name = "World"
    template = t"Hello {name}"
    assert template.interpolations[0].value == "World"
    assert template.interpolations[0].expression == "name"


def test_conversion():
    name = "World"
    template = t"Hello {name!r}"
    assert template.interpolations[0].conversion == "r"


def test_fmt_spec():
    value = 42
    template = t"Value: {value:.2f}"
    assert template.interpolations[0].format_spec == ".2f"


def test_nested_fmt_spec():
    value = 42
    precision = 2
    template = t"Value: {value:.{precision}f}"
    assert template.interpolations[0].format_spec == ".2f"


def test_nested_tstring():
    world = "World"
    template = t"Value: {t'hello {world}'}"

    assert template.interpolations[0].value.interpolations[0].value == world
