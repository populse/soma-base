# -*- coding: utf-8 -*-

""" Config module that sets up version variable and finds the
`BrainVISA <http://brainvisa.info>`_ `brainvisa-share` data directory.

Attributes
----------
fullVersion
shortVersion
full_version
short_version
BRAINVISA_SHARE
"""

from __future__ import absolute_import
import os
import sys
import soma.info

full_version = ".".join([str(soma.info.version_major),
                        str(soma.info.version_minor),
                        str(soma.info.version_micro)])
short_version = ".".join([str(soma.info.version_major),
                         str(soma.info.version_minor)])

fullVersion = full_version
shortVersion = short_version


def _init_default_brainvisa_share():
    try:
        import brainvisa_share.config
        bv_share_dir = brainvisa_share.config.share
        has_config = True
    except ImportError:
        bv_share_dir = "brainvisa-share-%s" % short_version
        has_config = False

    if bv_share_dir and os.path.exists(bv_share_dir):
        return bv_share_dir

    share = os.getenv('BRAINVISA_SHARE')
    if share:
        # share is the base share/ directory: we must find the brainvisa-share
        # directory in it.
        share = os.path.join(share, bv_share_dir)
    if not share or not os.path.exists(share):
        if has_config:
            share = os.path.join(os.path.dirname(os.path.dirname(
                os.path.dirname(
                    brainvisa_share.config.__file__))), 'share',
                    brainvisa_share.config.share)
        else:
            share = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'share', bv_share_dir)  # cannot do better.
    return share

BRAINVISA_SHARE = _init_default_brainvisa_share()
