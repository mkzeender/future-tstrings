# -*- coding: future-tstrings -*-
thing = 'world'
template = t'hello {thing}'
print(template)

assert template.strings[0] == 'hello '
assert template.interpolations[0].value == 'world'