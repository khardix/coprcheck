"""Main CLI interface of the coprcheck package."""


import argparse
from contextlib import contextmanager
from functools import partial
from os.path import expanduser
import sys
from subprocess import CalledProcessError

from blessings import Terminal
import tqdm

from . apiscan import current_builds
from . fetch import fetch_build
from . checks import rpmgrill


term = Terminal()

print_progress = partial(print, file=sys.stderr, flush=True)

def copr_project(full_project: str):
    """Validate and parse COPR project name."""

    parts = full_project.split('/')
    if len(parts) != 2:
        msg = 'Invalid project: {}'.format(full_project)
        raise argparse.ArgumentTypeError(msg)
    return tuple(parts)

@contextmanager
def running_task(name: str):
    """Report that the task is running and if it was successfull."""

    print_progress('Running {}...'.format(name), end='')
    try:
        yield
    except Exception:
        print_progress('[{}]'.format(term.bold_red('FAIL')))
        raise
    else:
        print_progress('[{}]'.format(term.green('DONE')))


argparser = argparse.ArgumentParser(
        description='Check COPR repository for package quality',
        )
argparser.add_argument('project',
        metavar='USER/PROJECT',
        type=copr_project,
        help='Full project name',
        )
argparser.add_argument('-t', '--target',
        help='Directory in which the downloaded packages will be stored. '
            +'Defaults to $PWD/USER-PROJECT.',
        )

outputs = argparser.add_mutually_exclusive_group()
outputs.add_argument('-q', '--quiet',
        dest='report_progress',
        action='store_false',
        help='Silences progess output to console.',
        )
outputs.add_argument('--no-logs',
        dest='write_logs',
        action='store_false',
        help='Do not write progress report.',
        )

phases = argparser.add_mutually_exclusive_group()
phases.add_argument('--no-download',
        dest='download',
        action='store_false',
        help='Do not download packages, use the contents of the target.'
        )
phases.add_argument('--no-checks',
        dest='check',
        action='store_false',
        help='Do not run checks on downloaded packages.'
        )


parameters = argparser.parse_args()
if parameters.target is None:
    parameters.target = '-'.join(parameters.project)

if parameters.download:
    builds = list(current_builds(*parameters.project))
    if parameters.report_progress:
        builds = tqdm.tqdm(builds)
    for url in builds:
        fetch_build(url, parameters.target)

if parameters.check:
    checks_results = dict()

    try:
        with running_task('rpmgrill'):
            checks_results['rpmgrill'] = rpmgrill.scan(parameters.target)
    except CalledProcessError as exc:
        raise SystemExit(0xFF)

    if parameters.report_progress:

        print('Failed packages:')
        for package, results in checks_results['rpmgrill'].items():
            print('\t{}:'.format(term.bold_white(package)))
            for check, state in results.items():
                print('\t\t{}:'.format(term.yellow(check)))
                for code, diag in state.items():
                    print('\t\t\t{}: {}'.format(code, diag))
