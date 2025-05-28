
future-tstrings
===============

A backport of tstrings to python<3.14

Also serves as a backport of full-syntax fstrings (PEP701-style) to python <3.12.

Does nothing on 3.14 or higher.

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

from string.templatelib import Template
assert isinstance(template, Template)
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
template = __create_template__('hello ', (thing, 'thing', None, ''))
print(template)
```

## Integrating with template processing tools

Libraries that consume template strings (html parsers, etc) do not need to do anything extra to support future-tstrings, except:

They should NOT disable this behavior on python<3.14. Instead, they should only disable the behavior if `import strings.templatelib` fails.

## How does this work?

`future-tstrings` has two parts:
1. An `importer` which transpiles t-strings and f-strings to older versions of python
1. An alternative utf-8 compatible `codec` which does the same (in case you can't use the importer)
1. A `.pth` file which registers the importer on interpreter startup.

## Alternative python environments

In environments (such as aws lambda) where packages are not truly installed packages, the `.pth` magic will not work.

Additionally, in environments that don't load (directly) import .py files, the importer will not work.

For those circumstances, you'll need to manually initialize `future-tstrings`
in a regular python module. For instance:

```python
from future_tstrings.installer import install

install()

from actual_main import main

if __name__ == '__main__':
    main()
```
