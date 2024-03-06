"""
Base classes for reading various minf formats (XML, HDF5, Python's pickle, etc.)
"""

__docformat__ = "restructuredtext en"


from soma.translation import translate as _

# ------------------------------------------------------------------------------


class RegisterMinfReaderClass(type):
    """
    RegisterMinfReaderClass is used as metaclass of L{MinfReader} to automatically
    register all classes derived from L{MinfReader}.
    """

    def __init__(cls, name, bases, dict):
        # why test hasattr(cls, name) ?
        # on Ubuntu 12.04 the six.with_metaclass() function may trigger this
        # constructor on a "NewBase" type which doesn't have the name attribute
        if hasattr(cls, "name") and cls.name is not None:
            MinfReader._allReaderClasses[cls.name] = cls


# ------------------------------------------------------------------------------
class MinfReader(metaclass=RegisterMinfReaderClass):
    """
    Class derived from MinfReader are responsible of reading a specific format of
    minf file. This version only support XML format but other formats may be added
    later (such as HDF5).
    All classes derived from L{MinfReader} must define a L{name} class attribute
    and L{nodeIterator} method. The constructor of L{MinfReader} derived class
    must be callable without arguments (except C{self}), it does not have to be
    overloaded.
    """

    #: all classes derived from L{MinfReader} are automatically stored in that
    #: dictionary (keys are formats name and values are class objects).
    _allReaderClasses = {}

    #: class derived from L{MinfReader} must set a format name in this attribute.
    name = None

    def createReader(format):
        """
        This static method create a L{MinfReader} instance by looking for a registered
        L{MinfReader} derived classes named C{format}.
        @param format: name of the minf format.
        @type  format: string
        @returns: L{MinfReader} derived class instance.
        """
        reader = MinfReader._allReaderClasses.get(format)
        if reader is None:
            raise ValueError(
                _(
                    'No minf reader for format "%(format)s", possible formats are: %(possible)s'
                )
                % {
                    "format": format,
                    "possible": ", ".join(
                        ['"' + i + '"' for i in MinfReader._allReaderClasses]
                    ),
                }
            )
        return reader()

    createReader = staticmethod(createReader)

    def reduction(self, source):
        """
        Return a pair C{( reduction, buffer )} where C{reduction} is the name of
        the L{MinfReducer<soma.minf.tree.MinfReducer} stored in the minf file and
        C{buffer} is the data that have been read from file.
        """

    def nodeIterator(self, source):
        """
        Return an iterator on all the nodes of the minf tree corresponding to the content
        of the C{source} minf file.
        @param source: source of the minf file.
        @type  source: string of file object
        """
