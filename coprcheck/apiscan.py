"""COPR API data miner."""

"""Currently uses both versions of the API, since the newer one
does not provide monitor equivalent"""


import itertools as it

import requests


COPR_ROOT = 'https://copr.fedorainfracloud.org'
MONITOR_URL = '/api/coprs/{user}/{project}/monitor'
BUILD_TASK_URL = '/api_2/build_tasks'


class ProjectNotFoundError(RuntimeError):
    """Indicate that the project was not found by the COPR web."""


def monitor(user: str, project: str) -> dict:
    """Fetch monitor for the specified project."""

    rsp = requests.get(''.join([COPR_ROOT, MONITOR_URL.format(
            user=user, project=project)]))
    data = rsp.json()

    if rsp.status_code == 200:
        return data
    else:
        raise ProjectNotFoundError(data['error'])


def builds(user: str, project: str) -> None:
    """Generate build URLs for the specified project."""

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
