"""Generic utility/helper functions, classes and decorators for the
whole module.
"""


from distutils.spawn import find_executable
from functools import wraps
import fnmatch
import itertools as it
import os


class MissingBinaryError(OSError):
    """Cannot find specific executable in $PATH."""


def unique(iterable):
    """Generate unique elements from iterable, preserving order."""

    seen = set()
    for element in it.filterfalse(seen.__contains__, iterable):
        seen.add(element)
        yield element


def require_bin(*binaries: [str]):
    """Decorator which checks for binaries on a system before calling
    the decorated function.

    Arguments:
        [binary, ...]: Names of binaries to look for.
    """
    def decorator(func):

        @wraps(func)
        def check_binaries(*args, **kwargs):

            for binary in binaries:
                exe = find_executable(binary)
                if exe is None: raise MissingBinaryError(binary)

            return func(*args, **kwargs)

        return check_binaries
    return decorator


def rpm_dirs(root: str):
    """Generate paths to all directories under root that contains any RPM file.

    Keyword arguments:
        root: The top of the searched tree

    Yields:
        Paths from root (included) to the directory with RPM(s).
    """

    for root, _, flist in os.walk(root):
        if len(fnmatch.filter(flist, '*.rpm')) > 0:
            yield root
