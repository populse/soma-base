"""
QLineEditModificationTimer and TimeredQLineEdit classes associate a
QtCore.QTimer to a QtGui.QLineEdit in order to signal user
modification only after an inactivity period.
"""

__docformat__ = "restructuredtext en"

import weakref

from soma.qt_gui.predef_lineedit import QPredefLineEdit
from soma.qt_gui.qt_backend import QtCore

# -------------------------------------------------------------------------


class QLineEditModificationTimer(QtCore.QObject):
    """
    A QLineEditModificationTimer instance is associated to a
    QtGui.QLineEdit instance, it listens all user modification (Qt
    signal 'textChanged( const QString & )') and emits a
    signal 'userModification()' when timerInterval milliseconds passed
    since the last user modification.
    """

    # Default timer interval in milliseconds
    defaultTimerInterval = 2000
    userModification = QtCore.Signal()

    def __init__(self, qLineEdit, timerInterval=None):
        """
        .. seealso:: :class:`TimeredQLineEdit`

        Parameters
        ----------
        qLineEdit: (QtGui.QLineEdit instance)
            widget associated with this QLineEditModificationTimer.
        timerInterval: (milliseconds)
            minimum inactivity period before emitting
            userModification signal. Default value is
            QLineEditModificationTimer.defaultTimerInterval

        """

        QtCore.QObject.__init__(self)
        # QLineEdit<qt.QLineEdit> instance associated with this
        # QLineEditModificationTimer
        self.qLineEdit = weakref.proxy(qLineEdit)
        if timerInterval is None:
            self.timerInterval = self.defaultTimerInterval
        else:
            # minimum inactivity period before emitting C{userModification}
            # signal.
            self.timerInterval = timerInterval
        self.__timer = QtCore.QTimer(self)
        self.__timer.setSingleShot(True)
        self.__internalModification = False
        self.qLineEdit.textChanged.connect(self._userModification)
        self.qLineEdit.editingFinished.connect(self._noMoreUserModification)
        self.__timer.timeout.connect(self.modificationTimeout)

    def close(self):
        self.stop()
        self.qLineEdit.textChanged.disconnect(self._userModification)
        # emit a last signal if modifs have been done
        self.qLineEdit.editingFinished.disconnect(self._noMoreUserModification)
        self.__timer.timeout.disconnect(self.modificationTimeout)

    def _userModification(self, value):
        if not self.__internalModification:
            self.__timer.start(self.timerInterval)

    def modificationTimeout(self):
        self.userModification.emit()  # self.qLineEdit.text())

    def _noMoreUserModification(self):
        if self.__timer.isActive():
            self.__timer.stop()
            self.userModification.emit()  # self.qLineEdit.text())

    def stopInternalModification(self):
        """
        Stop emitting ``userModification`` signal when associated
        :pyqt:`QLineEdit <QtGui/QLineEdit.html>` is modified.

        .. seealso:: :meth:`startInternalModification`
        """
        self.__internalModification = False

    def startInternalModification(self):
        """
        Restart emitting C{userModification} signal when associated
        :pyqt:`QLineEdit <QtGui/QLineEdit.html>` is modified.

        .. seealso:: :meth:`stopInternalModification`
        """
        self.__internalModification = True

    def stop(self):
        """
        Stop the timer if it is active.
        """
        self.__timer.stop()

    def isActive(self):
        """
        Returns True if the timer is active, or False otherwise.
        """
        return self.__timer.isActive()


# -------------------------------------------------------------------------
class TimeredQLineEdit(QPredefLineEdit):
    """
    Create a QLineEdit instance that has an private attribute
    containing a QLineEditModificationTimer associated to self. Whenever
    the internal QLineEditModificationTimer emits a userModification
    signal, this signal is also emitted by the TimeredQLineEdit instance.
    """

    userModification = QtCore.Signal()
    focusChange = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        """
        All non keyword parameters of the constructor are passed to
        :pyqt:`QLineEdit <QtGui/QLineEdit.html>` constructor. An optional
        *timerInterval* keyword parameter can be given, it is passed to
        :class:`QLineEditModificationTimer` constructor. At the time this class
        was created, :pyqt:`QLineEdit <QtGui/QLineEdit.html>` constructor did
        not accept keyword parameters.
        """
        timerInterval = kwargs.pop("timerInterval", None)
        if kwargs:
            super().__init__(*args, **kwargs)
        else:
            super().__init__(*args)
        self.__timer = QLineEditModificationTimer(self, timerInterval=timerInterval)
        self.__timer.userModification.connect(self.userModification)

    def stopInternalModification(self):
        """
        .. seealso:: :meth:`QLineEditModificationTimer.stopInternalModification`
        """
        self.__timer.stopInternalModification()

    def startInternalModification(self):
        """
        .. seealso:: :meth:`QLineEditModificationTimer.startInternalModification`
        """
        self.__timer.startInternalModification()

    def close(self):
        self.__timer.close()
        super().close()

    def set_value(self, value):
        super().set_value(value)
        self.userModification.emit()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focusChange.emit(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focusChange.emit(False)
