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

__docformat__ = "epytext en"


import os, sys, platform
from soma.singleton import Singleton
from soma.signature.api import HasSignature, Signature, VariableSignature,\
                                    Unicode, Number, Integer, Boolean, FileName
from soma.uuid import Uuid
from soma.minf.api import readMinf, minfFormat
from soma.translation import translate as _
from soma.notification import Notifier
from soma.wip.application.plugins import Plugins
from soma.wip.configuration import Configuration

#-------------------------------------------------------------------------------
class Application( Singleton, HasSignature ):
  class Directories( HasSignature ):
    signature = VariableSignature(
      'user', FileName,
      'site', FileName,
      'application', FileName,
    )
    
    def __init__( self, **kwargs ):
      HasSignature.__init__( self )
      self.initializeSignatureAttributes( **kwargs )
  
  
  def __singleton_init__( self, name, version, **kwargs ):
    HasSignature.__init__( self )
    self.signature = VariableSignature(
      'directories', Application.Directories,
      'verbose', Integer( minimum=0 ), dict( defaultValue=0 ),
      'configuration', Configuration,
    )
    self.name = name
    self.version = version
    self.uuid = Uuid()
    
    homedir = os.getenv( 'HOME' )
    if not homedir:
      homedir = ''
      if platform.system() == 'Windows':
        homedir = os.getenv( 'USERPROFILE' )
        if not homedir:
          homedir = os.getenv( 'HOMEPATH' )
          if not homedir:
            homedir = '\\'
          drive = os.getenv( 'HOMEDRIVE' )
          if not drive:
            drive = os.getenv( 'SystemDrive' )
            if not drive:
              drive = os.getenv( 'SystemRoot' )
              if not drive:
                drive = os.getenv( 'windir' )
              if drive and len( drive ) >= 2:
                drive = drive[ :2 ]
              else:
                drive = ''
          homedir = drive + homedir
    
    self.directories = Application.Directories(
      user = os.path.join( homedir, '.' + name ),
      site = '/etc/' + name,
      application = os.path.join( os.path.dirname( sys.argv[0] ), '..' ),
    )
    self.configuration = Configuration()
    self.plugins = Plugins()
  
  
  #: This notifier is notified once at the begining of application
  #: initialization
  onInitialization = Notifier( 0 )
  
  def initialize( self, args=() ):
    Application.onInitialization.notify()
    del Application.onInitialization
    i = 0
    while i < len( args ):
      parameter = args[ i ]
      i += 1
      if not parameter.startswith( '--' ):
        raise ValueError( _( 'Invalid parameter: %s' ) % parameter )
      attributes = parameter[ 2: ].split( '.' )
      object = self
      for attribute in attributes[ :-1 ]:
        object = getattr( object, attribute )
      attribute = attributes[ -1 ]
      dataType = object.signature[ attribute ].type
      values = []
      while i < len( args ) and not args[ i ].startswith( '--' ):
        values.append( args[ i ] )
        i += 1
      if not values:
        if isinstance( dataType, Integer ):
          setattr( object, attribute, getattr( object, attribute, 0 ) + 1 )
        elif isinstance( dataType, Boolean ):
          setattr( object, attribute, True )
        else:
          raise ValueError( _( 'Value missing for %s' ) % parameter )
      elif len( values ) == 1:
        if isinstance( dataType, ( Unicode, Number, Boolean, ) ):
          setattr( object, attribute, dataType.convertAttribute( object, attribute, values[ 0 ] ) )
        else:
          setattr( object, attribute, dataType.convertAttribute( object, attribute, values ) )
      else:
        setattr( object, attribute, dataType.convertAttribute( object, attribute, values ) )
    
    self.plugins.initialize()
