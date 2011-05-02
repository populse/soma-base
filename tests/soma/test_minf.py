# -*- coding: utf-8 -*-

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

from soma.minf.api import readMinf, writeMinf, createReducerAndExpander, \
                               registerClass, MinfError, iterateMinf
import os, unittest, tempfile, itertools
from cStringIO import StringIO


class TestMinf( unittest.TestCase ):
  class MyClass( object ):
    '''
    This class is used to illustrate how to write custom class
    instances in a minf file.
    '''
    
    def __init__( self, arg1, arg2, kwarg1=None, kwarg2=None ):
      '''
      The constructor takes several parameters, some of them
      have default values.
      '''
      self.arg1 = arg1
      self.arg2 = arg2
      self.kwarg1 = kwarg1
      self.kwarg2 = kwarg2
    
    
    def __getinitkwargs__( self ):
      '''
      This method return the arguments to pass to self.__init__
      to get a copy of self. It returns a tuple ( args, kwargs ) where
      args is a tuple (possibly empty) containing arguments values
      and kwargs is a dictionary (possibly empty) containing named 
      arguments values.
      '''
      kwargs = {}
      if self.kwarg1 is not None:
        kwargs[ 'kwarg1' ] = self.kwarg1
      if self.kwarg2 is not None:
        kwargs[ 'kwarg2' ] = self.kwarg2
      return ( ( self.arg1, self.arg2 ), kwargs )
  
  
    def __eq__( self, other ):
      '''
      Print instances as they have been defined. For instance: 'MyClass( 1, 2, kwarg2=3 )'
      '''
      if isinstance( other, TestMinf.MyClass ):
        return self.__dict__ == other.__dict__
      return False
    
    
    def __repr__( self ):
      '''
      Print instances as they have been defined. For instance: 'MyClass( 1, 2, kwarg2=3 )'
      '''
      args, kwargs = self.__getinitkwargs__()
      result = 'MyClass('
      if args or kwargs:
        result += ' ' + \
          ', '.join( ( ', '.join( (repr(i) for i in args) ),
                      ', '.join( (n+'='+repr(v) for n,v in kwargs.iteritems()) ) ) ) + \
          ' '
      result += ')'
      return result
  
  
    def __hash__( self ):
      '''
      Defining this method is a trick to allow to make two different
      instances of MyClass being identical when used as dictionary key
      as long as they have the same content. It allows to use operator
      == on two dictionaries that have MyClass instance as key, in that
      case the keys are compared by their contents (instead of their
      addresses if __hash__ was not defined).
      '''
      return hash( tuple( self.__dict__.iteritems() ) )
  
  
  def setUp( self ):
    createReducerAndExpander( 'example_1.0', 'minf_2.0' )
    registerClass( 'example_1.0', TestMinf.MyClass, 'MyClass' )
    self.minfSample = '<?xml version="1.0" encoding="utf-8" ?>\n' \
      '<minf expander="example_1.0">\n' \
      '<none/>\n' \
      '<false/>\n' \
      '<true/>\n' \
      '<n>1234</n>\n' \
      '<n>-12.34</n>\n' \
      '<s>a string</s>\n' \
      '<s>h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '<l>\n' \
      '  <none/>\n' \
      '  <false/>\n' \
      '  <true/>\n' \
      '  <n>1234</n>\n' \
      '  <n>-12.34</n>\n' \
      '  <s>a string</s>\n' \
      '  <s>h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '  <l length="7">\n' \
      '    <none/>\n' \
      '    <false/>\n' \
      '    <true/>\n' \
      '    <n>1234</n>\n' \
      '    <n>-12.34</n>\n' \
      '    <s>a string</s>\n' \
      '    <s>h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '  </l>\n' \
      '  <d length="8">\n' \
      '    <none name="None"/>\n' \
      '    <false name="False"/>\n' \
      '    <true name="True"/>\n' \
      '    <n name="integer">1234</n>\n' \
      '    <s name="string">a string</s>\n' \
      '    <s name="unicode">h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '    <s name="h\xc3\xa9h\xc3\xa9 !">unicode</s>\n' \
      '    <l length="7">\n' \
      '      <none/>\n' \
      '      <false/>\n' \
      '      <true/>\n' \
      '      <n>1234</n>\n' \
      '      <n>-12.34</n>\n' \
      '      <s>a string</s>\n' \
      '      <s>h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '    </l>\n' \
      '    <d>\n' \
      '      \n' \
      '    </d>\n' \
      '  </d>\n' \
      '</l>\n' \
      '<d>\n' \
      '  <none name="None"/>\n' \
      '  <false name="False"/>\n' \
      '  <true name="True"/>\n' \
      '  <n name="integer">1234</n>\n' \
      '  <s name="string">a string</s>\n' \
      '  <s name="unicode">h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '  <l length="7" name="list">\n' \
      '    <none/>\n' \
      '    <false/>\n' \
      '    <true/>\n' \
      '    <n>1234</n>\n' \
      '    <n>-12.34</n>\n' \
      '    <s>a string</s>\n' \
      '    <s>h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '  </l>\n' \
      '  <f type="MyClass" name="object">\n' \
      '    <n>1</n>\n' \
      '    <n>2</n>\n' \
      '    <n name="kwarg2">3</n>\n' \
      '  </f>\n' \
      '  \n' \
      '  <none/>\n' \
      '  <s>None</s>\n' \
      '  <false/>\n' \
      '  <s>False</s>\n' \
      '  <true/>\n' \
      '  <s>True</s>\n' \
      '  <n>1234</n>\n' \
      '  <s>integer</s>\n' \
      '  <n>12.34</n>\n' \
      '  <s>float</s>\n' \
      '  <l length="7">\n' \
      '    <none/>\n' \
      '    <false/>\n' \
      '    <true/>\n' \
      '    <n>1234</n>\n' \
      '    <n>-12.34</n>\n' \
      '    <s>a string</s>\n' \
      '    <s>h\xc3\xa9h\xc3\xa9 !</s>\n' \
      '  </l>\n' \
      '  <s>list</s>\n' \
      '  <f type="MyClass">\n' \
      '    <n>1</n>\n' \
      '    <n>2</n>\n' \
      '    <n name="kwarg2">3</n>\n' \
      '  </f>\n' \
      '  <s>object</s>\n' \
      '</d>\n' \
      '<f type="MyClass">\n' \
      '  <n>1</n>\n' \
      '  <n name="kwarg2">3</n>\n' \
      '  <n name="arg2">2</n>\n' \
      '</f>\n' \
      '</minf>\n'
    self.minfSampleContent = (None,
      False,
      True,
      1234,
      -12.34,
      u'a string',
      u'h\xe9h\xe9 !',
      [None,
        False,
        True,
        1234,
        -12.34,
        u'a string',
        u'h\xe9h\xe9 !',
        [None, False, True, 1234, -12.34, u'a string', u'h\xe9h\xe9 !'],
        {(None, False, True, 1234, -12.34, u'a string', u'h\xe9h\xe9 !'): {},
        u'False': False,
        u'None': None,
        u'True': True,
        u'h\xe9h\xe9 !': u'unicode',
        u'integer': 1234,
        u'string': u'a string',
        u'unicode': u'h\xe9h\xe9 !'}],
      {None: u'None',
        False: u'False',
        True: u'True',
        12.34: u'float',
        1234: u'integer',
        TestMinf.MyClass( 1, 2, kwarg2=3 ): u'object',
        (None, False, True, 1234, -12.34, u'a string', u'h\xe9h\xe9 !'): u'list',
        u'False': False,
        u'None': None,
        u'True': True,
        u'integer': 1234,
        u'list': [None, False, True, 1234, -12.34, u'a string', u'h\xe9h\xe9 !'],
        u'object': TestMinf.MyClass( 1, 2, kwarg2=3 ),
        u'string': u'a string',
        u'unicode': u'h\xe9h\xe9 !'},
      TestMinf.MyClass( 1, 2, kwarg2=3 ) )
    self.temporaryFileName = tempfile.mkstemp()[ 1 ]
  
  
  def tearDown( self ):
    if os.path.exists( self.temporaryFileName ):
      os.remove( self.temporaryFileName  )
  
  
  def testReadExistingMinfXML( self ):
    '''
    Check that reading a minf sample always gives the same result.
    '''
    self.assertEqual( readMinf( StringIO( self.minfSample ) ), self.minfSampleContent )
  
  
  def testWriteAndReadMinfXML( self ):
    '''
    Check that writing and reading minf file behave as expected.
    '''
    unicodeValue = unicode( 'h\xc3\xa9h\xc3\xa9 !', 'utf-8' )
    tupleValue = ( None, False, True, 1234, -12.34, 'a string', unicodeValue )
    expectedTupleValue = [ None, False, True, 1234, -12.34, u'a string', unicodeValue ]
    tupleValue = tupleValue + ( tupleValue, list( tupleValue ) )
    expectedTupleValue = expectedTupleValue + [ list(expectedTupleValue), list( expectedTupleValue ) ]
    dictValue =   {
      'None': None,
      'False': False,
      'True': True,
      'integer': 1234,
      'float': -12.34,
      'string': 'a string',
      'unicode': unicodeValue,
      'tuple': tupleValue,
      'list': list( tupleValue ),
      'object': TestMinf.MyClass( 1, 2, kwarg2=3 ),
      None: 'None',
      False: 'False',
      True: 'True',
      1234: 'integer',
      12.34: 'float',
      unicodeValue: 'unicode',
      ( None, False, True, 1234, -12.34, 'a string', unicodeValue ): 'tuple',
    }
    expectedDictValue =   {
      u'None': None,
      u'False': False,
      u'True': True,
      u'integer': 1234,
      u'float': -12.34,
      u'string': u'a string',
      u'unicode': unicodeValue,
      u'tuple': expectedTupleValue,
      u'list': expectedTupleValue,
      u'object': TestMinf.MyClass( 1, 2, kwarg2=3 ),
      None: u'None',
      False: u'False',
      True: u'True',
      1234: u'integer',
      12.34: u'float',
      unicodeValue: u'unicode',
      ( None, False, True, 1234, -12.34, u'a string', unicodeValue ): u'tuple',
    }
    dictValue[ 'tuple' ] = tuple( tupleValue + ( dict( dictValue ), ) ) 
    expectedDictValue[ 'tuple' ] = expectedTupleValue + [ dict( expectedDictValue ) ]
    dictValue[ 'dictionary' ] = dict( dictValue )
    expectedDictValue[ 'dictionary' ] = dict( expectedDictValue )
      
  
    objectsWritten = tupleValue + ( dictValue, )
    expectedObjectsWritten = tuple( expectedTupleValue ) + ( expectedDictValue, )
    self.assertRaises( MinfError, writeMinf, self.temporaryFileName, objectsWritten )
    writeMinf( self.temporaryFileName, objectsWritten, reducer='example_1.0' )
    objectsRead = readMinf( self.temporaryFileName )
    self.assertEqual( objectsRead, expectedObjectsWritten )
    writeMinf( self.temporaryFileName, objectsRead, reducer='example_1.0' )
    objectsReread = readMinf( self.temporaryFileName )
    self.assertEqual( objectsReread, objectsRead )
    
    
    
    
if __name__ == '__main__':
    unittest.main()
