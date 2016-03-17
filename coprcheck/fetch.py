"""Download requested COPR builds."""


import asyncio
from os import path
import subprocess
from urllib.parse import urlparse

import tqdm


def _wget_dir(remote_dir: str, local_root: str,
              accept: [str] = ['rpm', 'log.gz']) -> None:
    """Download contents of the remote directory to the local root.

    The last segment od the remote_dir is recreated in local_root
    and its contents are saved in it. It is therefore safe to
    use this call to download multiple directories in the same
    local_root without mixing their contents.

    Args:
        remote_dir: Full URL to the downloaded directory.
        local_root: Directory to which the results should be saved.
        accept: List of accepted extensions
    """

    remote_path = urlparse(remote_dir).path
    *tree, target = filter(None, remote_path.split('/'))

    cmd = ['wget']
    # Command output
    cmd += ['--quiet']
    # File output
    cmd += ['--no-host-directories', '--cut-dirs={l}'.format(l=len(tree))]
    cmd += ["--directory-prefix={}".format(path.expanduser(local_root))]
    # Downloading options
    cmd += ['--recursive', '--no-parent', '--level=1']
    cmd += ["--accept=*.{ext}".format(ext=e) for e in accept]
    # Download source
    cmd += [remote_dir]

    subprocess.check_call(cmd)


#@asyncio.coroutine
def fetch_build(url: str, local_root: str) -> None:
    return _wget_dir(url, local_root)
