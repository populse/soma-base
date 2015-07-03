
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
    except ImportError:
        bv_share_dir = "brainvisa-share"

    share = os.getenv('BRAINVISA_SHARE')
    if not share or not os.path.exists(share):
        share = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname( \
            brainvisa_share.config.__file__))), 'share',
            brainvisa_share.config.share)
    return share

BRAINVISA_SHARE = _init_default_brainvisa_share()
