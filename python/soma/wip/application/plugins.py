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

import os
from soma.minf.api import readMinf, minfFormat, writeMinf
from soma.signature.api import HasSignature, Signature, Unicode, Sequence, \
                               Boolean
from soma.translation import translate as _


#-------------------------------------------------------------------------------
class PluginDependency( HasSignature ):
  signature = Signature(
    'module', Unicode,
    'version', Unicode, dict( defaultValue = '' ),
  )
  
  def __init__( self, **kwargs ):
    super( PluginDependency, self ).__init__()
    self.initializeSignatureAttributes( **kwargs )


#-------------------------------------------------------------------------------
class Plugin( HasSignature ):
  signature = Signature(
    'pluginSystem', Unicode, dict( defaultValue = 'soma' ),
    'name', Unicode, dict( defaultValue = '<unnamed>' ),
    'version', Unicode, dict( defaultValue = None ),
    'module', Unicode, dict( defaultValue = None ),
    'dependencies', Sequence( PluginDependency ), dict( defaultValue = [] ),
    'auto_include', Boolean, dict( defaultValue = False ),
    'platforms', Sequence( Unicode ), dict( defaultValue = [] ),
  )
  
  def __init__( self, directory=None ):
    super( Plugin, self ).__init__( self )
    if directory is None:
      self.directory = None
    else:
      self.directory = os.path.abspath( os.path.normpath( directory ) )
      fileName = os.path.join( self.directory, 'plugininfo.minf' )
      readMinf( fileName, targets=(self,) )
      if self.pluginSystem != 'soma':
        raise TypeError( _( 'Cannot use %s plugins' ) % self.pluginSystem )
  
  
  def writeMinf( self, dest ):
    writeMinf( dest, ( self, ) )
  
  
  def isPlugin( directory ):
    fileName = os.path.join( directory, 'plugininfo.minf' )
    return os.path.exists( fileName ) and minfFormat( fileName ) is not None
  isPlugin = staticmethod( isPlugin )
  
  
  def isInitialized( self ):
    return sys.modules.get( self.module ) is None
  
  
  def initialize( self ):
    __import__( self.module )


#-------------------------------------------------------------------------------
class Plugins( object ):
  def __init__( self ):
    self._availablePlugins = {}
    self._includedPlugins = {}


  def includePlugin( self, pluginName, requiredVersion=None ):
    '''
    Make a plugin available for initialization and import.
    '''
    if isinstance( pluginName, Plugin ):
      plugin = pluginName
    elif os.path.isdir( pluginName ):
      plugin = Plugin( pluginName )
    else:
      plugin = self.findPlugin( pluginName, requiredVersion )
    if plugin.module not in self._includedPlugins:
      packages = plugin.module.split( '.' )
      __import__( '.'.join( packages[ : -1 ] ) )
      topLevelPackage = __import__( packages[ 0 ] )
      pluginsPackage = topLevelPackage
      for p in packages[ 1 : -1 ]:
        pluginsPackage = getattr( pluginsPackage, p )
      pluginsPackage.__path__.append( plugin.directory )
      self._includedPlugins[ plugin.module ] = plugin
      if Application().verbose > 1:
        print 'Included plugin', plugin.module, 'version', plugin.version, \
              'from', repr( plugin.directory )
      if plugin.dependencies:
        for d in plugin.dependencies:
          self.includePlugin( d.module, d.version )
    return plugin
  
  
  def findPlugin( self, pluginName, requiredVersion=None ):
    result = None
    plugin = self._includedPlugins.get( pluginName )
    if plugin is not None:
      if plugin.version != requiredVersion and requiredVersion is not None:
        raise ImportError( _( 'Plugin %(plugin)s already included with version '
          '%(version)' ) % dict( plugin=plugin.module,
                                 version=str(plugin.version) ) )
      result = plugin
    else:
      for plugin in self._availablePlugins.get( pluginName, () ):
        if plugin.version == requiredVersion or requiredVersion is None:
          result = plugin
          break
      if result is None:
        if requiredVersion is None:
          raise ImportError( _( 'Cannot find plugin %s' ) % pluginName )
        else:
          raise ImportError( _( 'Cannot find plugin %(plugin)s version '
                                '%(version)s' ) % dict( plugin=pluginName,
                                                      version=requiredVersion ))
    return result
  
  
  def initialize( self ):
    auto_include = []
    app = Application()
    for d in app.directories.user, app.directories.site, app.directories.application:
      pluginsDir = os.path.join( d, 'plugins' )
      if os.path.isdir( pluginsDir ):
        for n in os.listdir( pluginsDir ):
          pluginDir = os.path.join( pluginsDir, n )
          if Plugin.isPlugin( pluginDir ):
            plugin = Plugin( pluginDir )
            self._availablePlugins.setdefault( plugin.module, [] ).append( 
              plugin )
            if app.verbose > 2: 
              print 'Found plugin', plugin.module, 'version', plugin.version, \
                    'in', repr( pluginDir )
            if plugin.auto_include:
              auto_include.append( plugin )
    for plugin in auto_include:
      if app.verbose > 2: 
        print 'Automatic include for plugin', plugin.module, 'version', plugin.version
      self.includePlugin( plugin )

from soma.wip.application.application import Application
