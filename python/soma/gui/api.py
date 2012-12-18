# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.

'''
This module contains functions and classes related to graphical interface
but independant of GUI backend (Qt3, Qt4, wxWidget, Tcl/TK, etc).

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
__docformat__ = "epytext en"
 

import sys

def choose_matplotlib_backend():
  '''
  Tries to identify running graphical interface an select the appropriate
  backend for Matplotlib. This function must be called after GUI is started.
  
  Currently only works with Qt4Agg and QtAgg
  
  Example::
    from soma.gui.api import chooseMatplotlibBackend
    chooseMatplotlibBackend()
  '''
  
  if sys.modules.has_key( 'PyQt4' ):
    runningGUIBackend = 'Qt4Agg'
  else:
    runningGUIBackend = 'QtAgg'
  
  import matplotlib
  if 'matplotlib.backends' not in sys.modules:
    matplotlib.use( runningGUIBackend )
  elif matplotlib.get_backend() != runningGUIBackend:
    raise RuntimeError( 'Mismatch between Qt version and matplotlib backend: '
      'matplotlib uses ' + matplotlib.get_backend() + ' but ' + runningGUIBackend + ' is required.' )
  return matplotlib.get_backend()

# For backward compatibility:
chooseMatplotlibBackend = choose_matplotlib_backend