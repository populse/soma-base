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


# backward compatibility with older Python versions
import __builtin__
if not hasattr( __builtin__, 'set' ):
  from sets import Set as set

from soma.translation import translate as _
import os, threading, atexit, warnings, stat, platform
from soma.wip.application.api import Application
from soma.signature.api import Unicode


#----------------------------------------------------------------------------
class TemporaryFileManager:

  __removePermissions = stat.S_IWRITE + stat.S_IREAD
  
  
  class __SelfDestroyFileName( str ):
    def __new__( cls, value, manager ):
      '''
      This operator must be overloaded because C{str.__new__} accept only one 
      parameter but our class will be build with two parameters (see 
      L{__init__}).
      '''
      return str.__new__( cls, value )
    
    
    def __init__( self, fileName, manager ):
      self.data = fileName
      self.__manager = manager
    
    def __del__( self ):
      if self.data:
        if self.__manager is not None:
          self.__manager.removePath( self.data, raiseException=False )
        elif os.path.exists( self.data ):
          warnings.warn( _('temorary path %(path)s not deleted: %(error)s')%\
            { 'path': path, 
              'error': _('file not controled by a TemporaryFileManager' ) } )


  def __init__( self, directory, defaultPrefix ):
    self.__directory = directory
    self.__defaultPrefix = defaultPrefix
    self.__pathsToDelete = set()
    self.__lock = threading.RLock()
    self.__identifier = str( os.getpid() )
    self.__count = 0
    atexit.register( self.close )
    
    
  def registerPath( self, path ):
    self.__lock.acquire()
    try:
      self.__pathsToDelete.add( str( path ) )
    finally:
      self.__lock.release()


  def removePath( self, path, raiseException=True ):
    if self.__lock is None: return
    self.__lock.acquire()
    try:
      self.__pathsToDelete.discard( path )
      link = os.path.islink( path )
      if os.path.exists( path ) or link:
        error = None
        if not link and os.path.isdir( path ):
          for f in os.listdir( path ):
            self.removePath( os.path.join( path, f ), 
                             raiseException = raiseException )
          try:
            os.rmdir( path )
          except OSError:
            # try changing permissions
            os.chmod( path, self.__removePermissions )
            try:
              os.rmdir( path )
            except OSError, error:
              if raiseException: raise
        else:
          try:
            os.remove( path )
          except OSError:
            # try changing permissions
            try:
              os.chmod( path, self.__removePermissions )
              os.remove( path )
            except OSError, error:
              if raiseException: raise
        if error is not None:
          warnings.warn( _('temorary path %(path)s not deleted: %(error)s')%\
            { 'path': path, 'error': unicode( error ) } )
    finally:
      self.__lock.release()


  def __del__( self ):
    self.close()
  
  
  def close( self ):
    if self.__lock is None: return
    self.__lock.acquire()
    try:
      for f in list(self.__pathsToDelete):
        self.removePath( f, raiseException=False )
      self.__pathsToDelete.clear()
    finally:
      self.__lock.release()
      self.__lock = None
    
  
  def newFileName( self, suffix=None, prefix=None, directory=None ):
    if directory is None:
      directory = self.__directory
    if suffix is None:
      suffix = ''
    if prefix is None:
      prefix = self.__defaultPrefix
    self.__lock.acquire()
    try:
      result = os.path.join( directory,
                   prefix + '_' +self.__identifier + '_' + str( self.__count ) + suffix )
      self.__count += 1
    finally:
      self.__lock.release()
    return result


  def createSelfDestroyed( self, path ):
    result = self.__SelfDestroyFileName( path, self )
    self.registerPath( result )
    return result
    
    
  def new( self, suffix=None, prefix=None, directory=None ):
    path = self.newFileName( suffix=suffix, prefix=prefix, directory=directory )
    return self.createSelfDestroyed( path )
  
  
  def setDefaultTemporaryDirectory( self, path ):
    self.__directory = path
   
   
  def defaultTemporaryDirectory( self, path ):
    return self.__directory
    
  
  def isTemporary( self, path ):
    return isinstance( self.__SelfDestroyFileName, path )




#----------------------------------------------------------------------------
                                 
def getSystemDefaultTempDir():
  if platform.system() == 'Windows':
    defaultTemporary = os.getenv( 'TEMP' )
    if not defaultTemporary:
      defaultTemporary = os.getenv( 'TMP' )
      if not defaultTemporary:
        defaultTemporary = 'C:\\WINDOWS\\TEMP'
  else:
    defaultTemporary = '/tmp'
  
  return defaultTemporary

def initializeTemporaryFiles():
  application = Application()
  if application.verbose:
    print 'Initializing temporary files'
  defaultTemporary = getSystemDefaultTempDir()
  manager = TemporaryFileManager( defaultTemporary, 
                                  defaultPrefix = str( application.uuid ) )
  application.directories.signature.append( 'temporary', Unicode,
                                defaultValue = defaultTemporary,
                                doc='Directory where temporary files are put.' )
  application.temporary = manager
  application.onAttributeChange( 'temporary_directory', 
                                 manager.setDefaultTemporaryDirectory )

#----------------------------------------------------------------------------
Application.onInitialization.add( initializeTemporaryFiles )


