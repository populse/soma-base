import enum
import inspect
import sys


def sip4_to_sip6_enums(module, recursive=True):
    """Convert Sip4 style enums to sip6 style enums.

    Sip4 exports C++ enums as in C++, ex::

        instance.ENUM_VALUE  # where ENUM_VALUE is an instance of EnumType

    Sip6 keeps values inside the enum type::

        instance.EnumType.ENUM_VALUE

    In order to maintain code compatible, we duplicate these values. If using
    sip4, then we copy values inside the enum types as sip6 does.

    If recursive (the default), sub-modules are also scanned and modified.
    """
    todo = [module]
    done = set()
    while todo:
        module = todo.pop(0)
        if id(module) in done:
            continue

        done.add(id(module))
        enums = set()
        for iname, item in module.__dict__.items():
            if type(item).__name__ == "enumtype" and id(item) not in done:
                enums.add(item)
                done.add(id(item))
            elif inspect.isclass(item) or (recursive and inspect.ismodule(item)):
                todo.append(item)
        if enums:
            for iname, item in module.__dict__.items():
                if type(item) in enums:
                    setattr(type(item), iname, item)


def sip6_to_sip4(module, recursive=True):
    """Convert Sip6 style enums to sip4 style enums.

    Sip4 exports C++ enums as in C++, ex::

        instance.ENUM_VALUE  # where ENUM_VALUE is an instance of EnumType

    Sip6 keeps values inside the enum type::

        instance.EnumType.ENUM_VALUE

    In order to maintain code compatible, we duplicate these values. If using
    sip6, then we copy values outside the enum types as sip4 does.
    Moreover Qt5 uses dedicated types for enum combinations:
    ``Qt.KeyboardModifier | Qt.KeyboardModofier -> Qt.KeyboardMofifiers``
    Qt6 uses the same type ``Qt.KeyboardModifier`` for combinations. We also
    try to duplicate the enum types as ``<enum_type>s``.

    If recursive (the default), sub-modules are also scanned and modified.
    """
    todo = [module]
    done = set()
    while todo:
        module = todo.pop(0)
        if id(module) in done:
            continue

        done.add(id(module))
        enums = {}
        for iname, item in module.__dict__.items():
            if type(item) is enum.EnumMeta and id(item) not in done:
                enums[iname] = item
                done.add(id(item))
            elif inspect.isclass(item) or (recursive and inspect.ismodule(item)):
                todo.append(item)
        for iname, entype in enums.items():
            for name in entype._member_map_:
                setattr(module, name, getattr(entype, name))
            if iname + "s" not in module.__dict__:
                setattr(module, iname + "s", entype)


def sip_export_enums(module, recursive=True):
    """Convert Sip6 style enums to sip4 style enums, or the contrary.

    Sip4 exports C++ enums as in C++, ex::

        instance.ENUM_VALUE  # where ENUM_VALUE is an instance of EnumType

    Sip6 keeps values inside the enum type::

        instance.EnumType.ENUM_VALUE

    In order to maintain code compatible, we duplicate these values. If using
    sip6, then we copy values outside the enum types as sip4 does. If using
    sip4, then we copy values inside the enum types as sip6 does.

    If recursive (the default), sub-modules are also scanned and modified.
    """
    sip = sys.modules["sip"]
    if sip.SIP_VERSION >= 0x060000:
        sip6_to_sip4(module, recursive=recursive)
    else:
        sip4_to_sip6_enums(module, recursive=recursive)
