import sys
from ._fstrings import *  # noqa: F403

if sys.version_info > (3, 11):
    from ._fstrings_multiline import *  # noqa: F403
