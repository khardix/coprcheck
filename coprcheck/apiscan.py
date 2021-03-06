"""COPR API data miner."""

"""Currently uses both versions of the API, since the newer one
does not provide monitor equivalent"""


import itertools as it

import requests

from . _data_def import Chroot, BuildResult
from . _utils.generic import unique


COPR_ROOT = 'https://copr.fedorainfracloud.org'
MONITOR_URL = '/api/coprs/{user}/{project}/monitor'
BUILD_URL = '/api_2/builds/{build_id:d}'


# Possible API contact errors
ConnectionError = requests.exceptions.ConnectionError

HTTPError = requests.HTTPError

class ProjectNotFoundError(RuntimeError):
    """Indicate that a project was not found on the COPR web."""

class BuildNotFoundError(RuntimeError):
    """Indicate that a build was not found on the COPR web."""


def monitor(user: str, project: str) -> dict:
    """Get monitor for the specified user/project.

    Arguments:
        user -- The owner of the project.
        project -- The name of the project.

    Returns:
        Current project status in dictionary (JSON) format.

    Raises:
        ConnectionError -- On unreachable network.
        ProjectNotFoundError -- When specified project cannot be found in COPR.
        HTTPError -- On general server errors.
    """

    rsp = requests.get(''.join([COPR_ROOT, MONITOR_URL.format(
            user=user, project=project)]))

    if rsp.status_code == requests.codes.ok:
        return rsp.json()
    elif rsp.status_code == requests.codes.not_found:
        raise ProjectNotFoundError(rsp.json()['error'])
    else:
        rsp.raise_for_status()


def build(build_id: int) -> dict:
    """Get build information for build with the specified id.

    Arguments:
        build_id -- The numeric ID of the build.

    Returns:
        Build information with embedded build tasks in dictionary (JSON) format.
        See https://copr-rest-api.readthedocs.org/en/latest/Resources/build.html#get-build-details

    Raises:
        ConnectionError -- On unreachable network.
        BuildNotFoundError -- When specified build cannot be found in COPR.
        HTTPError -- On general server errors.
    """

    rsp = requests.get(
            ''.join([COPR_ROOT, BUILD_URL.format(build_id=build_id)]),
            params={'show_build_tasks': True})

    if rsp.status_code == requests.codes.ok:
        return rsp.json()
    elif rsp.status_code == requests.codes.not_found:
        raise BuildNotFoundError('Build #{} not found'.format(build_id))
    else:
        rsp.raise_for_status()


def current_builds(user: str, project: str): # Generator[BuildResult, None, None]
    """Generate BuildResults for all current builds in project.

    Arguments:
        user -- The owner of the project.
        project -- The name of the project.

    Yields:
        BuildResult for each current build and chroot.

    Raises:
        ConnectionError -- On unreachable network.
        ProjectNotFoundError -- When specified project cannot be found in COPR.
        HTTPError -- On general server errors.
    """

    # List of mappings of SRPMS to results
    packages = monitor(user, project)['packages']
    # Long list of all current builds on all arches
    pkg_builds = it.chain.from_iterable(
            pkg['results'].values() for pkg in packages)
    # Unique build ids across all arches and builds
    build_ids = unique(pb['build_id'] for pb in pkg_builds
            if pb is not None and pb['status'] == 'succeeded')

    # List of all build tasks associated with any build ids
    build_tasks = it.chain.from_iterable(
            build(b_id)['build_tasks'] for b_id in build_ids)
    tasks = (bt['build_task'] for bt in build_tasks if bt is not None)

    # Final build informations
    yield from (BuildResult(url=t['result_dir_url'],
                            chroot=Chroot.from_chroot_name(t['chroot_name']),
                            build_id=t['build_id'])
                for t in tasks if t is not None and t['state'] == 'succeeded')
