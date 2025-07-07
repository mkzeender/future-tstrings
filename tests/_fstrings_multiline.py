def test_multiline_single_quote():
    v = (
        "world"
        in f"hello ........ {
            'world' + '................................................'
        }"
    )

    assert v
