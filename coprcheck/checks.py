"""Checks to run on fetched builds."""


from contextlib import contextmanager
from distutils.spawn import find_executable
from functools import wraps
import fnmatch
import os
from shutil import rmtree
from subprocess import check_call


class MissingBinaryError(OSError):
    """The binary required for this check is not present in the $PATH."""


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


@require_bin('rpmgrill', 'rpmgrill-unpack-rpms')
def rpmgrill(project_root: str) -> None:
    """Run rpmgrill on all packages in the tree.

    *   Assumes following directory structure:
            <project_root>/<distro>/<srpm_name>/*.rpm
        The rpmgrill is run for each <distro>/<srpm_name> variant.

    Keyword arguments:
        project_root: Path to the stored rpms tree.
    """

    @contextmanager
    def unpacked(path):
        """Unpacks and then cleans files required by rpmgrill.

        Keyword arguments:
            path: the directory to be unpacked and tested.

        Returns/yields:
            path to the unpacked files.
        """

        cmd = 'rpmgrill-unpack-rpms {0}'.format(path).split()
        check_call(cmd)
        resultdir = os.path.join(path, 'unpacked')

        yield resultdir

        #rmtree(resultdir)

    for directory in rpm_dirs(project_root):
        with unpacked(directory) as grillroot:
            cmd = ['rpmgrill', grillroot]
            check_call(cmd)
