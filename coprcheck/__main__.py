import argparse
from os.path import expanduser

import tqdm

from . import apiscan
from .fetch import fetch_build


def copr_project(full_project: str):
    """Validate and parse COPR project name."""
    parts = full_project.split('/')
    if len(parts) != 2:
        msg = 'Invalid project: {}'.format(full_project)
        raise argparse.ArgumentTypeError(msg)
    return tuple(parts)


parser = argparse.ArgumentParser(prog='coprcheck',
                                 description='Download current builds from COPR project.')
parser.add_argument('-t', '--target', dest='target', default='.',
                    help='Directory to save the results to. Deafults to CWD.')
parser.add_argument('project', type=copr_project,
                    help='COPR project (format: user/project)')

args = parser.parse_args()

res = []
for url in tqdm.tqdm(list(apiscan.builds(*args.project))):
    #fetch_build(url, args.target)
    res.append(url)

print(*res, sep='\n')
