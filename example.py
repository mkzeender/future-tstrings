# use "python -m example", NOT "python example.py"

from future_tstrings import _  # <--- Magic line!


from string.templatelib import Template  # or, future_tstrings.templatelib


thing = "world"
template: Template = t"hello {thing}"

print(repr(template))  # t"hello {'world'}"

assert template.strings[0] == "hello "
assert template.interpolations[0].value == "world"
