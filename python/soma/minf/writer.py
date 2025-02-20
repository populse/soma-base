"""
Base classes for writing various minf formats (XML, HDF5, Python's pickle, etc.)
"""

__docformat__ = "restructuredtext en"

from soma.translation import translate as _


__docformat__ = "restructuredtext en"


#------------------------------------------------------------------------------
class RegisterMinfWriterClass(type):
    """
    RegisterMinfWriterClass is used as metaclass of L{MinfWriter} to automatically
    register all classes derived from L{MinfWriter}.
    """

    def __init__(cls, name, bases, dict):
        # why test hasattr(cls, name) ?
        # on Ubuntu 12.04 the six.with_metaclass() function may trigger this
        # constructor on a "NewBase" type which doesn't have the name attribute
        if hasattr(cls, "name") and cls.name is not None:
            MinfWriter._allWriterClasses[cls.name] = cls


# ------------------------------------------------------------------------------
class MinfWriter(metaclass=RegisterMinfWriterClass):
    """
    Class derived from MinfWriter are responsible of writing a specific format of
    minf file. This version only support XML format but other formats may
    be added later (such as HDF5).
    All classes derived from L{MinfWriter} must define a L{name} class attribute
    the following methods:
      - L{__init__} to construct writer instances.
      - L{write} to write objects in minf file.
      - L{close} to terminate writing.
    """

    #: all classes derived from L{MinfWriter} are automatically stored in that
    #: dictionary (keys are formats name and values are class objects).
    _allWriterClasses = {}

    #: class derived from L{MinfWriter} must set a format name in this attribute.
    name = None

    def __init__(self, file, reducer, close_file=False):
        '''
        Constructor of classes derived from L{MinfWriter} must be callable with two
        parameters.
        @param file: file object (opened for writing) where the minf file is
          written.
        @type  file: any object respecting Python file object API
        @param reducer: name of the reducer to use (see L{soma.minf.tree} for
          more information about reducers).
        @type  reducer: string
        plus optionally:
        @type close_file: bool
        @param close_file: if the given file should be closed after the
        writing operation
        '''

    def write(self, value):
        """
        Write an object into the minf file.
        @param value: any value that can be written in this minf file.
        """

    def close(self):
        """
        Close the writer, further calls to L{write} method will lead to an error.
        The underlying file is NOT closed.
        """

    def createWriter(destFile, format, reducer):
        """
        This static method create a L{MinfWriter} instance by looking for a
        registered L{MinfWriter} derived class named C{format}. Parameters
        C{destFile} and C{reducer} are passed to the derived class constructor.
        @param format: name of the minf format.
        @type  format: string
        @returns: L{MinfWriter} derived class instance.
        @param file: file name or file object (opened for writing) where the minf
          file is written. If it is a file name, it is opened with
          C{open( destFile, 'wb' )}.
        @type  file: string or any object respecting Python file object API
        @param reducer: name of the reducer to use (see L{soma.minf.tree} for
          more information about reducers).
        @type  reducer: string
        """
        writer = MinfWriter._allWriterClasses.get(format)
        if writer is None:
            raise ValueError(
                _('No minf writer for format "%(format)s", possible formats are: %(possible)s')
                %
                {'format': format,
                 'possible': ', '.join(['"' + i + '"'
                                        for i in
                                        MinfWriter._allWriterClasses])})
        close_file = False
        if not hasattr(destFile, 'write'):
            destFile = open(destFile, 'w')
            close_file = True
        return writer(destFile, reducer, close_file=close_file)
    createWriter = staticmethod(createWriter)
