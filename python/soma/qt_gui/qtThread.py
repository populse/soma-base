# -*- coding: utf-8 -*-
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

* author: Dominique Geffroy
* organization: NeuroSpin
* license: `CeCILL B <http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html>`_
"""
from __future__ import print_function

from __future__ import absolute_import
__docformat__ = "restructuredtext en"

import sys
import threading
import six
from soma.qt_gui.qt_backend.QtCore import QObject, QTimer, QEvent, QCoreApplication
from soma import singleton


class FakeQtThreadCall(QObject):

    '''
    Fake QtThreadCall that behave as if always used from main thread.
    '''
    def isInMainThread():
        return True
    isInMainThread = staticmethod(isInMainThread)

    def push(function, *args, **kwargs):
        if kwargs is None or not kwargs:
            function(*args)
        else:
            function(*args, **kwargs)
    push = staticmethod(push)

    def call(function, *args, **kwargs):
        if kwargs is None or not kwargs:
            return function(*args)
        else:
            return function(*args, **kwargs)
    call = staticmethod(call)


class QtThreadCall(singleton.Singleton, QObject):

    """
    This object enables to send tasks to be executed by qt thread (main thread).
    This object must be initialized in qt thread.
    It starts a QTimer and periodically execute tasks in its actions list.

    Attributes
    ----------
    lock: RLock
        lock to prevent concurrent access to actions list
    actions: list
        tasks to execute
    mainThread: Thread
        current thread at object initialisation
    timer: QTimer
        timer to wake this object periodically
    """

    def __singleton_init__(self):
        # QObject.__init__( self, None )
        super(QtThreadCall, self).__singleton_init__(None)
        self.lock = threading.RLock()
        self.actions = []
        # look for the main thread
        mainthreadfound = False
        for thread in threading.enumerate():
            if isinstance(thread, threading._MainThread):
                mainthreadfound = True
                self.mainThread = thread
                break
        if not mainthreadfound:
            print('Warning: main thread not found')
            self.mainThread = threading.current_thread()

    def _postEvent(self):
        class QtThreadCallEvent(QEvent):

            def __init__(self, qthreadcall):
                QEvent.__init__(self, QEvent.Type(QEvent.User + 24))
                self.qthreadcall = qthreadcall
        QCoreApplication.instance().postEvent(self,
                                              QtThreadCallEvent(self))

    def event(self, e):
        sys.stdout.flush()
        if e.type() == QEvent.User + 24:
            self.doAction()
            return True
        return QObject.event(self, e)

    def push(self, function, *args, **kwargs):
        """
        Add a function call to the actions list. the call is executed immediatly if current thread is main thread. Otherwise it will be executed some time in the main thread (asynchronously to the current thread). The function return value is ignored and will be lost.

        Parameters
        ----------
        function: function
            the function to call in main thread.
        """
        if self.isInMainThread():
            if kwargs is None or len(kwargs) == 0:
                function(*args)
            else:
                function(*args, **kwargs)
        else:
            self.lock.acquire()
            try:
                self.actions.append((function, args, kwargs))
                self._postEvent()
            finally:
                self.lock.release()

    def call(self, function, *args, **kwargs):
        """
        Send the function call to be executed in the qt main thread and wait for the result. The result will be returned to the calling thread.

        .. warning::

            If returned objects are thread-depenendent (typically, Qt widgets),
            they must be destroyed within the thread which created them, namely
            the main thread. The :class:`MainThreadLife` object wrapper may be
            helpful for this.

        Parameters
        ----------
        function: function
            the function to call in main thread.

        Returns
        -------
        function call result
        """
        if self.isInMainThread():
            if kwargs is None or len(kwargs) == 0:
                return function(*args)
            return function(*args, **kwargs)
        else:
            semaphore = threading.Semaphore(0)
            self.lock.acquire()
            try:
                self.actions.append(
                    (self._callAndWakeUp, (semaphore, function, args, kwargs), {}))
                self._postEvent()
            finally:
                self.lock.release()
            semaphore.acquire()
                              # block until semaphore is released in
                              # _callAndWakeUp method
            result = semaphore._mainThreadActionResult
            exception = semaphore._mainThreadActionException
            if exception is not None:
                six.reraise(*exception)
            return result

    def _callAndWakeUp(self, semaphore, function, args, kwargs):
        """
        Call the function, set the result in semaphore attributes and release the semaphore.

        Parameters
        ----------
        semaphore: threading.Semaphore
            thread which has added this task is blocked on this semaphore. function call's result will be kept in this semaphore attributes.
        function: function
            the function to call in main thread.
        """
        semaphore._mainThreadActionResult = None
        semaphore._mainThreadActionException = None
        try:
            if kwargs is None or len(kwargs) == 0:
                semaphore._mainThreadActionResult = function(*args)
            else:
                semaphore._mainThreadActionResult = function(*args, **kwargs)
        except:  # noqa: E722
            semaphore._mainThreadActionException = sys.exc_info()
        semaphore.release()
                          # release the semaphore to unblock the thread which
                          # waits for the function call's result

    def isInMainThread(self):
        """
        Returns
        -------
        boolean: True if the current thread is the main thread
        """
        # return threading.currentThread().getName() == 'MainThread'
        return threading.current_thread() is self.mainThread

    def doAction(self):
        """
        This method is called each time the timer timeout.
        It executes all functions in actions list.
        """
        self.lock.acquire()
        try:
            actions = self.actions
            # print("actions to do", self.actions)
            self.actions = []
        finally:
            self.lock.release()
        for (function, args, kwargs) in actions:
            try:
                if kwargs is None or len(kwargs) == 0:
                    function(*args)
                else:
                    function(*args, **kwargs)
            except:  # noqa: E722
                # Should call a customizable function here
                raise


class MainThreadLife(object):
    '''This wrapper class ensures the contained object is deleted in the main
    thread, and not in the current non-GUI thread. The principle is the
    following:

    * acquire a lock
    * pass the object to something in the main thread
    * the main thread waits on the lock while holding a reference on the object
    * we delete the object in the calling thread
    * the lock is releasd from the calling thread
    * now the main thread can go on, and del / release the ref on the object:
      it is the last ref on it, so it is actually deleted there.

    .. warning::

        The thing is only working if no other reference is held anywhere on the underlying object, otherwise we do not control its deletion.

    Ex:

    ::

        # from a secondary thread

        widget = QtThreadCall().call(Qt.QWidget)
        # widget.show() # should crash
        QtThreadCall().push(widget.show)
        # ... use it ...
        # del widget # should crash

    ::

        # from a secondary thread

        widget = MainThreadLife(QtThreadCall().call(Qt.QWidget))
        QtThreadCall().push(widget.ref().show)
        # ... use it ...
        del widget # OK
    '''
    def __init__(self, obj_life=None, *args, **kwargs):
        super(MainThreadLife, self).__init__(*args, **kwargs)
        if obj_life is not None:
            self._obj_life = obj_life

    def __del__(self):
        if (not isinstance(threading.current_thread(), threading._MainThread)
                and hasattr(self, '_obj_life')):
            lock = threading.Lock()
            lock.acquire()
            QtThreadCall().push(MainThreadLife.delInMainThread, lock,
                                self._obj_life)
            del self._obj_life
            lock.release()

    def ref(self):
        '''Access the underlying object'''
        return self._obj_life

    @staticmethod
    def delInMainThread(lock, thing):
        # wait for the lock to be released in the process thread
        lock.acquire()
        lock.release()
        # now the process thread should have removed its reference on thing:
        # we can safely delete it fom here, in the main thread.
        del thing # probably useless
