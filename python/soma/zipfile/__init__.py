# -*- coding: utf-8 -*-
# modified zipfile module in brainvisa project to switch between the regular
# python zipfile and a copy of the one from python 2.6 when version < 2.6

from __future__ import absolute_import
import sys
ver = sys.version_info[0] * 0x100 + sys.version_info[1]
if ver >= 0x0206:
    from zipfile import *
else:
    from soma.zipfile import *
