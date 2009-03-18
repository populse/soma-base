# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
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
@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''

__docformat__ = "epytext en"


import os, glob
from soma.wip.application.application import Application
from soma.path import split_path
import soma

#-------------------------------------------------------------------------------
#: Directory where soma icons files are stored
somaIconsDirectory = sorted( glob.glob( os.path.join( *( 
 split_path( soma.__file__ )[:-3] + [ 'share', 'soma-*', 'icons' ]) \
  ) ) )
if somaIconsDirectory:
  somaIconsDirectory = somaIconsDirectory[ 0 ]
else:
  somaIconsDirectory = ''


#-------------------------------------------------------------------------------
def findIconFile( fileName ):
  '''
  Find an icon file in user, application and site "icons" directories.
  Return C{None} if the file has not been found.
  '''
  app = Application("soma", "")
  for dir in ( app.directories.user, app.directories.application,
               app.directories.site, somaIconsDirectory ):
    file = os.path.join( dir, 'icons', fileName )
    if os.path.exists( file ):
      #print '!icon!', repr( fileName ), '-->', file
      return file
  if os.path.exists( fileName ):
    #print '!icon!', repr( fileName ), '-->', fileName
    return fileName
  #print '!icon!', repr( fileName ), '-->', None
  return None
