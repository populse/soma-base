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

"""
This module enables to make a function to be executed in qt thread (main thread). 
It is useful when you want to call qt functions from another thread.
It enables to do thread safe calls because all tasks sent are executed in the same thread (qt main thread).

@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
"""

import sys
import threading
from soma.qt_gui.qt_backend.QtCore import QObject, QTimer, QEvent, SIGNAL, QCoreApplication
from soma import singleton

class FakeQtThreadCall( QObject ):
  '''
  Fake L{QtThreadCall} that behave as if always used from main thread.
  '''
  def isInMainThread():
    return True
  isInMainThread = staticmethod( isInMainThread )
  
  
  def push( function, *args, **kwargs ):
    if kwargs is None or not kwargs:
      function( *args )
    else:
      function( *args, **kwargs )
  push = staticmethod( push )

  def call( function, *args, **kwargs ):
    if kwargs is None or not kwargs:
      return function( *args )
    else:
      return function( *args, **kwargs )
  call = staticmethod( call )



class QtThreadCall( singleton.Singleton, QObject ):
  """
  This object enables to send tasks to be executed by qt thread (main thread). 
  This object must be initialized in qt thread. 
  It starts a QTimer and periodically execute tasks in its actions list.
  
  @type lock: RLock
  @ivar lock: lock to prevent concurrent access to actions list
  @type actions: list
  @ivar actions: tasks to execute
  @type mainThread: Thread
  @ivar mainThread: current thread at object initialisation
  @type timer: QTimer
  @ivar timer: timer to wake this object periodically
  """
  def __singleton_init__( self ):
    # QObject.__init__( self, None )
    super( QtThreadCall, self ).__singleton_init__( None )
    self.lock = threading.RLock()
    self.actions = []
    # look for the main thread
    mainthreadfound = False
    for thread in threading.enumerate():
      if isinstance( thread, threading._MainThread ):
        mainthreadfound = True
        self.mainThread=thread
        break
    if not mainthreadfound:
      print 'Warning: main thread not found'
      self.mainThread=threading.currentThread()

  def _postEvent( self ):
    class QtThreadCallEvent( QEvent ):
      def __init__( self, qthreadcall ):
        QEvent.__init__( self, QEvent.Type( QEvent.User + 24 ) )
        self.qthreadcall = qthreadcall
    QCoreApplication.instance().postEvent( self, 
      QtThreadCallEvent( self ) )

  def event( self, e ):
    sys.stdout.flush()
    if e.type() == QEvent.User + 24:
      self.doAction()
      return True
    return QObject.event( self, e )

  def push( self, function, *args, **kwargs ):
    """
    Add a function call to the actions list. the call is executed immediatly if current thread is main thread.
    
    @type function: function
    @param function: the function to call in main thread.
    """
    if self.isInMainThread():
      if kwargs is None or len( kwargs ) == 0:
        apply( function, args )
      else:
        apply( function, args, kwargs )
    else:
      self.lock.acquire()
      try:
        self.actions.append( ( function, args, kwargs ) )
        self._postEvent()
      finally:
        self.lock.release()

  def call( self, function, *args, **kwargs ):
    """
    Send the function call to be executed in the qt main thread and wait for the result.
    
    @type function: function
    @param function: the function to call in main thread.
     
    @return: function call's result
    """
    if self.isInMainThread():
      if kwargs is None or len( kwargs ) == 0:
        return apply( function, args )
      return apply( function, args, kwargs )
    else:
      semaphore = threading.Semaphore( 0 )
      self.lock.acquire()
      try:
        self.actions.append( ( self._callAndWakeUp, ( semaphore, function, args, kwargs ), {} ) )
        self._postEvent()
      finally:
        self.lock.release()
      semaphore.acquire() # block until semaphore is released in _callAndWakeUp method
      result = semaphore._mainThreadActionResult
      exception = semaphore._mainThreadActionException
      if exception is not None:
        e, v, t = exception
        raise e, v, t
      return result

  def _callAndWakeUp( self, semaphore, function, args, kwargs ):
    """
    Call the function, set the result in semaphore attributes and release the semaphore.
    
    @type semaphore: threading.Semaphore
    @ivar semaphore: thread which has added this task is blocked on this semaphore. function call's result will be kept in this semaphore attributes.
    @type function: function
    @param function: the function to call in main thread.
    """
    semaphore._mainThreadActionResult = None
    semaphore._mainThreadActionException = None
    try:
      if kwargs is None or len( kwargs ) == 0:
        semaphore._mainThreadActionResult = function( *args )
      else:
        semaphore._mainThreadActionResult = function( *args, **kwargs )
    except:
      semaphore._mainThreadActionException = sys.exc_info()
    semaphore.release() # release the semaphore to unblock the thread which waits for the function call's result

  def isInMainThread( self ):
    """
    @rtype: boolean
    @return: True if current thread is main thread
    """ 
    #return threading.currentThread().getName() == 'MainThread'
    return threading.currentThread() is self.mainThread

  def doAction( self ):
    """
    This method is called each time the timer timeout.
    It executes all functions in actions list.
    """
    self.lock.acquire()
    try:
      actions = self.actions
      #print "actions to do", self.actions
      self.actions = []
    finally:
      self.lock.release()
    for ( function, args, kwargs ) in actions:
      try:
        if kwargs is None or len( kwargs ) == 0:
          apply( function, args )
        else:
          apply( function, args, kwargs )
      except:
        # Should call a customizable function here
        raise
