# -*- coding: iso-8859-1 -*-

# Copyright IFR 49 (1995-2009)
#
#  This software and supporting documentation were developed by
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
Toolboxes to create
U{Turbogears<http://turbogears.org/>} widgets.

This module gather together several public items defined in various submodules:
  - From L{soma.gui.base}:
    - L{ApplicationBaseGUI}
  - From L{soma.tggui.automatic}:
    - L{ApplicationTgGUI}
    - L{TgGUI}
    - L{TgWindowManager}
    - L{TgWindow}
  - Other items:
    - L{TgRemoteForm}
    - L{TgTextField}
    - L{TgCheckBox}
    - L{TgSingleSelectField}
    - L{TgFieldSet}
@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

#: Default size for icons
defaultIconSize = ( 16, 16 )
largeIconSize = ( 22, 22 )

from soma.gui.base                            import ApplicationBaseGUI
from soma.tggui.automatic                     import ApplicationTgGUI, TgGUI, TgWindowsManager, TgWindow
from soma.tggui.standard_widgets              import TgRemoteForm, TgTextField, TgCheckBox, TgSingleSelectField, TgFieldSet, TgExtendedApplet, TgUploadMultipleFiles

#from soma.tggui.timered_widgets import QLineEditModificationTimer, TimeredQLineEdit
#from soma.tggui.vscrollframe import VScrollFrame
#from soma.tggui.list_tree_widgets import ObservableListWidget, EditableTreeWidget, TreeListWidget
#from soma.tggui.qt3thread import QtThreadCall, FakeQtThreadCall
#from soma.tggui.file_dialog import QFileDialogWithSignals
#from soma.tggui.icons import getPixmap
#from soma.tggui.text import TextEditWithSearch, TextBrowserWithSearch
