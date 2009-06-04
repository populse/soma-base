# -*- coding: utf-8 -*-

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
Singleton pattern.

A class deriving from C{Singleton} can have only one instance.
The first instanciation will create an object and
other instanciations return the same object. Note that the C{__init__} 
method (if any) is still called at each instanciation (on the same object).
Therefore, C{Singleton} derived class should define C{__singleton_init__} 
instead of C{__init__} because the former is only called once.
 
Usage examples :
  - Inherits from a Singleton class
  
  class A(object):
    def __init__(self):
      print "call init A"
      super(A, self).__init__()
    

  class As(Singleton, A): # As = singleton(A)
    def __singleton_init__(self):
      print "call singleton init As"
      A.__init__(self)

  class Asd(As): # Asd = singleton(A) derived class      
    # derived class must implement __singleton_init__ method, not __init__ method
    def __singleton_init__(self):
      print "call singleton init Asd"
      As.__singleton_init__(self)

  # it is possible to have several class which inherits from the same singleton, 
  # the singleton instance is stored in the derived class context
  class Asd2(As):
    # if __new__ is redefined, it will be called before the new in the super class
    def __new__(cls, forceNewInstance=False):
      if forceNewInstance:
        self=object.__new__(cls)
        self.__singleton_init__()
      else:
        self=super(Asd2, cls).__new__(cls)
      return self
      
    def __singleton_init__(self):
      print "call singleton init Asd2"
      As.__singleton_init__(self)
    
  a=Asd()
  a2=Asd()
  print a, a2, a is a2
  a3=Asd2()
  a4=Asd2(forceNewInstance=True)
  print a3, a4, a3 is a4
  print Asd._singleton_instance
  print Asd2._singleton_instance


@author: Dominique Geffroy
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"
import soma.notification
from soma.singleton import Singleton

class ObservableSingleton( Singleton ):
  '''
  Implements the singleton pattern and notifies when the singleton instance is created. 
  It is possible to get the current singleton instance without creating a new instance if it doesn't exist, using create constructor's parameter. By default this option is True, so an instance is created the first time the constructor is called.
  
  A class deriving from C{Singleton} can have only one instance.
  The first instanciation will create an object and
  other instanciations return the same object. Note that the C{__init__} 
  method (if any) is still called at each instanciation (on the same object).
  Therefore, C{Singleton} derived class should define C{__singleton_init__} 
  instead of C{__init__} because the former is only called once.
  
  Example::
  
    from soma.wip.singleton import ObservableSingleton
    
    class MyClass( ObservableSingleton ):
      def __singleton_init__( self, *args, **kwargs ):
        self.attribute = 'value'
    
    def onCreate():
      print "MyClass instance created"
    
    MyClass.addCreateListener(onCreate)
    o1 = MyClass(create=False)
    print o1 # o1 is None
    o1 = MyClass()
    o2 = MyClass()
    print o1 is o2
  '''
  onCreateNotifiers={}
  #soma.notification.Notifier()
  
  def __new__( cls, *args, **kwargs ):
    '''If the keyword arg create is set to False, then a new instance is
    not created event if the singleton has not been instantiated yet.
    '''
    instance=None
    create = kwargs.get( 'create', True )
    if '_singleton_instance' not in cls.__dict__:
      if create:
        instance = super(ObservableSingleton, cls).__new__( cls, *args,
          **kwargs )
        notifier = cls.onCreateNotifiers.get(str(cls))
        if notifier is not None:
          notifier.notify(instance)
    else:
      instance = cls._singleton_instance
    return instance

  def addCreateListener(cls, listener):
    className=str(cls)
    notifier=cls.onCreateNotifiers.get(className)
    if notifier is None:
      notifier=soma.notification.Notifier()
      cls.onCreateNotifiers[className] = notifier
    notifier.add(listener)
  addCreateListener=classmethod(addCreateListener)

  def removeCreateListener(cls, listener):
    className=str(cls)
    notifier=cls.onCreateNotifiers.get(className)
    if notifier is not None:
      notifier.remove(listener)
  removeCreateListener=classmethod(removeCreateListener)

  def __init__( self, *args, **kwargs ):
    '''
    C{__init__} method of L{Singleton} derived class should do nothing. Derived
    classes must define C{__singleton_init__} instead of C{__init__}.
    '''