# -*- coding: future-tstrings -*-
from string.templatelib import Template


thing = "world"
template: Template = t"hello {thing}"
print(template)

assert template.strings[0] == "hello "
assert template.interpolations[0].value == "world"
