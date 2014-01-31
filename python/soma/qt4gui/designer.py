# -*- coding: utf-8 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
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
# knowledge of the CeCILL license version 2 and that you accept its terms.

'''
Facilitation of run-time creation and usage of C{Qt} widgets from C{*.ui} 
files created with 
U{Qt designer<http://doc.trolltech.com/designer-manual.html>}.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"


import os
from functools import partial
from PyQt4 import QtGui, QtCore
use_pyside = False
try:
  from PyQt4 import uic
  from PyQt4.uic.Loader import loader
  from PyQt4.uic import loadUiType
except: # maybe PySide
  from PyQt4.QtUiTools import QUiLoader
  use_pyside = True

def _iconset(self, prop):
  return QtGui.QIcon( os.path.join( self._basedirectory, prop.text ).replace("\\", "\\\\") )
def _pixmap(self, prop):
  return QtGui.QPixmap(os.path.join( self._basedirectory, prop.text ).replace("\\", "\\\\"))


def loadUi( ui, *args, **kwargs ):
  '''
  This function is a replacement of PyQt4.uic.loadUi. The only difference is 
  that relative icon or pixmap file names that are stored in the *.ui file 
  are considered to be relative to the directory containing the ui file. With
  PyQt4.uic.loadUi, relative file names are considered relative to the current
  working directory therefore if this directory is not the one containing the 
  ui file, icons cannot be loaded.
  '''
  if not use_pyside:
    # the problem is corrected in version > 4.7.2,
    # anyway there is no ui files containing relative icons or pixmaps in brainvisa
    if QtCore.PYQT_VERSION > 0x040702:
      return uic.loadUi(ui, *args, **kwargs)
    else:
      uiLoader = loader.DynamicUILoader()
      uiLoader.wprops._basedirectory = os.path.dirname( os.path.abspath( ui ) )
      uiLoader.wprops._iconset = partial( _iconset, uiLoader.wprops )
      uiLoader.wprops._pixmap = partial( _pixmap, uiLoader.wprops )
      return uiLoader.loadUi( ui, *args, **kwargs )
  else:
    return QUiLoader().load( ui ) #, *args, **kwargs )


def loadUiType( uifile, from_imports=False ):
  if not use_pyside:
    return uic.loadUiType( uifile ) # the parameter from_imports doesn't exist in our version of PyQt
  else:
    raise NotImplementedError( 'loadUiType does not work with PySide' )
    #ui = loadUi( uifile )
    #return ui.__class__, QtGui.QWidget # FIXME

