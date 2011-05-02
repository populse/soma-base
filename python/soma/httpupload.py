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
This module contains classes used to upload files using http protocol.
Http upload is processed as follow :
  - xml fragment header is uploaded. It is a file field that contains xml document formatted as follow :

  .. code-block:: xml

    <fragment>
      <filename>filename</filename>
      <filelength>4096</filelength>
      <offset>2048</offset>
      <length>1024</length>
      <sha1>f3862f40fc63c739618dace578da3607c6ac1847</sha1>
    </fragment>
    
  - if the fragment containing data already exists on the server, it is not necessary to upload it again,
    otherwise the data for the fragment must be uploaded. To check that data exists on the server and that
    data integrity is correct, the sha1 key is used.

  - after each fragment upload (header or data), a check is made to ensure that files are not complete.
  - if file is complete (i.e. : all the file fragments have been receive), it is added to a queue for
    being rebuilt.

- author: Nicolas Souedet
- organization: `NeuroSpin <http://www.neurospin.org>`_ and 
  `IFR 49 <http://www.ifr49.org>`_
- license: `CeCILL version 2 <http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>`_
'''
from __future__ import with_statement
__docformat__ = 'restructuredtext en'

import datetime
#import turbogears
import os
import thread
import threading
import tempfile
import sha
import signal
import string
import sys
import traceback
import gc

from threading import RLock
from Queue import Queue
from xml.dom import minidom, Node

from soma.decorators import synchronized
from soma.uuid import Uuid
from soma.enum import Enum
from soma.singleton import Singleton


#def displayHttpUploadDebugInfos() :
    #print '1 - resourcemanager -> resourcelocks : ', len(resourcemanager.resourcelocks)
    #print '                    -> builders : ', len(resourcemanager.builders)
    #print '2 - filebuilderinfomanager -> filebuilderinfos : ', len(FileBuilderInfoManager().filebuilderinfos)
    #print '                           -> queue : ', FileBuilderInfoManager().queue.qsize()
    
    #try :
        ## Try to get more debug information
        #import objgraph
        #print '3 - objgraph -> filebuilderinfos : ', objgraph.count('FileBuilderInfo')
        #print '             -> filefragments', objgraph.count('FileFragment')
    #except Exception, e :
        #pass
    
def displayFileBuilderInfos():
  '''
    Display current registered :py:class:`FileBuilderInfo`s.
  '''
  for filebuilderinfo in FileBuilderInfoManager().filebuilderinfos.itervalues() :
    print filebuilderinfo

def checkSha1( content, sha1 ) :
  '''
    Check that a string content matches a particular SHA-1 key.
    
    - content: string
    
      content to check.
    
    - sha1: string
    
      sha1 key to check.
    
    - returns: True if the content matches the sha1 key, False otherwise.
  '''
  digest = sha.new( content )
  return ( digest.hexdigest() == sha1 )
  
@synchronized
def checkDirectory( directory ) :
  '''
  Creates the needed directories
  '''
  if not os.path.exists( directory ) :
    os.makedirs( os.path.realpath( directory ) )

def getDirectoryFilesSize( directory ) :
  '''
  getDirectoryFilesSize
  '''
  result = 0
  
  for root, dirs, files in os.walk( directory ):
    result += sum(os.lstat( os.path.join(root, name) )[6] for name in files )

  return result
  
def getDirectoryFilesCount( directory ) :
  '''
  getDirectoryFilesCount
  '''
  result = 0
  
  for root, dirs, files in os.walk( directory ):
    result += len( files )

  return result

def walkTree( node ):
  '''
    Walk trough an xml tree node.
    
    - node: Node
    
      xml tree node to go trough.
    
    - returns: Generator to walk the xml tree node.
  '''
  if (node.nodeType == Node.ELEMENT_NODE) :
    yield node
    for child in node.childNodes:
      for n1 in walkTree(child):
        yield n1

def showNode( node, showattributes = False ):
  '''
    Get xml node content as string value.
    
    - node: Node
    
      xml node to go trough.
    
    - showattributes: bool
    
      specify if attributes must be shown.
    
    - returns: *string* containing the result of the node display.
  '''
  content = []

  if showattributes :
    # Write out the attributes.
    attrs = node.attributes
    content.append( attrs.values() )

  # Walk over any text nodes in the current node.
  for child in node.childNodes:
    if ((child.nodeType == Node.TEXT_NODE) or (child.nodeType == Node.CDATA_SECTION_NODE)) :
      content.append( child.nodeValue )

  return string.join( content )

def getTextValue( node ) :
  '''
    Recursively get xml node text content as string value.
    
    - node: Node
    
      xml node to go trough.
    
    - returns: *string* containing the result of the node as text value.
  '''
  output = ''
  for currentnode in walkTree( node ):
    nodetext = showNode( currentnode )

    if len(output) > 0 and len(nodetext) > 0 :
      output += '\n' + nodetext
    elif len(nodetext) > 0 :
      output = nodetext

  return output

def getUploadResponseDocument( upload ) :
  '''
    Create xml upload response document.
    
    - upload: bool
    
      specify if the data upload must be done or not.
    
    - returns: xml document containing the response.
  '''

  document = minidom.Document()
  node = document.createElement( 'fragment' )
  node.setAttribute( 'upload', unicode( upload ) )
  document.appendChild( node )

  return document

def getFileBuildLengthResponseDocument( filelength ) :
  '''
    Create xml file build length response document.
    
    - filelength: long
    
      specify the file upload build length.
    
    - returns: xml document containing the response.
  '''

  document = minidom.Document()
  node = document.createElement( 'file' )
  node.setAttribute( 'buildlength', unicode( filelength ) )
  document.appendChild( node )

  return document

def getFileBuildCountResponseDocument( buildcount ) :
  '''
    Create xml file build count response document.
    
    - filelength: long
    
      specify the file upload build count.
    
    - returns: xml document containing the response.
  '''

  document = minidom.Document()
  node = document.createElement( 'uploadtask' )
  node.setAttribute( 'buildcount', unicode( buildcount ) )
  document.appendChild( node )

  return document

def processHttpUploadQuery( *args, **kwargs ) :
  '''
    Main httpupload function entry. It processes arguments and
    saves uploaded file on the server using it.
    
    - returns: *string* containing the response.
  '''
  result = ''

  if 'file' in kwargs :
    # Get parsed fields from the current http request
    file = kwargs[ 'file' ]
    isheader = ( ( 'isheader' in kwargs ) and bool( kwargs[ 'isheader' ] ) )

    # Process the file header or data from the http request
    result = resourcemanager.processFileStorage( file, isheader )

  elif 'query' in kwargs :
    if kwargs.get( 'query' ) == 'getuploadbuildcount' :
      result = resourcemanager.getUploadBuildCount( kwargs['uploadid'] )
    else :
      # return an empty string
      #result = resourcemanager.getFileBuildLength( kwargs['uploadid'], kwargs['basedirectory'], kwargs['filename'], kwargs['filelength'] )
      result = resourcemanager.getUploadBuildLength( kwargs['uploadid'] )
  
  return result

LogLevel = Enum( 'NONE',
                 'ERROR',
                 'WARNING',
                 'INFO',
                 'DEBUG' )
'''LogLevel'''

class LogManager( Singleton ) :
  '''LogManager
  '''
  
  def __singleton_init__( self ):
    super( LogManager, self ).__init__()
    
    self._loglock = RLock()
    self._startdate = datetime.datetime.now()
    self._initialized = False

  @synchronized
  def setLogLevel( self, level ):
    '''
    Set log level from configuration file.
    '''
    self._loglevel = level
    
  def logReset( self ):
    '''
    Get log reset from configuration file.
    '''
    return turbogears.config.get( 'httpupload.logreset', True )
  
  def logLevel( self ):
    '''
    Get log level from configuration file.
    '''
    if not hasattr( self, '_loglevel' ) :
      value = turbogears.config.get( 'httpupload.loglevel' )
      result = LogLevel.__dict__.get( value, LogLevel.INFO )
      self.setLogLevel( result )
    else :
      result = self._loglevel
    return result

  def logFile( self ):
    '''
    Get log file from configuration file.
    '''
    value = turbogears.config.get( 'httpupload.logfile', '/var/log/serverpack/httpupload/httpupload_%(startdate)s.log' )
    value = os.path.expandvars( value )
    return value % { 'startdate' : self._startdate.isoformat() }
  
  def writeLogInfo( self, value, filepath = None, mode = 'a+b', level = LogLevel.INFO ):
    '''writeLogInfo'''

    if not self._initialized :
      self._initialized = True
      if self.logReset() :
        mode = 'w+b'
      
      
    if filepath is None :
      filepath = self.logFile()
      
    if level <= self.logLevel() :
      try :      
        self.write( '%s %s %s : %s [ %s ]\n' %
                    ( datetime.datetime.now().isoformat(' '),
                      self.__module__,
                      level,
                      value,
                      threading.currentThread().getName() ),
                  filepath,
                  mode )
      except Exception, error :
        if ( self.loglevel() != LogLevel.NONE ) :
          print 'Log was desactivated due to errors. %s. %s' % (error, traceback.format_exc() )
          
          # Desactivate log level for write
          self.setLogLevel( LogLevel.NONE )
    
  def write( self, value, filepath, mode ):
    '''write'''
    checkDirectory( os.path.dirname( filepath ) )
    with self._loglock :
      file = open( filepath, mode )
      file.write( value )
      file.close()

logmanager = LogManager()
    
#------------------------------------------------------------------------------
class ResourceManager( Singleton ) :
  '''
  Register the resources directories and manages concurrent resource
  accesses using locks.
  '''
  defaultdirectories = { 'httpupload.dirtempfilefragments' : os.path.join( tempfile.gettempdir(), 'uploaddata' ),
                         'httpupload.dirbasefileoutput' : os.path.join( tempfile.gettempdir(), 'database' ) }
  
  def __singleton_init__( self ):
    super( ResourceManager, self ).__init__()

    self.resourcelocks = dict()
    self.builders = list()

  @synchronized
  def startFileBuilders( self, count = None ) :
    '''
      Start builder threads. These threads will reconstruct files when upload is complete.
      
      - count: integer
      
        number of :py:class:`FileBuilder` threads to start.
    '''
    if count is None :
      count = int(turbogears.config.get( 'httpupload.threadcount', '4' ))
      
    if len( self.builders ) == 0 :
      logmanager.writeLogInfo( 'Module started' )
            
      for x in xrange ( count ):
        builder = FileBuilder()
        self.builders.append( builder )
        builder.setDaemon( True )
        builder.start()

      logmanager.writeLogInfo( '%s file builders started' % (count, ), level = LogLevel.DEBUG )

  @synchronized
  def stopFileBuilders( self ) :
    '''
      Stop builder threads.
    '''
    while ( len( self.builders ) > 0 ):
      builder = self.builders.pop()
      builder.shutdown()   

  def getDirectory( self, key ) :
    '''
    Get the managed directories
    
    - returns: managed directory list.
    '''
    result = None
    defaultvalue = None
    
    if key in self.defaultdirectories :
      defaultvalue = self.defaultdirectories[ key ]

    result = turbogears.config.get( key, defaultvalue )
    result = os.path.expandvars( result )
    checkDirectory( result )
    return result

  @synchronized
  def getResourceLock( self, resourcekey ) :
    '''
    Get a new resource lock if not already exists,
    otherwise get the existing one.
    
    - resourcekey: string
    
      resource key to get lock for.
    
    - returns: resource lock.
    '''
    if resourcekey in self.resourcelocks :
      resourcelock = self.resourcelocks[ resourcekey ]
    else :
      resourcelock = RLock()
      self.resourcelocks[ resourcekey ] = resourcelock

    return resourcelock

  @synchronized
  def deleteResourceLock( self, resourcekey ) :
    '''
    Delete resource lock if exists,
    
    - resourcekey: string
    
      resource key to delete lock for.
    
    - returns: resource lock.
    '''
    if resourcekey in self.resourcelocks :
      del self.resourcelocks[ resourcekey ]
    
  @synchronized
  def getObjectLock( self, value ) :
    '''
    Get the :py:class:`threading.RLock` for the object.
    
    - value: oject
    
      object to get :py:class:`threading.RLock` for.
    
    - returns: :py:class:`threading.RLock` for the object.
    '''
    objectlock = getattr( value, '__objectlock', None )
    if objectlock is None :
      objectlock = RLock()
      setattr( value, '__objectlock', objectlock )

    return objectlock
  
  def getResultUploadDirectory( self, uploadid ) :
    '''
    Get upload directory path for an upload id.
    
    - uploadid : string
    
      upload id.
    
    - returns: *string* containing the upload directory path.
    '''
    dirbasefileoutput = self.getDirectory( 'httpupload.dirbasefileoutput' )
    return os.path.realpath( os.path.join( dirbasefileoutput, uploadid ) )
    
  def getResultDirectory( self, uploadid, basedirectory ) :
    '''
    Get result directory path of the file to rebuild.
    
    - uploadid : string
    
      upload id.
    
    - basedirectory : string
    
      relative base directory path.
    
    - returns: *string* containing the result directory path.
    '''
    uploaddirectory = self.getResultUploadDirectory( uploadid )
    return os.path.realpath( os.path.join( uploaddirectory, basedirectory ) )
  
  @staticmethod
  def getResultFileName( filename, filelength ) :
    '''
    Get result file name for the file name and length. i.e. the name of the file to rebuild.
    
    - filename : string
    
      file name.
    
    - filelength : long
    
      file length.
    
    - returns: *string* containing the result file name.
    '''
    #return string.join( [ filename, unicode( filelength ) ] , '_' )
    return filename

  def processFileStorage( self, filestorage, isheader ) :
    '''
    Process a :py:class:`cgi.FileStorage` field of an http request to get file fragment information.
    
    - filestorage: :py:class:`cgi.FileStorage`
    
      cgi.FileStorage field of an http request to get file fragment information.
      It can contain either header information or data.
    
    - isheader: bool
    
      specify if the filestorage contains header information or data.
    '''

    # First we check that some file builders have been started, if not we start some.
    self.startFileBuilders()
    
    if isheader :
      if len(filestorage.value) > 0 :
        mustuploaddata = False
        
        # Create filefragment for the header
        filefragment = FileFragment( filestorage )
        filebuilderinfo = filebuilderinfomanager.getFileBuilderInfo( filefragment.getUploadId(),
                                                                    filefragment.getBaseDirectory(),
                                                                    filefragment.getFileName(),
                                                                    filefragment.getFileLength() )
        filebuilderinfo.addFileFragment( filefragment )
        
        # Check that the file fragment has not been already uploaded
        isdatafilefragmentvalid = filefragment.hasValidLocalData()
        isresultfilevalid = filebuilderinfo.checkResultFile()

        if not isresultfilevalid :
          # Result file is not valid locally
          
          if not isdatafilefragmentvalid :
            # In that case data for file fragment must be uploaded
            mustuploaddata = True
          else :
            # Check file build availability
            filebuilderinfo.checkFileBuild()
      else :
        # An error occured so that we are not able to know if the fragment must be uploaded again
        mustuploaddata = None

      # Data part must be transfered only when data is missing and resulting file does not exists
      result = getUploadResponseDocument( mustuploaddata )

    else :
      filename = filestorage.filename
      isdatafilefragmentvalid = checkSha1( filestorage.value, filename )
      if isdatafilefragmentvalid :
        filebuilderinfos = filebuilderinfomanager.getFileBuilderInfosFromKey( filename )

        for filebuilderinfo in filebuilderinfos :
          filefragment = filebuilderinfo.getFileFragment( filename )

          # Write data to disk taking care of multithread concurrent accesses
          filefragment.writeLocalData( filestorage )

          # Check file build availability
          filebuilderinfo.checkFileBuild()

      result = getUploadResponseDocument( not isdatafilefragmentvalid )

    return result.toxml()

  def getUploadBuildLength( self, uploadid ) :
    '''
    Get the length of built files for an upload.
    
    - uploadid : string
    
      upload id.
    '''
    directory = self.getResultUploadDirectory( uploadid )

    if ( os.path.exists( directory ) ) :
      processedfilesize = getDirectoryFilesSize( directory )
    else :
      processedfilesize = 0
     
    result = getFileBuildLengthResponseDocument( processedfilesize )
    
    return result.toxml()


  def getUploadBuildCount( self, uploadid ) :
    '''
    Get the count of built files for an upload.
    
    - uploadid : string
    
      upload id.
    '''
    directory = self.getResultUploadDirectory( uploadid )

    if ( os.path.exists( directory ) ) :
      processedfilecount = getDirectoryFilesCount( directory )
    else :
      processedfilecount = 0

    result = getFileBuildCountResponseDocument( processedfilecount )
    return result.toxml()
    
    
  def getFileBuildLength( self, uploadid, basedirectory, filename, filelength ) :
    '''
    Get the status for a file information.
    
    - uploadid : string
    
      upload id.
    
    - basedirectory : string
    
      relative directory path.
    
    - filename : string
    
      file name.
    
    - filelength : long
    
      file length.
    '''
    resultfilename = self.getResultFileName( filename, filelength )
    directory = self.getResultDirectory( uploadid, basedirectory )
    resultfilepath = os.path.realpath( os.path.join( directory, resultfilename ) )

    if ( os.path.exists( resultfilepath ) ) :
      processedfilesize = os.path.getsize( resultfilepath )
    else :
      processedfilesize = 0
     
    result = getFileBuildLengthResponseDocument( processedfilesize )
    
    return result.toxml()
      
resourcemanager = ResourceManager()

#------------------------------------------------------------------------------
class FileBuilder( threading.Thread ) :
  '''
  Builder :py:class:`threading.Thread` for files that were uploaded by fragments.
  '''

  def __init__(self):
    #threading.Thread.__init__(self)
    super( FileBuilder, self ).__init__()
    
    self._finished = threading.Event()
    self._interval = 1.0

  def setInterval( self, interval ):
    '''
    Set the number of seconds we sleep between executing our task
    '''
    self._interval = interval

  def shutdown( self ):
    '''
    Stop this thread
    '''
    self._finished.set()

  def run(self):
    '''run'''
    
    while 1:
        
      if self._finished.isSet():
        return
      
      # Get a file builder info out of the queue
      filebuilderinfo = filebuilderinfomanager.getQueue().get()

      # Check if we actually have filebuilderinfo to rebuild file
      if filebuilderinfo != None:

        # Build result file
        filebuilderinfo.buildResultFile()

        # Remove file builder info
        filebuilderinfomanager.removeFileBuilderInfo( filebuilderinfo )
        
        del filebuilderinfo

        # Force garbage collection
        gc.collect()

      # sleep for interval or until shutdown
      self._finished.wait( self._interval )

#------------------------------------------------------------------------------
class FileBuilderInfoManager( Singleton ) :
  '''
  Class to manage :py:class:`FileBuilderInfo`.
  '''

  def __singleton_init__( self ):
    super( FileBuilderInfoManager, self ).__init__()
    
    self.filebuilderinfos = dict()
    self.queue = Queue()

  def getFileBuilderInfo( self, uploadid, basedirectory, filename, filelength, new = True, default = None ) :
    '''
    Get a :py:class:`FileBuilderInfo` using its file name and file length. If the :py:class:`FileBuilderInfo` does not exist yet, it is added.
    
    - uploadid : string
    
      file name.
    
    - basedirectory : string
    
      base directory.
    
    - filename : string
    
      file name.
    
    - filelength : long
    
      file length.
    
    - new : boolean

      specify to add a new :py:class:`FileBuilderInfo` if None exists for the 
      file name and length.
    
    - default : object
      
      default value if None exists for the file name and length. This value is 
      used only if the 'new' parameter is set to False.
    
    - returns: the matching :py:class:`FileBuilderInfo`.
    '''
    
    # Get the file builder info from file fragment
    filehash = FileBuilderInfo.getHash( uploadid, basedirectory, filename, filelength )

    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      if filehash in self.filebuilderinfos :
        result = self.filebuilderinfos[ filehash ]
      elif new :
        result = FileBuilderInfo( uploadid, basedirectory, filename, filelength )
        self.filebuilderinfos[ filehash ] = result
      else :
        result = default

    return result

  def getFileBuilderInfosFromKey( self, filefragmentsha1 ) :
    '''
    Get a :py:class:`FileBuilderInfo` list using the sha1 key of 
    :py:class:`FileFragment`.
    It retrieves all :py:class:`FileBuilderInfo` that contains a 
    :py:class:`FileFragment` with the matching sha1 key.
    
    -  filefragmentsha1 : string
    
      sha1 key for the :py:class:`FileFragment`.
    
    - returns: the matching :py:class:`FileBuilderInfo` list.
    '''
    result = list()

    # Get the file builder info from fragment key
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      # This prevent changes to the dictionary during iteration
      for filebuilderinfo in self.filebuilderinfos.itervalues() :
        filefragment = filebuilderinfo.getFileFragment( filefragmentsha1 )

        if ( filefragment is not None ) :
          result.append( filebuilderinfo )

    return result

  def getQueue( self ) :
    '''
    Get the :py:class:`Queue.Queue` that is used to put 
    :py:class:`FileBuilderInfo` once they are complete.
    
    - returns: the :py:class:`Queue.Queue` that is used to put 
      :py:class:`FileBuilderInfo` once they are complete.
    '''
    return self.queue

  def transferToQueue( self, filebuilderinfo ) :
    '''
    Transfer a :py:class:`FileBuilderInfo` to the :py:class:`Queue.Queue`.
    
    -  filename : FileBuilderInfo
    
      :py:class:`FileBuilderInfo` to put in :py:class:`Queue.Queue`.
    '''
    filebuilderinfo.addToQueue( self.queue )

  @synchronized
  def removeFileBuilderInfo( self, filebuilderinfo ) :
    '''
    Remove a :py:class:`FileBuilderInfo` from the *dict* of managed ones.
    
    - filename : FileBuilderInfo
    
      :py:class:`FileBuilderInfo` to remove from the *dict* of managed ones.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
    
      if filebuilderinfo.getFileHash() in self.filebuilderinfos :
        self.filebuilderinfos.pop( filebuilderinfo.getFileHash() )

      # Remove unused fragments local data
      locks = list()

      for info in self.filebuilderinfos.values() :
        # Add a lock for each file builder info in order that they can not be modified
        lock = resourcemanager.getObjectLock( info )
        locks.append( lock )
        lock.acquire()
      
      for filefragment in filebuilderinfo.getFileFragments().values() :
        filebuilderinfos = self.getFileBuilderInfosFromKey( filefragment.getSha1() )

        if len(filebuilderinfos) == 0 :
          # No file builder info uses file fragment local data anymore so we can delete it
          filefragment.deleteLocalData()

      for lock in locks :
        # Release locks
        lock.release()

filebuilderinfomanager = FileBuilderInfoManager()
'''filebuilderinfomanager'''

#------------------------------------------------------------------------------
FileBuilderInfoStatus = Enum( 'BUILDING',
                              'BUILT',
                              'NOT_BUILT' )
'''FileBuilderInfoStatus'''
                              
class FileBuilderInfo(object) :
  '''
  Class to get info about uploaded file.
  '''
      
  def __init__( self, uploadid, basedirectory, filename, filelength ) :
    '''
    Initialize :py:class:`FileBuilderInfo` using its file name and file length.
    
    - uploadid : string
    
      unique identifier for the upload.
    
    - basedirectory : string
    
      relative base directory.
    
    - filename : string
    
      file name.
    
    - filelength : long
    
      file length.
    '''
    super(FileBuilderInfo, self).__init__()
    
    self.status = FileBuilderInfoStatus.NOT_BUILT
    self.uploadid = uploadid
    self.basedirectory = basedirectory
    self.filename = filename
    self.filelength = filelength
    self.filefragments = dict()

  def checkFileFragment( self, filefragment ) :
    '''
    Check that :py:class:`FileFragment` matches the file to which it belongs.
    
    - filefragment : :py:class:`FileFragment`
    
      :py:class:`FileFragment` to check that it belongs current :py:class:`FileBuilderInfo`.
    
    - returns: True if the :py:class:`FileFragment` belongs to the :py:class:`FileBuilderInfo`, False otherwise.
    '''
    return ( ( filefragment.getUploadId() == self.uploadid ) and ( filefragment.getFileName() == self.filename ) and ( filefragment.getFileLength() == self.filelength ) )

  def addToQueue( self, queue ):
    '''
    Add :py:class:`FileBuilderInfo` to the :py:class:`queue.Queue` if not already added.
    
    -  queue : :py:class:`queue.Queue`
    
      :py:class:`queue.Queue` to add :py:class:`FileBuilderInfo` to.
    '''
    if self.status == FileBuilderInfoStatus.NOT_BUILT :
      self.status = FileBuilderInfoStatus.BUILDING
      queue.put( self )
      loginfopath = os.path.join( self.uploadid, self.basedirectory, self.getResultFileName() )
      logmanager.writeLogInfo( 'Queued \'%s\'' % ( loginfopath, ) )

  def checkFileBuild( self ) :
    '''
    Check if the current :py:class:`FileBuilderInfo` is complete and contains 
    all needed information to be rebuilt. If it is the case, the current 
    :py:class:`FileBuilderInfo` is transfered to the queue
    of :py:class:`FileBuilderInfo` to be rebuilt.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      if ( self.checkFileIntegrity() and ( not self.checkResultFile() ) ) :
        filebuilderinfomanager.transferToQueue( self )
        return True
      else :
        return False

  def checkResultFile( self ) :
    '''
    Check that result file exists and has a rigth length.
    
    - returns: True if the result file exists with the rigth length, False otherwise.
    '''
    result = False
    filename = self.getResultFileName()
    filefragments = self.filefragments
    
    try :
      directory = self.getResultDirectory()
      filepath = os.path.realpath( os.path.join( directory, filename ) )
      
      objectlock = resourcemanager.getResourceLock( filepath )
      with objectlock :
        if os.path.exists( filepath ) :
          if ( os.path.getsize( filepath ) == self.getFileLength() ) :
            result = True
      resourcemanager.deleteResourceLock( filepath )
      
    except Exception, error :
      logmanager.writeLogInfo( 'Error occured checking result file. %s. %s' % (error, traceback.format_exc() ), level = LogLevel.ERROR )

    return result

  def checkFileIntegrity( self ) :
    '''
    Check that all required :py:class:`FileFragment`s exist and have the 
    correct length.
    
    - returns: True if all required :py:class:`FileFragment`s exist and have 
      the correct length, False otherwise.
    '''
    offsetcheck = 0
    fragmentlength = 0

    # Check file fragments contiguity
    for fragmentkey in sorted( self.filefragments.iterkeys() ) :
      fragment = self.filefragments[ fragmentkey ]
      fragmentoffset = fragment.getOffset()
      fragmentlength = fragment.getLength()
      if ( ( not ( offsetcheck >= fragmentoffset ) ) or ( not fragment.hasValidSizeLocalData() ) ):
        return False

      offsetcheck += fragmentlength

    return ( offsetcheck == self.filelength )

  def setStatus( self, value ):
    '''
    Set the :py:class:`FileBuilderInfo` status.
    
    - value : :py:class:`FileBuilderInfoStatus`
    
      :py:class:`FileBuilderInfoStatus` that specify if the 
      :py:class:`FileBuilderInfo` status.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      self.status = value

  def buildResultFile( self ) :
    '''
    Build a file from a :py:class:`FileBuilderInfo`. This method can not be 
    executed by multiple :py:class:`threading.Thread` simultaneously.
    
    - filebuilderinfo : FileBuilderInfo
    
      :py:class:`FileBuilderInfo` that contains all information
      about the file to rebuild (fragments, length, name).
    
    - filepath : string
    
      path of the file to rebuild.
    '''
    filename = self.getResultFileName()
    directory = self.getResultDirectory()
    loginfopath = os.path.join( self.uploadid, self.basedirectory, filename )
    
    checkDirectory( directory )

    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      try :
        filepath = os.path.realpath( os.path.join( directory, filename ) )

        # First we check file integrity
        if self.checkFileIntegrity() :

          # Check that result file has not been built by another thread
          if not self.checkResultFile() :
            filefragments = self.filefragments
            resourcelock = resourcemanager.getResourceLock( filepath )
            with resourcelock :
              file = open( filepath, "w+b" )
              for filefragmentkey in sorted( filefragments.iterkeys() ) :
                filefragment = filefragments[ filefragmentkey ]
                fragmentcontent = filefragment.readLocalData()

                if not fragmentcontent is None :
                  file.write( fragmentcontent )

              file.close()

            resourcemanager.deleteResourceLock( filepath )
            logmanager.writeLogInfo( 'Rebuilt \'%s\'' % ( loginfopath, ) )

            self.status = FileBuilderInfoStatus.BUILT

        else :
          logmanager.writeLogInfo( 'Rebuild corrupted \'%s\'' % ( loginfopath, ), level = LogLevel.WARNING )
          self.status = FileBuilderInfoStatus.NOT_BUILT
          
      except Exception, error :
        logmanager.writeLogInfo( 'Error occured building \'%s\'. %s. %s' % ( loginfopath, error, traceback.format_exc() ), level = LogLevel.ERROR )
        self.status = FileBuilderInfoStatus.NOT_BUILT

  def getFileFragments( self ) :
    '''
    Get :py:class:`FileFragment` for the current :py:class:`FileBuilderInfo`.
    
    - returns: *dict* containing the :py:class:`FileFragment`s.
    '''
    return self.filefragments

  def getFileFragment( self, filefragmentsha1 ) :
    '''
    Get :py:class:`FileFragment` using its sha1 key for the current 
    :py:class:`FileBuilderInfo`.
    
    - filefragmentsha1 : string
    
      sha1 key for the :py:class:`FileFragment`.
    
    - returns: the found :py:class:`FileFragment` or None if not found.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      for filefragment in self.filefragments.values() :
        if filefragment.sha1 == filefragmentsha1 :
          return filefragment

      return None

  def getResultFileName( self ) :
    '''
    Get result file name for the current :py:class:`FileBuilderInfo`. i.e. the 
    name of the file rebuilt.
    
    - returns: *string* containing the result file name for the current 
      :py:class:`FileBuilderInfo`.
    '''
    return resourcemanager.getResultFileName( self.getFileName(), self.getFileLength() )

  def getResultDirectory( self ) :
    '''
    Get result directory for the current :py:class:`FileBuilderInfo`. i.e. the 
    name of the directory where the file will be rebuild.
    
    - returns: *string* containing the result directory for the current 
      :py:class:`FileBuilderInfo`.
    '''
    return resourcemanager.getResultDirectory( self.getUploadId(), self.basedirectory )

  def addFileFragment( self, filefragment ) :
    '''
    Add :py:class:`FileFragment` to the current :py:class:`FileBuilderInfo`. 

    - filefragment : :py:class:`FileFragment`
    
      :py:class:`FileFragment` to add to the current 
      :py:class:`FileBuilderInfo`.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      # File fragments are ordered using their offset
      self.filefragments[ filefragment.getOffset() ] = filefragment

  def getFileName( self ):
    '''
    Get the considered file name for the current :py:class:`FileBuilderInfo`.
    
    - returns: *string* containing the considered file name for the current 
      :py:class:`FileBuilderInfo`.
    '''
    return self.filename

  def getFileLength( self ):
    '''
    Get the considered file length for the current :py:class:`FileBuilderInfo`.
    
    - returns: *long* containing the considered file length for the current 
      :py:class:`FileBuilderInfo`.
    '''
    return self.filelength

  def getUploadId( self ):
    '''
    Get the upload id for the current :py:class:`FileBuilderInfo`.
    
    - returns: *string* containing the upload id for the current 
      :py:class:`FileBuilderInfo`.
    '''
    return self.uploadid
  
  def getFileHash( self ):
    '''
    Get the considered file hash for the current :py:class:`FileBuilderInfo`.
    
    - returns: *string* containing the considered file hash for the current 
      :py:class:`FileBuilderInfo`.
    '''
    return FileBuilderInfo.getHash( self.uploadid, self.basedirectory, self.filename, self.filelength )
    
  def __str__( self ):
    '''
    Get the string current :py:class:`FileBuilderInfo`.
    
    - returns: *string* representing the current :py:class:`FileBuilderInfo`.
    '''
    result = '--> filebuilderinfo - filename : ' + self.filename + ', filebuilderinfo.filelength : ' + unicode(self.filelength) + '\n'

    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      for filefragment in self.filefragments.itervalues() :
        result += '  --> filebuilderinfo - filefragment : ' + str(filefragment) + '\n'
    return result

  @staticmethod
  def getHash( uploadid, basedirectory, filename, filelength ):
    '''
    Get the hash for a file name and length.
    
    - filename : string
    
      file name to use for creating the hash.
    
    - filename : long
    
      file length to use for creating the hash.
    
    - returns: the hash for a file name and length.
    '''
    return repr( [ basedirectory, filename, filelength, uploadid ] )


#------------------------------------------------------------------------------
class FileFragment(object) :
  '''
  Class to get file fragment information. A FileFragment correponds to a part of a file.
  '''
  header = None

  def __init__( self, headerfile ) :
    '''
    Initialize the :py:class:`FileFragment`.
    
    - headerfile : cgi.FieldStorage
    
      :py:class:`cgi.FieldStorage` from the parsed http request.
    '''
    super(FileFragment, self).__init__()
    header = minidom.parseString( headerfile.value )
    self.parseFromXml( header )

  def _checkFile( self, filepath ) :
    '''
    Check that the file exists and that the :py:class:`FileFragment` SHA-1 key 
    matches for its content.
    
    - filepath : string
    
      path of the file to check for the :py:class:`FileFragment`.
    
    - returns: True if the file exists and matches the :py:class:`FileFragment` 
      SHA-1 key, False otherwise.
    '''
    if ( ( len( filepath ) > 0 ) and os.path.exists( filepath ) ) :
      resourcelock = resourcemanager.getResourceLock( filepath )
      with resourcelock :
        # Read file content and check that sha1 key is correct
        file = open( filepath, 'r+b' )
        filecontent = file.read()

        result = checkSha1( filecontent, self.sha1 )
      resourcemanager.deleteResourceLock( filepath )
      return result

    else :
      return False

  def writeLocalData( self, datafile ) :
    '''
    Write data to a local file from :py:class:`cgi.FieldStorage`. The 
    :py:class:`cgi.FieldStorage` comes from a parsed http request.
    
    - datafile : cgi.FieldStorage
    
      :py:class:`cgi.FieldStorage` containing the data for the 
      :py:class:`FileFragment`.
    
    - returns: True if the data were written to the local file without any 
      issue, False otherwise.
    '''
    try :
      # Try to write data to the data directory
      directory = resourcemanager.getDirectory( 'httpupload.dirtempfilefragments' )
      filepath = os.path.realpath( os.path.join( directory, datafile.filename ) )
      if not self._checkFile( filepath ) :
        resourcelock = resourcemanager.getResourceLock( filepath )
        with resourcelock :
          file = open( filepath, "w+b" )
          file.write( datafile.value )
          file.close()
        
        resourcemanager.deleteResourceLock( filepath )
        
        return True

    except Exception, error :
      # If write in this directory fails we try the next directory
      logmanager.writeLogInfo( 'Error occured writing fragment data. %s. %s' % (error, traceback.format_exc() ), level = LogLevel.ERROR )

    return False
  
  def readLocalData( self ) :
    '''
    Read data for the :py:class:`FileFragment` from a local file.
    
    - returns: *string* containing the data for the :py:class:`FileFragment`.
    '''
    filepath = self.getLocalDataPath()
    
    resourcelock = resourcemanager.getResourceLock( filepath )
    with resourcelock :
      if ( len(filepath) > 0 ) :
        file = open( filepath, "r+b" )
        result = file.read()
      else :
        result = None
    
    resourcemanager.deleteResourceLock( filepath )
    return result

  def deleteLocalData( self ) :
    '''
    Delete data for the :py:class:`FileFragment` local file.
    
    - filepath : string
    
      *string* containing the file path to delete.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      try :
        filepath = self.getLocalDataPath()
        resourcelock = resourcemanager.getResourceLock( filepath )
        with resourcelock :
          if ( len(filepath) > 0 ) and os.path.exists( filepath ) :
            os.remove( filepath )
        resourcemanager.deleteResourceLock( filepath )
      except Exception, error :
        logmanager.writeLogInfo( 'Error occured deleting fragment data. %s. %s' % (error, traceback.format_exc() ), level = LogLevel.ERROR )

  def parseFromXml( self, document ) :
    '''
    Parses :py:class:`FileFragment` from an xml document.
    
    - document : xml.dom.minidom.Document
    
      :py:class:`xml.dom.minidom.Document` containing the parsed xml header for 
      the current :py:class:`FileFragment`.
    '''
    self.filename = getTextValue(document.getElementsByTagName( 'filename' ) [ 0 ])
    self.basedirectory = getTextValue(document.getElementsByTagName( 'basedirectory' ) [ 0 ])
    self.filelength = long( getTextValue(document.getElementsByTagName( 'filelength' ) [ 0 ]) )
    self.offset = long( getTextValue(document.getElementsByTagName( 'offset' ) [ 0 ]) )
    self.length = long( getTextValue(document.getElementsByTagName( 'length' ) [ 0 ]) )
    self.sha1 = getTextValue(document.getElementsByTagName( 'sha1' ) [ 0 ])
    self.uploadid = getTextValue(document.getElementsByTagName( 'uploadid' ) [ 0 ])

  def getBaseDirectory( self ):
    '''
    Get the base directory for the current :py:class:`FileFragment`.
    
    - returns: *string* containing the base directory for the current 
      :py:class:`FileFragment`.
    '''
    return self.basedirectory
  
  def getFileName( self ):
    '''
    Get the file name for the current :py:class:`FileFragment`.
    
    - returns: *string* containing the file name for the current 
      :py:class:`FileFragment`.
    '''
    return self.filename

  def getFileLength( self ):
    '''
    Get the file length for the current :py:class:`FileFragment`.
    
    - returns: *string* containing the file length for the current 
      :py:class:`FileFragment`.
    '''
    return self.filelength

  def getOffset( self ):
    '''
    Get the offset of the current :py:class:`FileFragment` (i.e. the index of 
    the first :py:class:`FileFragment` data character in the result file).
    
    - returns: *long* containing the fragment offset of the current 
      :py:class:`FileFragment`.
    '''
    return self.offset

  def getLength( self ):
    '''
    Get the length of the current :py:class:`FileFragment` (i.e. the length of 
    the :py:class:`FileFragment` data).
    
    - returns: *long* containing the length of the current 
    :py:class:`FileFragment`.
    '''
    return self.length

  def getUploadId( self ):
    '''
    Get the upload id for the current :py:class:`FileFragment`.
    
    - returns: *string* containing the upload id for the current 
      :py:class:`FileFragment`.
    '''
    return self.uploadid
  
  def getSha1( self ):
    '''
    Get the sha1 key of the current :py:class:`FileFragment` (the sha1 key is 
    used to process check sum on the :py:class:`FileFragment` data).
    
    - returns: *string* containing the sha1 key of the current 
    :py:class:`FileFragment`.
    '''
    return self.sha1

  def getLocalDataPath( self ) :
    '''
    Get a local data path for :py:class:`FileFragment`.
    
    - returns: *string* containing the local data path.
    '''
    foundfile = ''

    directory = resourcemanager.getDirectory( 'httpupload.dirtempfilefragments' )
    if os.path.exists( directory ) :
      filepath = os.path.realpath( os.path.join( directory, self.sha1 ) )
      
    return filepath

  def hasValidSizeLocalData( self ) :
    '''
    Check that the current :py:class:`FileFragment` has valid local data. 
    Checks the file existence and the size of the file.
    
    - returns: True if the current :py:class:`FileFragment` has valid local 
      data using data size, False otherwise.
    '''
    filepath = self.getLocalDataPath()
    resourcelock = resourcemanager.getResourceLock( filepath )
    with resourcelock :
      if ( len(filepath) > 0 ) and os.path.exists( filepath ) :
        result = ( os.path.getsize( filepath ) == self.getLength() )
      else :
        result = False
    resourcemanager.deleteResourceLock( filepath )
    
    return result
      
  def hasValidLocalData( self ) :
    '''
    Check that the current :py:class:`FileFragment` has valid local data. 
    Checks the file existence and sha1 key.
    
    - returns: True if the current :py:class:`FileFragment` has valid local 
      data, False otherwise.
    '''
    filepath = self.getLocalDataPath()
    return self._checkFile( filepath )

  def __str__( self ) :
    '''
    Get a *string* representing the current :py:class:`FileFragment`.
    
    - returns: *string* representing the current :py:class:`FileFragment`.
    '''
    return 'self.filename : ' + self.filename + ', self.filelength : ' + unicode(self.filelength) + ', self.offset : ' + unicode(self.offset) + ', self.length : ' + unicode(self.length) + ', self.sha1 : ' + self.sha1 + ', self.getLocalDataPath() : ' + self.getLocalDataPath()
