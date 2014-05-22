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
Utils for socket communication
"""
import threading
import socket
import Queue
import errno
import time
import sys

from soma.qt_gui.qt_backend.QtCore import QObject, QSocketNotifier, SIGNAL

class Socket( QObject ):
    """
    Opens a connection to a socket server and provides methods to read from and write to socket streams.
    To handle specific message format, redefine readMessage method. By default it reads a line on the socket.
    To process messages, redefine processMessage method. By default it prints the message to standard output. 
    
    @type dest: string
    @ivar dest: socket server machine
    @type port: int
    @ivar port: port that the socket server listens
    @type socket: socket.socket
    @ivar socket: python socket object
    @type socketnotifier: qt.QSocketNotifier
    @ivar socketnotifier: the notifier sends a signal when there's something to read on the socket.
    @type readLock: threading.Lock
    @ivar readLock: lock to prevent threads from reading at the same time on the socket
    @type writeLock: threading.Lock
    @ivar writeLock: lock to prevent threads from writing at the same time on the socket
    @type lock: threading.RLock
    @ivar lock: lock to prevent concurrent access on object data because it can be used by multiple threads.
    At least principal thread and reading messages thread when it not possible to use a QSocketNotifier.
    @type initialized: bool
    @ivar initialized: indicates if the connection is correctly opened
    @type notifyenabled: bool
    @ivar notifyenabled: indicates if message received on the socket must be processed.
    
    @type loopRetry: int
    @cvar loopRetry: max number of connection tries
    @type defaultPort: int
    @cvar defaultPort: default port for socket server
    """
    
    loopRetry = 60      # Retry to connect 60 times (1 minute)
    defaultPort = 50007
    
    def __init__( self, host, port=None):
        """
        @type host: string
        @param host: socket server machine (localhost if it is current machine)
        @type port: int
        @param port: port that the socket server listens
        """
        apply( QObject.__init__, ( self, )  )
        self.dest = host
        self.port = port
        self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.socketnotifier = None
        # We are in a multi threaded environnement, so only one thread can
        # use the socket at the same time
        self.readLock = threading.Lock()
        self.writeLock = threading.Lock()
        self.lock = threading.RLock()
        self.initialized = 0
        self.notifyenabled = 1
                
    def initialize( self, port = None ):
        """
        Connects the socket to the server and sets the frame to read data from the socket.
        Two methods for reading :
          - reading thread
          - QSocketNotifier (not possible on windows platform)
        @type port: int
        @param port: port that the socket server listens
        """
        if self.initialized:
            return

        if port is not None:
            self.port = port
        # We have to retry connecting because it can take time for the socket server to start
        i = 0
        while i < Socket.loopRetry:
            # using socket.htons to convert port number is useless
            # because Python take care of this
            res = self.socket.connect_ex( ( self.dest, self.port ) )
            if res != 0:
                # retry to connect
                time.sleep( 1 )
                self.socket.close()    
                self.socket = socket.socket( socket.AF_INET,
                                             socket.SOCK_STREAM )
                i = i + 1
            else:
                # Connection successful, exit from the while loop
                break

        if findPlatform() == 'windows':
          # on windows, QSocketNotifier seems to make the socket fail
          self.usethread = 1
        else: 
          self.usethread = 1#0 # QSocketNotifier seems to create problems when it is not used in qt main thread (application freeze)
        #sets the frame to read from the socket
        if self.usethread:
          # reading thread
          self.readthread = threading.Thread( target = self.readForever )
          self.readthread.setDaemon( True ) # don't block when exiting program
          self._messages = Queue.Queue( 500 )
          self.socket.setblocking( 0 )
          self.initialized = 1
          self.readthread.start()
        else:
          # QSocketNotifier that signals that data is enable for reading
          self.socketnotifier = QSocketNotifier(self.socket.fileno(), QSocketNotifier.Read)#, self )
          self.connect( self.socketnotifier, SIGNAL( "activated(int)" ), self.messageHandler )
          self.socketnotifier.setEnabled(True)
          self.initialized = 1

    def messageHandler( self ):
        """
        This method is called when a message is received on the socket. 
        Gets and processes the message.
        """
        excep = None
        msg=None
        try:
          msg = self.getMessage()
        except Exception, e:
          excep = e
        self.processMessage( msg, excep )
    
    def getMessage( self, timeout=30 ):
      '''
      Called by message handler to gets the last received message. 
      If socket communication is managed by a QSocketNotifier, the message is not yet read, so this method read it. 
      If reading is in another process, the message is already read and it is in messages queue. 
      '''
      if not self.initialized:
          return '', ''
      if self.usethread:
        # block until a message arrives in queue
        self.lock.acquire()
        try:
          try:
            msg = self._messages.get( True, timeout )
          except Queue.Empty, e:
            raise IOError( errno.ETIMEDOUT,  'socket communication timed out' )
        finally:
          self.lock.release()
      else:
        try:
          msg = self.readMessage(timeout)
        except IOError, e:
          if e[ 0 ] == errno.EPIPE:
            # The socket has been closed
            # Return to avoid infinite loop
            self.close()
          raise
      return msg

    def processMessage(self, msg, excep):
        """
        Processes a message received on the socket. 
        This method only print the message. To do some specific treatment, subclass Socket and redefine this method.
        """
        print "message received :", msg, excep
        
    def send( self, msg ):
        """
        Sends data to the connected socket.
        @type msg: string
        @param msg: the message to send.
        """
        if not self.initialized:
            return
        totalsent = 0
        msglen = len( msg )
        # Send the message atomically (send is not thread-safe)
        close = False
        self.writeLock.acquire()
        # sendall() only appeared in python 2.1.12
        #self.socket.sendall( msg )
        n = 0
        try:
          while n < msglen:
            try:
              n += self.socket.send( msg[n:] )
            except socket.error, e:
              if e[0] == errno.EWOULDBLOCK:
                time.sleep( 0.02 )
              else:
                close = True
                break
        finally:
          self.writeLock.release()
        if close:
          self.close()

    def readForever( self ):
      """
      Reading loop to handle reading messages from the socket.
      Used only if QSocketNotifier cannot be used.
      """
      while self.initialized:
        try:
          msg=self.readMessage()
          self.lock.acquire()
          try:
            self._messages.put( msg )
          finally:
            self.lock.release()
          if self.notifyenabled:
            self.messageHandler()
        except IOError, e:
          if e[ 0 ] != errno.ETIMEDOUT:
            self.close()
            #raise
        if not self.initialized:
            break

    def readLine( self, timeout ):
      """
      Reads a line of data from the socket (a string followed by '\n').
      self.readLock must be acquired before calling this method.
      If data cannot be read before timeout (in seconds), an IOError exception is raised.
      @type timeout: int
      @param timeout: max time to wait before reading the message.
      """
      msg = ''
      char = ''
      waitedTime = 0
      # Receive the message atomically
      while char != '\n':
        if char != '':
          msg += char
        try:
          char = self.socket.recv( 1 )
          waitedTime = 0
          if char == '\0' or char == '':
            e = IOError( errno.EPIPE, 'socket communication interrupted' )
            raise e
        except socket.error, e:
          if e[0] == errno.EWOULDBLOCK:
            char = ''
            time.sleep( 0.02 )
            waitedTime += 0.02
            if waitedTime >= timeout:
              raise IOError( errno.ETIMEDOUT, 'socket communication timed out' )
          else:
            raise IOError( errno.EPIPE, 'socket communication interrupted' )
      return msg

    def readMessage(self, timeout=30 ):
      """
      Reads a message from the socket. This method only gets the readlock and reads a line.
      To read specific message formats, subclass Socket and redefine this method.
      
      @type timeout: int
      @param timeout: max time to wait before reading the message.
      @rtype: string
      @return: the message received from the socket
      """
      self.readLock.acquire()
      try:
        msg = self.readLine( timeout )
      finally:
        self.readLock.release()
      return msg
      
    def findFreePort( self ):
        """
        Try to find the first unused port.
        @rtype: int
        @return: numero of a free port
        """
        if self.port is not None:
          startport = self.port
        else:
          startport = Socket.defaultPort
        res = 0
        tmpsocket = socket.socket( socket.AF_INET,
                                   socket.SOCK_STREAM )
        while res == 0:
            res = tmpsocket.connect_ex( ( self.dest, startport ) )
            tmpsocket.close()
            if res != 0:
                return startport
            tmpsocket = socket.socket( socket.AF_INET,
                                       socket.SOCK_STREAM )
            startport += 1
    
    def disableHandler( self ):
        """Disables reading from the socket."""
        self.notifyenabled = 0
        if self.socketnotifier is not None:
            self.socketnotifier.setEnabled( 0 )

    def enableHandler( self ):
        """Enables reading from the socket."""
        self.notifyenabled = 1
        if self.socketnotifier is not None:
            self.socketnotifier.setEnabled( 1 )
        
    def __del__( self ):
        """
        Closes the connection when the object is deleted
        """
        self.close()

    def close( self ):
        """
        Closes the connection.
        """
        if not self.initialized:
            return
        self.initialized = 0
        self.disableHandler()
        self.socketnotifier = None
        self.socket.close()
        if self.usethread and self.readthread != threading.currentThread():
            self.readthread.join()

def findPlatform():
  """
  Identify platform, possible return values are :
    - 'windows': Windows
    - 'linux': Linux
    - 'sunos': SunOS (Solaris)
    - 'darwin': Darwin (MacOS X)
    - None: unknown  
  """
  if sys.platform[:3] == "win":
    return 'windows'
  else:
    if sys.platform.find( 'linux' ) != -1:
      return 'linux'
    if sys.platform.find( 'sunos' ) != -1:
      return 'sunos'
    if sys.platform.find( 'darwin' ) != -1:
      return 'darwin'
    if sys.platform.find( 'irix' ) != -1:
      return 'irix'
    return sys.platform
  