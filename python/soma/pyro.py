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
This module provides the class L{ThreadSafeProxy}.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"

import inspect, threading
import Pyro.core
from soma.thread_calls import SingleThreadCalls
from soma.functiontools import partial

class ThreadSafeProxy( object ):
  _thread = None
  
  def __init__( self, proxy ):
    '''
    This class makes it possible to share Pyro proxy across multiple threads.
    A single Pyro thread is created. This thread will be the only one to use Pyro
    proxy objects. A L{ThreadSafeProxy} is a proxy on a Pyro proxy that will send
    all activity (methods calls and attributes getting and setting) to the
    Pyro thread.
    
    Example
    -------
      import Pyro.core
      from soma.pyro import ThreadSafeProxy
      
      threadSafeProxy = ThreadSafeProxy( Pyro.core.getProxyFromURI( 'PYRO://127.0.0.1:7766/84a68da2260374b1b334d9591c4fd84f' ) )
    '''
    newProxy = self.pyroThreadCall( proxy.__class__, proxy.URI )
    object.__setattr__( self, '_proxy', newProxy )
  
  
  @staticmethod
  def _createThread():
    '''
    Internal method to create the Pyro thread if it does not exists
    '''
    if ThreadSafeProxy._thread is None:
      ThreadSafeProxy._threadCall = SingleThreadCalls()
      ThreadSafeProxy._thread = threading.Thread( target=ThreadSafeProxy._threadCall.processingLoop )
      ThreadSafeProxy._thread.setDaemon( True )
      ThreadSafeProxy._threadCall.setProcessingThread( ThreadSafeProxy._thread )
      ThreadSafeProxy._thread.start()
  
  #_dbg = 0
  @staticmethod
  def pyroThreadCall( *args, **kwargs ):
    '''
    Calls a function from the Pyro thread.
    '''
    ThreadSafeProxy._createThread()
    #n = ThreadSafeProxy._dbg
    #ThreadSafeProxy._dbg += 1
    #if isinstance( f, Pyro.core._RemoteMethod ):
      #sf = '<' + f._RemoteMethod__name + '>'
    #else:
      #sf = repr( f )
    #print '!pyroThreadCall! -->', n, sf, args, kwargs
    #result = ThreadSafeProxy._threadCall.call( f, *args, **kwargs )
    #print '!pyroThreadCall! <--', n, result
    #return result
    return ThreadSafeProxy._threadCall.call( *args, **kwargs )
  
  
  def __getattr__( self, name ):
    value = ThreadSafeProxy.pyroThreadCall( getattr, self._proxy, name )
    if isinstance( value, Pyro.core._RemoteMethod ) or inspect.ismethod( value ):
      return partial( ThreadSafeProxy.pyroThreadCall, value )
    return value


  def __setattr__( self, name, value ):
    return ThreadSafeProxy.pyroThreadCall( setattr, self._proxy, name, value )
