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
Utility classes and functions for debugging.

- author: Yann Cointepas
- organization: `NeuroSpin <http://www.neurospin.org>`_ and 
  `IFR 49 <http://www.ifr49.org>`_
- license: `CeCILL version 2 <http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>`_
'''
from __future__ import absolute_import

__docformat__ = 'restructuredtext en'

import sys
from pprint import pprint

from soma.undefined import Undefined

def function_call_info( frame=None ):
  '''
  Return a dictionary that gives information about a frame corresponding to a function call.
  The directory contains the following items:

  - 'function': name of the function called
  - 'filename': name of the python file containing the function
  - 'lineno': line number executed in 'filename'
  - 'arguments': arguments passed to the function. It is a list containing 
    pairs of (argument name, argument value).
  '''
  try:
    if frame is None:
      frame = sys._getframe( 1 )
    result = { 
      'function': frame.f_code.co_name,
      'lineno': frame.f_lineno,
      'filename': frame.f_code.co_filename,
    }
    args = frame.f_code.co_varnames[:frame.f_code.co_argcount]
    result[ 'arguments' ] = \
      [( p, frame.f_locals.get( p, frame.f_globals.get( p, Undefined ) ) ) for p in args]
  finally:
    del frame
  return result


def stack_calls_info( frame=None ):
  '''
  Return a list containing function_call_info(frame) for all frame in the stack.
  '''
  try:
    if frame is None:
      frame = sys._getframe( 1 )
    result = []
    while frame is not None:
      result.insert( 0, function_call_info( frame ) )
      frame = frame.f_back
    return result
  finally:
    del frame


def print_stack( out=sys.stdout, frame=None ):
  '''
  Print information about the stack, including argument passed to functions called.
  '''
  try:
    if frame is None:
      frame = sys._getframe( 1 )
    for info in stack_calls_info( frame ):
      print >> out, 'File "%(filename)s", line %(lineno)d' % info + ' in ' + info[ 'function' ]
      for name, value in info['arguments']:
        out.write( '   ' + name + ' = ' )
        pprint( value, out, 3 )
    out.flush()
  finally:
    del frame
