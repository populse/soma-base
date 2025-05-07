"""Config module that sets up version variable and finds the
`BrainVISA <https://brainvisa.info>`_ `brainvisa-share` data directory.

Attributes
----------
fullVersion
shortVersion
full_version
short_version
BRAINVISA_SHARE
"""

import os
from pathlib import Path

import soma

full_version = soma.__version__
short_version = ".".join(full_version.split(".")[:2])

fullVersion = full_version
shortVersion = short_version


def path_up(path, n=1):
    ''' Move up n directories
    (in other words, apply dirname the given number of times)
    '''
    for i in range(n):
        path = os.path.dirname(path)
    return path


def _init_default_brainvisa_share():
    try:
        import brainvisa_share.config

        bv_share_dir = brainvisa_share.config.share
        has_config = True
    except ImportError:
        bv_share_dir = f"brainvisa-share-{short_version}"
        has_config = False

    if bv_share_dir and os.path.exists(bv_share_dir):
        return bv_share_dir

    share = os.getenv("BRAINVISA_SHARE")
    if share:
        # share is the base share/ directory: we must find the brainvisa-share
        # directory in it.
        share = os.path.join(share, bv_share_dir)
    if not share or not os.path.exists(share):
        if 'CONDA_PREFIX' in os.environ:
            share = os.path.join(
                os.environ['CONDA_PREFIX'],
                'share', bv_share_dir)
            if not os.path.exists(share):
                # build dir config, we are in
                # <root>/lib/pythonx.x/site_packages/soma/config.py
                share = os.path.join(path_up(__file__, 5), 'share',
                                     bv_share_dir)
        if (not share or not os.path.exists(share)) and has_config:
            share = os.path.join(os.path.dirname(os.path.dirname(
                os.path.dirname(
                    brainvisa_share.config.__file__))), 'share',
                    brainvisa_share.config.share)
        if not share or not os.path.exists(share):
            share = os.path.join(path_up(__file__, 3), 'share', bv_share_dir)
    return share


def find_soma_root_dir():
    """Return the path of the base directory where software is installed. In a
    development environment this corresponds to the build directory. In
    user environments this corresponds to the install directory (which is
    $CONDA_PREFIX in the case of a Conda, Mamba or Pixi environment)
    """
    soma_root_dir = os.environ.get("SOMA_ROOT")
    if not soma_root_dir:
        soma_root_dir = os.environ.get("CASA_BUILD")
        if not soma_root_dir:
            soma_root_dir = os.environ.get("CONDA_PREFIX")
            if not soma_root_dir:
                soma_root_dir = Path(__file__).parent
                for i in range(3):
                    soma_root_dir = soma_root_dir.parent
                    if soma_root_dir.name in ("lib", "src"):
                        soma_root_dir = soma_root_dir.parent
                        return str(soma_root_dir)
    return soma_root_dir


BRAINVISA_SHARE = _init_default_brainvisa_share()
soma_root_dir = find_soma_root_dir()
