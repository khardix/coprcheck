"""COPR API data miner."""

"""Currently uses both versions of the API, since the newer one
does not provide monitor equivalent"""


from collections import namedtuple
import itertools as it

import requests


COPR_ROOT = 'https://copr.fedorainfracloud.org'
MONITOR_URL = '/api/coprs/{user}/{project}/monitor'
BUILD_URL = '/api_2/build/{build_id:d}'


# Results wrapper
BuildResult = namedtuple('BuildResult', ['build_id', 'chroot', 'url'])
BuildResult.__doc__ += ': Container for COPR build result info.'
# For 3.5+
#BuildResult.build_id.__doc__ = 'Build id.'
#BuildResult.chroot.__doc__ = 'Chroot in which the build was made.'
#BuildResult.url.__doc__ = 'Absolute URL of the resulting artifacts.'

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
        raise BuildNotFoundError(rsp.json()['message'])
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

    # Fetch and parse monitor
    packages = monitor(user, project)['packages']
    # link all builds from all packages into one iterable
    builds = it.chain.from_iterable(p['results'].values() for p in packages)
    uniq_ids = {b['build_id'] for b in builds
                              if b is not None and b['status'] == 'succeeded'}

    # Fetch URLs for all builds
    responses = (requests.get(COPR_ROOT+BUILD_TASK_URL, params={'build_id': uid})
                 for uid in uniq_ids)
    tasks = it.chain.from_iterable(r.json()['build_tasks'] for r in responses)
    yield from (task['build_task']['result_dir_url']
                for task in tasks if task['build_task']['state'] == 'succeeded')
