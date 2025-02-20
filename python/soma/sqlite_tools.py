"""
This module contains functions and classes related to sqlite databases.

* author: Yann Cointepas
* organization: NeuroSpin
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
"""

__docformat__ = "restructuredtext en"


import sqlite3
import sys
import threading

# ------------------------------------------------------------------------------


class ThreadSafeSQLiteConnection:
    """
    Python wrapping of SQLite do not allow sharing of database connection between
    threads. This class allows to automatically create a connection for each
    thread.
    """

    _currentId = 0
    _classLock = threading.RLock()

    def __init__(self, *args, **kwargs):
        """
        A ThreadSafeSQLiteConnection is created with the parameters that
        would be used for a call to sqlite3.connect() in a single thread
        system. These parameters are stored to allow to create a separate
        SQLite connection for any thread with get_connection().
        """
        super().__init__()
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

    def __del__(self):
        if threading is None:
            # The interpreter is exiting and we cannot access threading
            # module. We cannot do anything.
            return
        if self.__args is not None:
            sqliteFile = self.__args[0]
            try:
                self.close()
                for thread in self.connections.keys():
                    connection, connectionClosed = self.connections[thread]
                    if connection is not None:
                        currentThread = threading.current_thread().getName()
                        print(
                            "WARNING: internal error: an sqlite connection on",
                            repr(sqliteFile),
                            "is opened for thread",
                            thread,
                            "but the corresponding ThreadSafeSQLiteConnection instance (number "
                            + str(self._id)
                            + ") is being deleted in thread",
                            currentThread
                            + ". Method currentThreadCleanup() should have been called from",
                            thread,
                            "to suppress this warning.",
                            file=sys.stderr,
                        )
            except ImportError:
                # python is shutting down
                pass

    def get_connection(self):
        """
        Returns a SQLite connection (i.e. the result of sqlite3.connect)
        for the current thread. If it does not already exists, it is created
        and stored for the current thread. In order to destroy this connection
        it is necessary to call self.delete_connection() from the current
        thread. If a ThreadSafeSQLiteConnection is destroyed in a thread,
        all connections opened in other threads must have been deleted.
        """
        if self.__args is None:
            raise RuntimeError(
                "Attempt to access to a closed ThreadSafeSQLiteConnection"
            )
        currentThread = threading.current_thread().getName()
        # print('!ThreadSafeSQLiteConnection:' + currentThread + '!')
        # _getConnection( id =', self._id, ')', self.__args
        self._instanceLock.acquire()
        try:
            # currentThreadConnections = self.connections.setdefault( currentThread, {} )
            # print('!ThreadSafeSQLiteConnection:' + currentThread + '!')
            # currentThreadConnections =', currentThreadConnections
            connection, connectionClosed = self.connections.get(
                currentThread, (None, True)
            )
            if connectionClosed:
                if connection is not None:
                    connection.close()
                connection = sqlite3.connect(*self.__args, **self.__kwargs)
                # print('!ThreadSafeSQLiteConnection:' + currentThread + '!'
                # opened', connection)
                self.connections[currentThread] = (connection, False)
        finally:
            self._instanceLock.release()
        return connection

    def delete_connection(self):
        """
        Delete the connection previously created for the current thread with
        get_connection()
        """
        if threading.current_thread is None:
            # exiting, threading attributes have become None
            return
        currentThread = threading.current_thread().name
        self._instanceLock.acquire()
        try:
            connection, connectionClosed = self.connections.pop(
                currentThread, (None, True)
            )
        finally:
            self._instanceLock.release()
        if connection is not None:
            connection.close()

    def close(self):
        """
        After this call no more connection can be opened
        """
        if self.__args is not None:
            self.closeSqliteConnections()
            self.__args = None
            self.__kwargs = None

    def close_connections(self):
        """
        Mark the opened connection for all the threads as closed.
        Subsequent calls to get_connection() will have to
        recreate the sqlite connection with sqlite3.connect().
        This method does not delete the connection of the current
        thread.
        """
        if self.__args is not None:
            if threading.current_thread is None:
                # exiting, threading attributes have become None
                return
            self.currentThreadCleanup()
            self._instanceLock.acquire()
            try:
                for thread in self.connections.keys():
                    connection, connectionClosed = self.connections[thread]
                    self.connections[thread] = (connection, True)
            finally:
                self._instanceLock.release()

    # For backward compatibility
    _getConnection = get_connection
    currentThreadCleanup = delete_connection
    closeSqliteConnections = close_connections
