"""
Universal unique identifier.
"""

__docformat__ = "epytext en"

import binascii
import random
import struct

# -------------------------------------------------------------------------


class Uuid:
    """
    An Uuid instance is a universal unique identifier. It is a 128 bits
    random value.
    """

    def __new__(cls, value=None):
        if isinstance(value, Uuid):
            return value
        return object.__new__(cls)

    def __init__(self, uuid=None):
        """
        Uuid constructor. If *uuid* is omitted or *None*, a new random
        Uuid is created; if it is a string if must be 36 characters long and
        follow the pattern::

            XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

        where ``X`` is an
        hexadecimal digit (example:
        ``'ad2d8fb0-7831-50bc-2fb6-5df048304001'``).

        If *uuid* is an Uuid instance, no new instance is created, in this
        case, *Uuid(uuid)* returns *uuid*.
        """
        if isinstance(uuid, Uuid):
            return
        if uuid is None:
            # Generate a new 128 bits uuid
            self.__uuid = struct.pack(
                "QQ", random.randrange(2**64 - 1), random.randrange(2**64 - 1)
            )
        else:
            try:
                if isinstance(uuid, str):
                    uuid = uuid.encode(encoding="ascii")
                self.__uuid = binascii.unhexlify(
                    uuid[0:8] + uuid[9:13] + uuid[14:18] + uuid[19:23] + uuid[24:36]
                )
            except Exception as e:
                raise ValueError(f"Invalid uuid string {uuid!r}") from e

    def __getnewargs__(self):
        return (str(self),)

    def __str__(self):
        if not isinstance(self.__uuid, bytes):
            # this should not happen, but has been seen in some places
            import warnings

            warnings.warn(
                f"soma.uuid.Uuid: self.__uuid is not of type bytes, but {type(self.__uuid)}."
                " This is not supposed to happen.",
                stacklevel=2,
            )
            self.__uuid = bytes(self.__uuid, encoding="utf-8")
        return (
            binascii.hexlify(self.__uuid[0:4])
            + b"-"
            + binascii.hexlify(self.__uuid[4:6])
            + b"-"
            + binascii.hexlify(self.__uuid[6:8])
            + b"-"
            + binascii.hexlify(self.__uuid[8:10])
            + b"-"
            + binascii.hexlify(self.__uuid[10:16])
        ).decode()

    def __repr__(self):
        return repr(str(self))

    def __hash__(self):
        return hash(self.__uuid)

    def __eq__(self, other):
        if isinstance(other, Uuid):
            return self.__uuid == other.__uuid
        elif isinstance(other, str):  # assume string-like object (str or unicode)
            try:
                uuid_other = Uuid(other)
            except ValueError:
                return False
            return self.__uuid == uuid_other.__uuid
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, Uuid):
            return self.__uuid != other.__uuid
        elif isinstance(other, str):  # assume string-like object (str or unicode)
            try:
                uuid_other = Uuid(other)
            except ValueError:
                return True
            return self.__uuid != uuid_other.__uuid
        else:
            return True
