
future-tstrings
===============

A backport of tstrings to python<3.14

Also serves as a backport of full-syntax fstrings (PEP701-style) to python <3.12.

Does nothing on 3.14 or higher.

This api may be unstable until the release of python 3.14 to ensure it is fully compatible.


## Installation

`pip install future-tstrings`


## Usage

Include the following magic line at the top of the file (before regular imports)

```python
from future_tstrings import _
```

And then write python 3.14 tstring and fstring code as usual!


```python
- example.py

from string.templatelib import Template  # or, future_tstrings.templatelib

thing = "world"
template: Template = t"hello {thing}"

print(repr(template))
# t"hello {'world'}"

assert template.strings[0] == "hello "
assert template.interpolations[0].value == "world"

```

```console
$ python -m example
t"hello {'world'}"
```

## Showing compiled source

`future-tstrings` also includes a cli to show transformed source.

```console
$ future-tstrings example.py

thing = 'world'
template = __create_template__('hello ', (thing, 'thing', None, ''))
print(template)
```

## Integrating with template processing tools

Libraries that consume template strings (html parsers, etc) do not need to do anything extra to support future-tstrings, except:

They should NOT disable this behavior on python<3.14. To support future-tstrings without listing it as a dependency, use the following:

```python
try:
    from string.templatelib import Template
except ImportError:
    if TYPE_CHECKING:
        raise
    else:
        class Template:
            pass


```

## How does this work?

`future-tstrings` has two parts:
1. An `importer` which transpiles t-strings and f-strings to code understood by older versions of python

1. A `.pth` file which registers the importer on interpreter startup.

## Alternative python environments

In environments (such as aws lambda) where packages are not installed via pip, the `.pth` magic will not work.

For those circumstances, you'll need to manually initialize `future-tstrings`
in a wrapper python module. For instance:

```python
from future_tstrings.installer import install

install()

from actual_main import main

if __name__ == '__main__':
    main()
```

Additionally, for zipped or frozen packages, the importer will not work. In such environments, you will need to use the ```future-tstrings``` command-line compiler before the code is zipped, frozen, etc.
