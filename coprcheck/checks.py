"""Checks to run on fetched builds."""


from contextlib import contextmanager
import os
from shutil import rmtree
from subprocess import check_call

from . _utils import MissingBinaryError, require_bin, rpm_dirs


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
