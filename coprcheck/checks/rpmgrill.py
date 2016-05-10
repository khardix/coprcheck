"""rpmgrill scan of COPR contents."""


from contextlib import contextmanager
import json
import os
from shutil import rmtree
from subprocess import check_call, DEVNULL

from .. _utils.generic import require_bin, rpm_dirs


@require_bin('rpmgrill-unpack-rpms')
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

    rmtree(resultdir)


def parse_results(grill_results: dict) -> (str, dict):
    """Parse the rpmgrill result logs.

    Keyword arguments:
        grill_results: rpmgrill result data.

    Returns:
        A (package, stats) tuple. Package is full NVR of scanned package,
        stats is a nested dictionary of failed checks:
        {FailedCheck: {code: diagnostic}}
    """

    pkginfo = grill_results['package']
    pkg_nvr = '-'.join([
        pkginfo['name'],
        pkginfo['version'],
        pkginfo['release'],
        ])

    stats = {test['module']:
                {result['code']: result['diag'] for result in test['results']}
            for test in grill_results['tests']
            if test['results']
            }

    return (pkg_nvr, stats)


@require_bin('rpmgrill')
def scan(project_root: str) -> dict:
    """Run rpmgrill on all packages in the tree.

    *   Assumes following directory structure:
            <project_root>/<distro>/<srpm_name>/*.rpm
        The rpmgrill is run for each <distro>/<srpm_name> variant.

    Keyword arguments:
        project_root: Path to the stored rpms tree.
    """

    result = dict()

    for directory in rpm_dirs(project_root):

        with unpacked(directory) as grillroot:
            cmd = ['rpmgrill', grillroot]
            check_call(cmd, stderr=DEVNULL)

            with open(os.path.join(grillroot, 'rpmgrill.json')) as res:
                grill_stats = json.load(res)

        nvr, stats = parse_results(grill_stats)
        result[nvr] = stats

    return result
