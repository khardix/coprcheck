import argparse
from functools import partial
from os.path import expanduser
from pprint import pprint
from sys import stderr
from subprocess import CalledProcessError

import tqdm

from . import apiscan
from .fetch import fetch_build
from .checks import rpmgrill


def copr_project(full_project: str):
    """Validate and parse COPR project name."""
    parts = full_project.split('/')
    if len(parts) != 2:
        msg = 'Invalid project: {}'.format(full_project)
        raise argparse.ArgumentTypeError(msg)
    return tuple(parts)


logprint = partial(print, file=stderr, flush=True)


parser = argparse.ArgumentParser(prog='coprcheck',
                                 description='Download current builds from COPR project.')
parser.add_argument('-t', '--target', dest='target', default='.',
                    help='Directory to save the results to. Deafults to CWD.')
parser.add_argument('project', type=copr_project,
                    help='COPR project (format: user/project)')

args = parser.parse_args()

#builds = list(apiscan.current_builds(*args.project))
#for build in tqdm.tqdm(builds):
    #fetch_build(build, args.target)
logprint('[CHECK] Running rpmgrill…', end='\t')
grill_stats = None
try:
    grill_stats = rpmgrill.scan(args.target)
except CalledProcessError as cmdfail:
    logprint('[FAIL]: {0}'.format(cmdfail.output))
else:
    logprint('[DONE]')

if grill_stats:
    print("Failed packages:")
    for pkg, checks in grill_stats.items():
        print('\t{}:'.format(pkg))
        for check, details in checks.items():
            print('\t\t{}:'.format(check))
            for code, diag in details.items():
                print('\t\t\t{}: {}'.format(code, diag))
