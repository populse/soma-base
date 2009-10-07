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
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''


import sys, os, qt

from brainvisa.configuration import *



#------------------------------------------------------------------------------
#if len( sys.argv ) > 1 and os.path.exists( sys.argv[1] ):
  #configuration.load( sys.argv[ 1 ] )

#------------------------------------------------------------------------------
qApp = qt.QApplication( sys.argv )
appGUI = ApplicationQt3GUI()
#qtgui = appGUI.instanceQt3GUI( configuration )
#widget = qtgui.editionWidget( configuration )
#widget.show()
#qApp.processEvents()
#widget.resize( widget.sizeHint() )
#qApp.setMainWidget( widget )

#qApp.exec_loop()
#qtgui.setObject( widget, configuration )

#------------------------------------------------------------------------------
readBrainVISA3_0Configuration( os.path.join( os.environ[ 'HOME' ], '.brainvisa', 'options.py' ), configuration )


#------------------------------------------------------------------------------
appGUI.edit( configuration )

#------------------------------------------------------------------------------
configuration.save( sys.stdout )
