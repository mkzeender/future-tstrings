
future-tstrings
===============

A backport of tstrings to python<3.14

Also serves as a backport of full-syntax fstrings (PEP701-style) to python <3.12.

This api may be unstable until the release of python 3.14 to ensure it is fully compatible.


## Installation

`pip install future-tstrings`


## Usage

Include the following encoding cookie at the top of your file (this replaces
the utf-8 cookie if you already have it):

```python
# -*- coding: future-tstrings -*-
```

And then write python 3.14 tstring and fstring code as usual!


```python
- example.py

# -*- coding: future-tstrings -*-
thing = 'world'
template = t'hello {thing}'
print(template)

assert template.strings[0] == 'hello '
assert template.interpolations[0].value == 'world'
```

```console
$ python -m example
t"hello {'world'}"
```

## Showing transformed source

`future-tstrings` also includes a cli to show transformed source.

```console
$ future-tstrings example.py
thing = 'world'
print('hello {}'.format((thing)))
```

## How does this work?

`future-tstrings` has two parts:

1. A utf-8 compatible `codec` which performs source manipulation
    - The `codec` first decodes the source bytes using the UTF-8 codec
    - The `codec` then leverages the `parso` library to recompile the
      t-strings and f-strings.
2. A `.pth` file which registers a codec on interpreter startup.

## when you aren't using normal `site` registration

in setups (such as aws lambda) where you utilize `PYTHONPATH` or `sys.path`
instead of truly installed packages, the `.pth` magic above will not take.

for those circumstances, you'll need to manually initialize `future-tstrings`
in a python file that does not use them. For instance:

```python
from future_tstrings.installer import install

install()

from actual_main import main

if __name__ == '__main__':
    main()
```
