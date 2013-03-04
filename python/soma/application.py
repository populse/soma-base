# -*- coding: utf-8 -*-

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

from __future__ import absolute_import
__docformat__ = "epytext en"


import os, sys, platform, traceback
from os.path import dirname

os.environ['ETS_TOOLKIT'] = 'qt4'
try:
  from enthought.traits.api import ReadOnly, Directory, ListStr, Instance
except ImportError:
  from traits.api import ReadOnly, Directory, ListStr, Instance

from soma.singleton import Singleton
from soma.controller import Controller, ControllerFactories


#-------------------------------------------------------------------------------
class Application( Singleton, Controller ):
  '''Any program using soma should create an Application instance to manage
  its configuration and to store any kind of value that have to be global to
  the program.'''
  name = ReadOnly( desc='Name of the application' )
  version = ReadOnly()
  
  install_directory = Directory( 
    desc='Base directory where the application is installed' )
  user_directory = Directory( 
    desc='Base directory where user specific information can be find' )
  application_directory = Directory(
    desc='Base directory where application specifc information can be find' )
  site_directory = Directory( 
    desc='Base directory where site specifc information can be find' )
  #early_plugin_modules = ListStr( 
    #desc='List of Python module to load before application configuration' )
  plugin_modules = ListStr(
    desc='List of Python module to load after application configuration' )

  def __singleton_init__( self, name, version=None, *args, **kwargs ):
    '''Replaces __init__ in Singleton.'''
    super( Application, self ).__init__( *args, **kwargs )
    
    self._controller_factories = None
    
    self.name = name
    self.version = version
    self.gui = None
    self.loaded_plugin_modules = {}
    

  def initialize( self ):
    '''This method must be called once to setup the application.'''
    self.install_directory = dirname( dirname( dirname( __file__ ) ) )
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
    if homedir and os.path.exists( homedir ):
      self.user_directory = homedir
    
    # Load early plugin modules
    for plugin_module in self.plugin_modules:
      module = self.load_plugin_module( plugin_module )
      if module is not None:
        self.loaded_plugin_modules[ plugin_module ] = module
        init = getattr( module, 'call_before_application_initialization', None )
        if init is not None:
          init( self )
        
    appdir = os.path.normpath( os.path.dirname( os.path.dirname( sys.argv[0] ) ) )
    if os.path.exists( appdir ):
      self.application_directory = appdir

    sitedir = os.path.join( '/etc', self.name )
    if os.path.exists( sitedir ):
      self.site_directory = sitedir

    # Load plugin modules
    for plugin_module in self.plugin_modules:
      module = self.loaded_plugin_modules.get( plugin_module )
      if module is None:
        module = self.load_plugin_module( plugin_module )
      if module is not None:
        self.loaded_plugin_modules[ plugin_module ] = module
        init = getattr( module, 'call_after_application_initialization', None )
        if init is not None:
          init( self )


  def initialize_gui( self ):
    '''If the application is using a graphical user interface (GUI), this
    method must be called to initialize it.'''
    if self.gui is None:
      from soma.gui.application_gui import ApplicationGUI
      self.gui = ApplicationGUI( self )
  
  
  def get_controller( self, something ):
    '''This method must be used to get a controller for any object.'''
    if self._controller_factories is None:
      self._controller_factories = ControllerFactories()
    return self._controller_factories.get_controller( something )
  
  
  @staticmethod
  def load_plugin_module( plugin_module ):
    '''This method loads a plugin module. It imports the module without raising
    an axception if it fails.'''
    try:
      __import__( plugin_module, level=0 )
      return sys.modules[ plugin_module ]
    except:
      traceback.print_last()
    return None