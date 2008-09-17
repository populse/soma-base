# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
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

from soma.signature.api import HasSignature, Signature
from soma.signature.api import Unicode, Integer, Choice
from soma.qt3gui.api import ApplicationQt3GUI

def showArgs0():
  print '--> showArgs0()'

def showArgs1( arg1 ):
  print '--> showArgs1(', repr( arg1 ), ')'

def showArgs2( arg1, arg2 ):
  print '--> showArgs2(', repr( arg1 ) + ',', repr( arg2 ), ')'

def showArgs3( arg1, arg2, arg3 ):
  print '--> showArgs3(', repr( arg1 ) + ',', repr( arg2 ) + ',', repr( arg3 ), ')'

def showArgs4( arg1, arg2, arg3, arg4 ):
  print '--> showArgs4(', repr( arg1 ) + ',', repr( arg2 ) + ',', repr( arg3 ) + ',', repr( arg4 ), ')'

def showArgs5( arg1, arg2, arg3, arg4, arg5 ):
  print '--> showArgs5(', repr( arg1 ) + ',', repr( arg2 ) + ',', repr( arg3 ) + ',', repr( arg4 ) + ',', repr( arg5 ), ')'

def showArgs( *args ):
  print '--> showArgs(', ', '.join( [repr(i) for i in args] ), ')'


class Date( HasSignature ):
  signature = Signature(
    'day', Integer( minimum=1, maximum=31 ),
    'month', Integer( minimum=1, maximum=31 ),
    'year', Integer( minimum=1 ),
  )

  def __init__( self, day, month, year ):
    HasSignature.__init__( self )
    self.day = day
    self.month = month
    self.year = year

  def __str__( self ):
    return '%02d/%02d/%04d' % ( self.day, self.month, self.year )


class Time( HasSignature ):
  signature = Signature(
    'hour', Integer( minimum=0, maximum=23 ), dict( defaultValue=0 ),
    'minute', Integer( minimum=0, maximum=59 ), dict( defaultValue=0 ),
    'second', Integer( minimum=0, maximum=59 ), dict( defaultValue=0 ),
  )
  
  def __init__( self, **kwargs ):
    HasSignature.__init__( self )
    self.initializeSignatureAttributes( **kwargs )

  
  def __str__( self ):
    return '%02d:%02d:%02d' % ( self.hour, self.minute, self.second )

class DateTime( HasSignature ):
  signature = Signature(
    'date', Date, dict( defaultValue=Date( 1, 1, 1970 ) ),
    'time', Time, dict( defaultValue=Time() ),
  )
  
  def __init__( self, **kwargs ):
    HasSignature.__init__( self )
    self.initializeSignatureAttributes( **kwargs )

  def __str__( self ):
    return str( self.date ) + " " + str( self.time )


class Appointment( HasSignature ):
  signature = Signature(
    'what', Unicode, dict( defaultValue=u'' ),
    'when', DateTime, dict( defaultValue=DateTime() ),
    'category', Choice(
      'Professional', 'Personal', 'Other' ),
      dict( defaultValue = 'Professional' ),
  )

  def __init__( self, **kwargs ):
    HasSignature.__init__( self )
    self.initializeSignatureAttributes( **kwargs )


  def __str__( self ):
    return repr( self.what ) + ' (' + self.category + ') ' + str( self.when )


a = Appointment()
appGUI = ApplicationQt3GUI()
