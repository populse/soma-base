from soma.singleton import Singleton

"""
attr:`undefined` is a constant that can be used as
a special value different from any other Python value including *None*.

Example::

    from soma.undefined import undefined

    if object.value is undefined:
        # do something
"""
__docformat__ = "restructuredtext en"


class UndefinedClass(Singleton):
    """
    *UndefinedClass* instance is used to represent an undefined attribute
    value when *None* cannot be used because it can be a valid value.

    Should only be used for value checking.
    """

    def __repr__(self):
        """
        Returns
        -------
        ``'<undefined>'``
        """
        return "<undefined>"

    def __bool__(self):
        """
        undefined is always a False value.

        Returns
        -------
        False
        """
        return False


Undefined = undefined = UndefinedClass()
