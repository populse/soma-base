# -*- coding: utf-8 -*-
# modified zipfile module in brainvisa project to switch between the regular
# python zipfile and a copy of the one from python 2.6 when version < 2.6

import sys, os
ver = sys.version_info[0] * 0x100 + sys.version_info[1]
if ver >= 0x0206:
  import imp
  f, pathname, description = imp.find_module( 'zipfile',
    [ os.path.dirname( os.__file__ ) ] )
  try:
    zipfile = imp.load_module( 'zipfile', f, pathname, description )
    globals().update( zipfile.__dict__ )
  finally:
    f.close()
    del f, pathname, description, imp
else:
  from zipfile import *
del zipfile, ver, sys, os

