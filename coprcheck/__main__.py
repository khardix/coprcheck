"""Coprcheck -- automated tests on COPR projects

Usage:
    {prog} [options] PROJECT

Positional arguments:
    PROJECT             The COPR project to check, in the format of <user>/<project>

Options:
    -t, --target=TARGET Directory to store the downloaded packages [default: <user>-<project>]
    -q, --quiet         Silences progress reporting to console
    -r, --report=REPORT Specify the file to output to [default: <user>-<project>.yml]

Phases options:
    --no-download       Do not download the package, use existing contents of TARGET
    --no-checks         Do not run checks on the TARGET
"""


import sys

import docopt
import yaml
from tqdm import tqdm

from . _utils.output import *
from . apiscan import current_builds
from . fetch import fetch_build
from . checks import rpmgrill


def valid_copr_project(name: str) -> (str, str):
    """Validate COPR project name, as user/project.

    Raises:
        ValueError if the project name is not valid.
    """

    parts = name.split('/')
    if len(parts) != 2:
        msg = 'Invalid project: {}'.format(name)
        raise ValueError(msg)
    else:
        return tuple(parts)


params = docopt.docopt(__doc__.format(prog=__package__))

# Validate project
try:
    user, project = valid_copr_project(params['PROJECT'])
except ValueError as err:
    raise SystemExit(str(err)) from None

# Construct defaults
if params['--target'] is None:
    params['--target'] = '-'.join((user, project))
if params['--report'] is None:
    params['--report'] = ''.join((user, '-', project, '.yml'))

if not params['--no-download']:
    builds = list(current_builds(user, project))

    if not params['--quiet']:
        builds = tqdm(builds)

    for url in builds:
        fetch_build(url, params['--target'])

if not params['--no-checks']:
    full_results = dict()

    try:
        with running_task('rpmgrill'):
            result = rpmgrill.scan(params['--target'])
            for pkg, checks in result.items():
                pkg = full_results.setdefault(pkg, dict())
                checks = {
                    check: [': '.join(it) for it in state.items()]
                    for check, state in checks.items()
                }

                pkg['rpmgrill'] = checks
    finally:
        pass

    if not params['--quiet']:
        report_failed(full_results)

    # print report
    with open(params['--report'], 'w') as report:
        print(yaml.dump(full_results, default_flow_style=False), file=report)
