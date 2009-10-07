# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL-B license under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the 
# terms of the CeCILL-B license as circulated by CEA, CNRS
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
# knowledge of the CeCILL-B license and that you accept its terms.


'''
The signature module provide a mechanism to define a type on some attributes of a Python object and to control the value and the modification of these attributes. This control is done I{via} a set of features:
  - B{initialization}: an attribute can have a default initial value.
  - B{validation}: the type of an attribute defines the validity domain of its  
    value. For example, an attribute whose type is 
    L{Number<soma.signature.Number>} cannot have a C{unicode} value but it 
    can have an C{int} or a C{float} value.
  - B{notification}: Setting a value to an attribute or, in some cases, 
    modifying an attribute's value can notify other parts of the program by 
    calling previously registered functions.
  - B{customization}: A programmer can define its own attribute types and 
    customize the behaviour of the various features provided by this module.
  - B{introspection}: signature can be parsed to retrieve, not only, all 
    attributes names and types, but also, the parameters used to define each 
    type. This is important to completely separate the core of the signature 
    mechanism from external package that need its knowledge. The visualization 
    feature (see below) is an example of such a separate package. Another 
    example could be an XML representation of attribute types allowing to load 
    and save signatures in a language independant way.
  - B{visualization}: automatic contruction of a graphical interface to 
    interactively edit an object is provided. This interface is based on the 
    U{Qt library<http://www.trolltech.com/products/qt>} and is designed to 
    provide an easy to used default interface that can be customized by the 
    programmer.

To benefit from these features, an object must be an instance of a class derived from L{HasSignature}. Such objects have a special attribute called C{signature} containing the definition of all the attributes that are connected to the signature system. These signature attributes are defined in a L{Signature} instance that behave like a dictionary (more precisely a L{SortedDictionary<soma.sorted_dictionary.SortedDictionary>}) whose keys are attribute names and whose values are L{DataType} instances representing attribute types.


Example
=======

Here is a small example showing how to define four classes that use the signature framework::
  from soma.signature import HasSignature, Signature
  from soma.signature import Unicode, Integer, Choice
  
  class Date( HasSignature ):
    signature = Signature(
      'day', Integer( minimum=1, maximum=31 ),
      'month', Integer( minimum=1, maximum=31 ),
      'year', Integer( minimum=1 ),
    )

  class Time( HasSignature ):
    signature = Signature(
      'hour', Integer( minimum=0, maximum=23 ), dict( defaultValue=0 ),
      'minute', Integer( minimum=0, maximum=59 ), dict( defaultValue=0 ),
      'second', Integer( minimum=0, maximum=59 ), dict( defaultValue=0 ),
    )
    
    def __init__( self, **kwargs ):
      HasSignature.__init__( self )
      self.initializeSignatureAttributes( **kwargs )
  
  
  class DateTime( HasSignature ):
    signature = Signature(
      'date', Date,
      'time', Time,
    )

  class Appointment( HasSignature ):
    signature = Signature(
      'what', Unicode,
      'when', DateTime,
      'category', Choice(
        'Professional', 'Personal', 'Other' ),
        dict( defaultValue = 'Professional' ),
    )

Module content
==============

The content of C{soma.signature} module is distributed in many submodules. However, all important items are imported in C{soma.signature}. Therefore, users only need to import items from C{soma.signature}. For example, if one wants to use the L{Number} class defined in the module  L{soma.signature.attributetypes.number}, he just have to use the following import statement::
  from soma.signature import Number

Core classes
------------
 - L{HasSignature}: base class for objects with a signature.
 - L{Signature}: kind of sorted dictionary containing the signature (I{i.e.} 
   attributes declaration) of an object.
 - L{VariableSignature}: a L{Signature} instance cannot be modified, but it can 
   be converted to a L{VariableSignature} that can be modified at run-time.
 - L{DataType}: base class of attribute type classes.
 - L{Undefined}: used to represent an undefined value when C{None} cannot be 
   used because it can be a valid value.

Data type classes
-----------------
  - L{Any}: value of this type may be antyhing
  - L{Unicode}: value of this type is a unicode text
  - L{Bytes}: value of this type is a byte array
  - L{Number}: value is any number (with an optional range).
  - L{Integer}: value is any integer (with an optional range).
  - L{Float}: value is any floating-point number (with an optional range).
  - L{IntegerU8}: L{Integer} between 0 and 255.
  - L{IntegerS8}: L{Integer} between -128 and 127.
  - L{IntegerU16}: L{Integer} between 0 and 65,535.
  - L{IntegerS16}: L{Integer} between -32,768 and 32,767.
  - L{IntegerU32}: L{Integer} between 0 and 4,294,967,295.
  - L{IntegerS32}: L{Integer} between -2,147,483,648 and 2,147,483,647.
  - L{IntegerU64}: L{Integer} between 0 and 18,446,744,073,709,551,615.
  - L{IntegerS64}: L{Integer} between -9,223,372,036,854,775,808 and 9,223,372,036,854,775,807.
  - L{Float32}: IEEE 754 single precision floating point (between -3.40282347e+38 and 3.40282347e+38).
  - L{Float64}: IEEE 754 double precision floating point (between  -1.7976931348623157e+308 and 1.7976931348623157e+308).
  - L{Boolean}: value of this type is a Python boolean.
  - L{FileName}: value of this type is a L{Unicode} representing a file name.
  - L{Choice}: value of this type is a choice among a predefined set of values.
  - L{OpenedChoice}: value of this type is a choice among a predefined set of values or any unicode text.
  - L{Sequence}: value is a Python sequence whose elements are all of the same 
    type.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''

__docformat__ = "epytext en"

from soma.signature.signature import DataType, ClassDataType, Signature, \
                                     VariableSignature, HasSignature, Undefined

from soma.signature.attributetypes.any import Any
from soma.signature.attributetypes.unicode import Unicode
from soma.signature.attributetypes.bytes import Bytes
from soma.signature.attributetypes.number import Number
from soma.signature.attributetypes.float import Float, Float32, Float64
from soma.signature.attributetypes.integer import Integer, IntegerU8, \
  IntegerS8, IntegerU16, IntegerS16, IntegerU32, IntegerS32, IntegerU64, \
  IntegerS64
from soma.signature.attributetypes.choice import Choice
from soma.signature.attributetypes.openedchoice import OpenedChoice
from soma.signature.attributetypes.boolean import Boolean
from soma.signature.attributetypes.fileName  import FileName
from soma.signature.attributetypes.sequence  import Sequence

