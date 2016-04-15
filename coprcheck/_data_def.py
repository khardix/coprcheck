"""Definitions of data types used accross the module."""


from collections import namedtuple
import re


class Chroot(namedtuple('Chroot', ['distro', 'version', 'arch'])):
    """Build chroot information."""

    CHROOT_RE = re.compile('^(?P<distro>.+)-(?P<version>[^-]+)-(?P<arch>[^-]+)$')

    @classmethod
    def from_chroot_name(cls, name: str):
        """Parse chroot name."""

        m = re.match(cls.CHROOT_RE, name)
        if m is None: raise ValueError('Invalid chroot: ' + name)

        return cls(**m.groupdict())

    @property
    def distribution(self):
        """Full distribution name."""
        return '-'.join([self.distro, self.version])

    def __str__(self):
        """Full chroot name."""
        return '-'.join([self.distro, self.version, self.arch])


BuildResult = namedtuple('BuildResult', ['build_id', 'chroot', 'url'])
BuildResult.__doc__ += ': Container for COPR build result info.'
# For 3.5+
#BuildResult.build_id.__doc__ = 'Build id.'
#BuildResult.chroot.__doc__ = 'Chroot in which the build was made.'
#BuildResult.url.__doc__ = 'Absolute URL of the resulting artifacts.'
