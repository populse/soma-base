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
This module contains functions and classes related to sqlite databases.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import absolute_import
__docformat__ = "epytext en"


import sys
import threading
import sqlite3

#------------------------------------------------------------------------------
class ThreadSafeSQLiteConnection( object ):
  '''
  Python wrapping of SQLite do not allow sharing of database connection between
  threads. This class allows to automatically create a connection for each
  thread.
  '''
  _currentId = 0
  _classLock = threading.RLock()
    
  def __init__( self, *args, **kwargs ):
    super( ThreadSafeSQLiteConnection, self ).__init__()
    self.__args = args
    self.__kwargs = kwargs
    self._instanceLock = threading.RLock()
    self.connections = {}
    self._classLock.acquire()
    try:
      self._id = ThreadSafeSQLiteConnection._currentId
      ThreadSafeSQLiteConnection._currentId += 1
    finally:
      self._classLock.release()

  def __del__( self ):
    if threading is None:
      # The interpretor is exiting and we cannot access threading
      # module. We cannot do anything.
      return
    if self.__args is not None:
      sqliteFile = self.__args[ 0 ]
      self.close()
      for thread in self.connections.keys():
        connection, connectionClosed = self.connections[ thread ]
        if connection is not None:
          currentThread = threading.currentThread().getName()
          print >> sys.stderr, 'WARNING: internal error: an sqlite connection on', repr( sqliteFile ), 'is opened for thread', thread, 'but the corresponding ThreadSafeSQLiteConnection instance (number ' + str( self._id ) + ') is being deleted in thread', currentThread + '. Method currentThreadCleanup() should have been called from', thread, 'to supress this warning.'
  
  def _getConnection( self ):
    if self.__args is None:
      raise RuntimeError( 'Attempt to access to a closed ThreadSafeSQLiteConnection' )
    currentThread = threading.currentThread().getName()
    #print '!ThreadSafeSQLiteConnection:' + currentThread + '! _getConnection( id =', self._id, ')', self.__args
    self._instanceLock.acquire()
    try:
      #currentThreadConnections = self.connections.setdefault( currentThread, {} )
      #print '!ThreadSafeSQLiteConnection:' + currentThread + '! currentThreadConnections =', currentThreadConnections
      connection, connectionClosed = self.connections.get( currentThread, ( None, True ) )
      if connectionClosed:
        if connection is not None:
          connection.close()
        connection = sqlite3.connect( *self.__args, **self.__kwargs )
        #print '!ThreadSafeSQLiteConnection:' + currentThread + '! opened', connection
        self.connections[ currentThread ] = ( connection, False )
    finally:
        self._instanceLock.release()
    return connection
  
  
  def currentThreadCleanup( self ):
    currentThread = threading.currentThread().getName()
    self._instanceLock.acquire()
    try:
      connection, connectionClosed = self.connections.pop( currentThread, ( None, True ) )
    finally:
      self._instanceLock.release()
    if connection is not None:
        connection.close()
  
  
  def close( self ):
    if self.__args is not None:
      self.closeSqliteConnections()
      self.__args = None
      self.__kwargs = None


  def closeSqliteConnections( self ):
    if self.__args is not None:
      self.currentThreadCleanup()
      currentThread = threading.currentThread().getName()
      self._instanceLock.acquire()
      try:
        for thread in self.connections.keys():
          connection, connectionClosed = self.connections[ thread ]
          self.connections[ thread ] = ( connection, True )
      finally:
        self._instanceLock.release()

