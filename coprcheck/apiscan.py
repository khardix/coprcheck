"""COPR API data miner."""

"""Currently uses both versions of the API, since the newer one
does not provide monitor equivalent"""


import asyncio
import itertools as it

import aiohttp
from blessings import Terminal


COPR_ROOT = 'https://copr.fedorainfracloud.org'
MONITOR_URL = '/api/coprs/{user}/{project}/monitor'
BUILD_TASK_URL = '/api_2/build_tasks'

_SEMAPHORE = asyncio.Semaphore(5)


class ProjectNotFoundError(RuntimeError):
    """Indicate that the project was not found by the COPR web."""


@asyncio.coroutine
def monitor(user: str, project: str) -> dict:
    """Fetch monitor for the specified project."""

    url = (COPR_ROOT, MONITOR_URL.format(user=user, project=project))
    with (yield from _SEMAPHORE):
        rsp = yield from aiohttp.get(''.join(url))
    try:
        data = yield from rsp.json()

        if rsp.status == 200:
            return data
        else:
            raise ProjectNotFoundError(data['error'])
    finally:
        yield from rsp.release()


@asyncio.coroutine
def fetch_build_task(uid: int):
    url = (COPR_ROOT, BUILD_TASK_URL)
    with (yield from _SEMAPHORE):
        rsp = yield from aiohttp.get(''.join(url), params={'build_id': uid})
    try:
        data = yield from rsp.json()
        return data['build_tasks']
    finally:
        yield from rsp.release()


def builds(user: str, project: str) -> None:
    """Generate build URLs for the specified project."""

    loop = asyncio.get_event_loop()
    term = Terminal()
    tag = '[{}/{}]'.format(user, project)

    print(term.yellow('{} Fetching monitor…'.format(tag)), end=' ', flush=True)
    # Fetch and parse monitor
    packages = loop.run_until_complete(monitor(user, project))['packages']
    # link all builds from all packages into one iterable
    builds = it.chain.from_iterable(p['results'].values() for p in packages)
    uniq_ids = {b['build_id'] for b in builds
                              if b is not None and b['status'] == 'succeeded'}
    print(term.bold_green('OK'), flush=True)

    # Fetch URLs for all builds
    url = (COPR_ROOT, BUILD_TASK_URL)
    futures = [fetch_build_task(uid) for uid in uniq_ids]
    responses = asyncio.as_completed(futures)
    tasks = it.chain.from_iterable(loop.run_until_complete(r) for r in responses)
    yield from (task['build_task']['result_dir_url']
                for task in tasks if task['build_task']['state'] == 'succeeded')

if __name__ == '__main__':
    for url in builds('msuchy', 'copr-dev'): print(url)
