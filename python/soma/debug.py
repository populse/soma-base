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

'''
Utility classes and functions for debugging.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import sys
from soma.functiontools import getArgumentsSpecification
from soma.undefined import Undefined
from pprint import pprint

def functionCallInfo( frame=None ):
  '''
  Return a dictionary that gives information about a frame corresponding to a function call.
  The directory contains the following items:
    'function': name of the function called
    'filename': name of the python file containing the function
    'lineno': line number executed in 'filename'
    'arguments': arguments passed to the function. It is a list containing pairs of 
                 (argument name, argument value).
  '''
  try:
    if frame is None:
      frame = sys._getframe( 1 )
    result = { 
      'function': frame.f_code.co_name,
      'lineno': frame.f_lineno,
      'filename': frame.f_code.co_filename,
    }
    c = frame.f_code.co_name
    args = frame.f_code.co_varnames[:frame.f_code.co_argcount]
    result[ 'arguments' ] = [( p, frame.f_locals.get( p, frame.f_globals.get( p, Undefined ) ) ) for p in args]
  finally:
    del frame
  return result


def stackCallsInfo( frame=None ):
  '''
  Return a list containing functionCallInfo(frame) for all frame in the stack.
  '''
  try:
    if frame is None:
      frame = sys._getframe( 1 )
    result = []
    while frame is not None:
      result.insert( 0, functionCallInfo( frame ) )
      frame = frame.f_back
    return result
  finally:
    del frame


def print_stack( file=sys.stdout, frame=None ):
  '''
  Print information about the stack, including argument passed to functions called.
  '''
  try:
    if frame is None:
      frame = sys._getframe( 1 )
    for info in stackCallsInfo( frame ):
      print >> file, 'File "%(filename)s", line %(lineno)d' % info + ' in ' + info[ 'function' ]
      for n, v in info['arguments']:
        file.write( '   ' + n + ' = ' )
        pprint( v, file, 3 )
    file.flush()
  finally:
    del frame
