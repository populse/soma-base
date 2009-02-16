# -*- coding: iso-8859-1 -*-

#  This software and supporting documentation were developed by
#  NeuroSpin and IFR 49
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use,contr modify and/or redistribute the software under the
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
This module contains classes used to upload files using http protocol.
Http upload is processed as follow :
  - xml fragment header is uploaded. It is a file field that contains xml document formatted as follow :
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

@author: Nicolas Souedet
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
from __future__ import with_statement
__docformat__ = "epytext en"

import datetime
import turbogears
import os
import thread
import threading
import tempfile
import sha
import signal
import string
import sys
import traceback

from threading import RLock
from Queue import Queue
from xml.dom import minidom, Node

from soma.decorators import synchronized
from soma.uuid import Uuid
from soma.enum import Enum
from soma.singleton import Singleton

def displayFileBuilderInfos():
  '''
    Display current registered {FileBuilderInfo}s.
  '''
  for filebuilderinfo in FileBuilderInfoManager().filebuilderinfos.itervalues() :
    print filebuilderinfo

def checkSha1( content, sha1 ) :
  '''
    Check that a string content matches a particular SHA-1 key.
    @type  content: string
    @param content: content to check.
    @type  sha1: string
    @param sha1: sha1 key to check.
    @return: True if the content matches the sha1 key, False otherwise.
  '''
  digest = sha.new( content )
  return ( digest.hexdigest() == sha1 )
  
@synchronized
def checkDirectory( directory ) :
  # Creates the needed directories
  if not os.path.exists( directory ) :
    os.makedirs( os.path.realpath( directory ) )
      
def walkTree(node):
  '''
    Walk trough an xml tree node.
    @type  node: Node
    @param node: xml tree node to go trough.
    @return: Generator to walk the xml tree node.
  '''
  if (node.nodeType == Node.ELEMENT_NODE) :
    yield node
    for child in node.childNodes:
      for n1 in walkTree(child):
        yield n1

def showNode( node, showattributes = False ):
  '''
    Get xml node content as string value.
    @type  node: Node
    @param node: xml node to go trough.
    @type  showattributes: bool
    @param showattributes: specify if attributes must be shown.
    @return: L{string} containing the result of the node display.
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
    @type  node: Node
    @param node: xml node to go trough.
    @return: L{string} containing the result of the node as text value.
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
    @type  upload: bool
    @param upload: specify if the data upload must be done or not.
    @return: xml document containing the response.
  '''

  document = minidom.Document()
  node = document.createElement( 'fragment' )
  node.setAttribute( 'upload', unicode( upload ) )
  document.appendChild( node )

  return document

def getFileBuildLengthResponseDocument( filelength ) :
  '''
    Create xml file build length response document.
    @type  filelength: long
    @param filelength: specify the file upload build length.
    @return: xml document containing the response.
  '''

  document = minidom.Document()
  node = document.createElement( 'file' )
  node.setAttribute( 'buildlength', unicode( filelength ) )
  document.appendChild( node )

  return document

def processHttpUploadQuery( *args, **kwargs ) :
  '''
    Main httpupload function entry. It processes arguments and
    saves uploaded file on the server using it.
    @return: L{string} containing the response.
  '''
  result = ''

  if 'file' in kwargs :
    # Get parsed fields from the current http request
    file = kwargs[ 'file' ]
    isheader = ( ( 'isheader' in kwargs ) and bool( kwargs[ 'isheader' ] ) )

    # Process the file header or data from the http request
    result = resourcemanager.processFileStorage( file, isheader )

  elif 'query' in kwargs :
    # return an empty string
    result = resourcemanager.getFileBuildLength( kwargs['uploadid'], kwargs['basedirectory'], kwargs['filename'], kwargs['filelength'] )

  return result

LogLevel = Enum( 'NONE',
                 'ERROR',
                 'WARNING',
                 'INFO',
                 'DEBUG' )

class LogManager( Singleton ) :
  
  def __singleton_init__( self ):
    super( Singleton, self ).__init__()
    self._loglock = RLock()
    self._startdate = datetime.datetime.now()
    self._initialized = False

  def logReset( self ):
    '''
    Get log reset from configuration file.
    '''
    return turbogears.config.get( 'httpupload.logreset', True )
  
  def logLevel( self ):
    '''
    Get log level from configuration file.
    '''
    defaultvalue = LogLevel.INFO
    value = turbogears.config.get( 'httpupload.loglevel', str( defaultvalue ) )
    return getattr( LogLevel, value, defaultvalue )

  def logFile( self ):
    '''
    Get log file from configuration file.
    '''
    value = turbogears.config.get( 'httpupload.logfile', '/var/log/httpupload_%(startdate)s.log' )
    return value % { 'startdate' : self._startdate.isoformat() }
  
  def writeLogInfo( self, value, filepath = None, mode = 'a+b', level = LogLevel.INFO ):

    if not self._initialized :
      self._initialized = True
      if self.logReset() :
        mode = 'w+b'
      
      
    if filepath is None :
      filepath = self.logFile()
      
    if level <= self.logLevel() :
      self.write( '%s %s %s : %s [ %s ]\n' %
                  ( datetime.datetime.now().isoformat(' '),
                    self.__module__,
                    level,
                    value,
                    threading.currentThread().getName() ),
                filepath,
                mode )
    
  def write( self, value, filepath, mode ):
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
    super( Singleton, self ).__init__()

    self.resourcelocks = dict()
    self.builders = list()

  @synchronized
  def startFileBuilders( self, count = 4 ) :
    '''
      Start builder threads. These threads will reconstruct files when upload is complete.
      @type  count: integer
      @param count: number of L{FileBuilder} threads to start.
    '''
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
    @return: managed directory list.
    '''
    result = None
    defaultvalue = None
    
    if key in self.defaultdirectories :
      defaultvalue = self.defaultdirectories[ key ]

    result = turbogears.config.get( key, defaultvalue )
    checkDirectory( result )
    return result

  @synchronized
  def getResourceLock( self, resourcekey ) :
    '''
    Get a new resource lock if not already exists,
    otherwise get the existing one.
    @type  resourcekey: string
    @param resourcekey: resource key to get lock for.
    @return: resource lock.
    '''
    if resourcekey in self.resourcelocks :
      resourcelock = self.resourcelocks[ resourcekey ]
    else :
      resourcelock = RLock()
      self.resourcelocks[ resourcekey ] = resourcelock

    return resourcelock

  @synchronized
  def getObjectLock( self, value ) :
    '''
    Get the L{threading.RLock} for the object.
    @type  value: oject
    @param value: object to get L{threading.RLock} for.
    @return: L{threading.RLock} for the object.
    '''
    objectlock = getattr( value, '__objectlock', None )
    if objectlock is None :
      objectlock = RLock()
      setattr( value, '__objectlock', objectlock )

    return objectlock

  @staticmethod
  def getResultFileName( filename, filelength ) :
    '''
    Get result file name for the file name and length. i.e. the name of the file to rebuild.
    @type filename : string
    @param filename : file name.
    @type filelength : long
    @param filelength : file length.
    @type return : L{string} containing the result file name.
    '''
    #return string.join( [ filename, unicode( filelength ) ] , '_' )
    return filename

  @staticmethod
  def getResultDirectory( uploadid, basedirectory ) :
    '''
    Get result directory path of the file to rebuild.
    @type uploadid : string
    @param uploadid : upload id.
    @type basedirectory : string
    @param basedirectory : relative base directory path.
    @type return : L{string} containing the result directory path.
    '''
    return os.path.realpath( os.path.join( resourcemanager.getDirectory( 'httpupload.dirbasefileoutput' ), uploadid, basedirectory ) )

  def processFileStorage( self, filestorage, isheader ) :
    '''
    Process a L{cgi.FileStorage} field of an http request to get file fragment information.
    @type  filestorage: cgi.FileStorage
    @param filestorage: L{cgi.FileStorage} field of an http request to get file fragment information.
      It can contains either header information or data.
    @type  isheader: bool
    @param isheader: specify if the filestorage contains header information or data.
    '''

    # First we check that some file builders have been started, if not we start some.
    self.startFileBuilders()
    
    if isheader :
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

  def getFileBuildLength( self, uploadid, basedirectory, filename, filelength ) :
    '''
    Get the status for a file information.
    @type uploadid : string
    @param uploadid : upload id.
    @type basedirectory : string
    @param basedirectory : relative directory path.
    @type filename : string
    @param filename : file name.
    @type filelength : long
    @param filelength : file length.
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
  Builder L{threading.Thread} for files that were uploaded by fragments.
  '''

  def __init__(self):
    threading.Thread.__init__(self)
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

      # sleep for interval or until shutdown
      self._finished.wait( self._interval )

#------------------------------------------------------------------------------
class FileBuilderInfoManager( Singleton ) :
  '''
  Class to manage L{FileBuilderInfo}.
  '''

  def __singleton_init__( self ):
    super( Singleton, self ).__init__()
    
    self.filebuilderinfos = dict()
    self.queue = Queue()

  def getFileBuilderInfo( self, uploadid, basedirectory, filename, filelength, new = True, default = None ) :
    '''
    Get a L{FileBuilderInfo} using its file name and file length. If the L{FileBuilderInfo}
    does not exist yet, it is added.
    @type uploadid : string
    @param uploadid : file name.
    @type basedirectory : string
    @param basedirectory : base directory.
    @type filename : string
    @param filename : file name.
    @type filelength : long
    @param filelength : file length.
    @type new : boolean
    @param new : specify to add a new L{FileBuilderInfo} if None exists for the file name and length.
    @type default : object
    @param default : default value if None exists for the file name and length. This value is used only
                     if the 'new' parameter is set to False.
    @return : the matching L{FileBuilderInfo}.
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
    Get a L{FileBuilderInfo} list using the sha1 key of L{FileFragment}.
    It retrieves all L{FileBuilderInfo} that contains a L{FileFragment} with the matching sha1 key.
    @type filefragmentsha1 : string
    @param filefragmentsha1 : sha1 key for the L{FileFragment}.
    @return : the matching L{FileBuilderInfo} list.
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
    Get the L{Queue.Queue} that is used to put L{FileBuilderInfo} once they are complete.
    @return : the L{Queue.Queue} that is used to put L{FileBuilderInfo} once they are complete.
    '''
    return self.queue

  def transferToQueue( self, filebuilderinfo ) :
    '''
    Transfer a L{FileBuilderInfo} to the L{Queue.Queue}.
    @type filename : FileBuilderInfo
    @param filename : L{FileBuilderInfo} to put in L{Queue.Queue}.
    '''
    filebuilderinfo.addToQueue( self.queue )

  @synchronized
  def removeFileBuilderInfo( self, filebuilderinfo ) :
    '''
    Add a L{FileBuilderInfo} to the L{dict} of managed ones.
    @type filename : FileBuilderInfo
    @param filename : L{FileBuilderInfo} to add to the L{dict} of managed ones.
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

#------------------------------------------------------------------------------
FileBuilderInfoStatus = Enum( 'BUILDING',
                              'BUILT',
                              'NOT_BUILT' )
                              
class FileBuilderInfo :
  '''
  Class to get info about uploaded file.
  '''

  def __init__( self, uploadid, basedirectory, filename, filelength ) :
    '''
    Initialize L{FileBuilderInfo} using its file name and file length.
    @type uploadid : string
    @param uploadid : unique identifier for the upload.
    @type basedirectory : string
    @param basedirectory : relative base directory.
    @type filename : string
    @param filename : file name.
    @type filelength : long
    @param filelength : file length.
    '''
    self.status = FileBuilderInfoStatus.NOT_BUILT
    self.uploadid = uploadid
    self.basedirectory = basedirectory
    self.filename = filename
    self.filelength = filelength
    self.filefragments = dict()

  def checkFileFragment( self, filefragment ) :
    '''
    Check that L{FileFragment} matches the file to which it belongs.
    @type filefragment : L{FileFragment}
    @param filefragment : L{FileFragment} to check that it belongs current C{FileBuilderInfo}.
    @type return : True if the L{FileFragment} belongs to the C{FileBuilderInfo}, False otherwise.
    '''
    return ( ( filefragment.getUploadId() == self.uploadid ) and ( filefragment.getFileName() == self.filename ) and ( filefragment.getFileLength() == self.filelength ) )

  def addToQueue( self, queue ):
    '''
    Add C{FileBuilderInfo} to the L{queue.Queue} if not already added.
    @type queue : L{queue.Queue}
    @param queue : L{queue.Queue} to add C{FileBuilderInfo} to.
    '''
    if self.status == FileBuilderInfoStatus.NOT_BUILT :
      self.status = FileBuilderInfoStatus.BUILDING
      queue.put( self )
      loginfopath = os.path.join( self.uploadid, self.basedirectory, self.getResultFileName() )
      logmanager.writeLogInfo( 'Queued \'%s\'' % ( loginfopath, ) )

  def checkFileBuild( self ) :
    '''
    Check if the current C{FileBuilderInfo} is complete and contains all needed informations
    to be rebuilt. If it is the case, the current C{FileBuilderInfo} is transfered to the queue
    of C{FileBuilderInfo} to be rebuilt.
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
    @return : True if the result file exists with the rigth length, False otherwise.
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
    except Exception, error :
      logmanager.writeLogInfo( 'Error occured checking result file. %s. %s' % (error, traceback.format_exc() ), level = LogLevel.ERROR )

    return result

  def checkFileIntegrity( self ) :
    '''
    Check that all required L{FileFragment}s exist and have the correct length.
    @return : True if all required L{FileFragment}s exist and have the correct
            length, False otherwise.
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
    Set the C{FileBuilderInfo} status.
    @type value : L{FileBuilderInfoStatus}
    @param value: L{FileBuilderInfoStatus} that specify if the C{FileBuilderInfo} status.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      self.status = value

  def buildResultFile( self ) :
    '''
    Build a file from a L{FileBuilderInfo}. This method can not be executed
    by multiple L{threading.Thread} simultaneously.
    @type filebuilderinfo : FileBuilderInfo
    @param filebuilderinfo : L{FileBuilderInfo} that contains all informations
            about the file to rebuild (fragments, length, name).
    @type filepath : string
    @param filepath : path of the file to rebuild.
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
    Get L{FileFragment} for the current C{FileBuilderInfo}.
    @type return : L{dict} containing the L{FileFragment}s.
    '''
    return self.filefragments

  def getFileFragment( self, filefragmentsha1 ) :
    '''
    Get L{FileFragment} using its sha1 key for the current C{FileBuilderInfo}.
    @type filefragmentsha1 : string
    @param filefragmentsha1 : sha1 key for the L{FileFragment}.
    @type return : the found L{FileFragment} or None if not found.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      for filefragment in self.filefragments.values() :
        if filefragment.sha1 == filefragmentsha1 :
          return filefragment

      return None

  def getResultFileName( self ) :
    '''
    Get result file name for the current C{FileBuilderInfo}. i.e. the name
    of the file rebuilt.
    @type return : L{string} containing the result file name for the current C{FileBuilderInfo}.
    '''
    return resourcemanager.getResultFileName( self.getFileName(), self.getFileLength() )

  def getResultDirectory( self ) :
    '''
    Get result directory for the current C{FileBuilderInfo}. i.e. the name
    of the directory where the file will be rebuild.
    @type return : L{string} containing the result directory for the current C{FileBuilderInfo}.
    '''
    return resourcemanager.getResultDirectory( self.getUploadId(), self.basedirectory )

  def addFileFragment( self, filefragment ) :
    '''
    Add L{FileFragment} to the current C{FileBuilderInfo}. i.e.
    @type filefragment : L{FileFragment}
    @param filefragment : L{FileFragment} to add to the current C{FileBuilderInfo}.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      # File fragments are ordered using their offset
      self.filefragments[ filefragment.getOffset() ] = filefragment

  def getFileName( self ):
    '''
    Get the considered file name for the current C{FileBuilderInfo}.
    @return : L{string} containing the considered file name for the current C{FileBuilderInfo}.
    '''
    return self.filename

  def getFileLength( self ):
    '''
    Get the considered file length for the current C{FileBuilderInfo}.
    @return : L{long} containing the considered file length for the current C{FileBuilderInfo}.
    '''
    return self.filelength

  def getUploadId( self ):
    '''
    Get the upload id for the current C{FileBuilderInfo}.
    @return : L{string} containing the upload id for the current C{FileBuilderInfo}.
    '''
    return self.uploadid
  
  def getFileHash( self ):
    '''
    Get the considered file hash for the current C{FileBuilderInfo}.
    @return : L{string} containing the considered file hash for the current C{FileBuilderInfo}.
    '''
    return FileBuilderInfo.getHash( self.uploadid, self.basedirectory, self.filename, self.filelength )
    
  def __str__( self ):
    '''
    Get the string current C{FileBuilderInfo}.
    @return : L{string} representing the current C{FileBuilderInfo}.
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
    @type filename : string
    @param filename : file name to use for creating the hash.
    @type filename : long
    @param filename : file length to use for creating the hash.
    @return : the hash for a file name and length.
    '''
    return repr( [ basedirectory, filename, filelength, uploadid ] )


#------------------------------------------------------------------------------
class FileFragment :
  '''
  Class to get file fragment information. A C{FileFragment} correponds to a part of a file.
  '''
  header = None

  def __init__( self, headerfile ) :
    '''
    Initialize the C{FileFragment}.
    @type headerfile : cgi.FieldStorage
    @param headerfile : L{cgi.FieldStorage} from the parsed http request.
    '''
    header = minidom.parseString( headerfile.value )
    self.parseFromXml( header )

  def _checkFile( self, filepath ) :
    '''
    Check that the file exists and that the C{FileFragment} SHA-1 key matches for its content.
    @type filepath : string
    @param filepath : path of the file to check for the C{FileFragment}.
    @return : True if the file exists and matches the C{FileFragment} SHA-1 key, False otherwise.
    '''
    if ( ( len( filepath ) > 0 ) and os.path.exists( filepath ) ) :
      resourcelock = resourcemanager.getResourceLock( filepath )
      with resourcelock :
        # Read file content and check that sha1 key is correct
        file = open( filepath, 'r+b' )
        filecontent = file.read()

        return checkSha1( filecontent, self.sha1 )

    else :
      return False

  def writeLocalData( self, datafile ) :
    '''
    Write data to a local file from L{cgi.FieldStorage}. The L{cgi.FieldStorage} comes
    from a parsed http request.
    @type datafile : cgi.FieldStorage
    @param datafile : L{cgi.FieldStorage} containing the data for the C{FileFragment}.
    @return : True if the data were written to the local file without any issue, False otherwise.
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

      return True

    except Exception, error :
      # If write in this directory fails we try the next directory
      logmanager.writeLogInfo( 'Error occured writing fragment data. %s. %s' % (error, traceback.format_exc() ), level = LogLevel.ERROR )

    return False
  
  def readLocalData( self ) :
    '''
    Read data for the C{FileFragment} from a local file.
    @return : L{string} containing the data for the C{FileFragment}.
    '''
    filepath = self.getValidLocalDataPath()
    
    resourcelock = resourcemanager.getResourceLock( filepath )
    with resourcelock :
      if ( len(filepath) > 0 ) :
        file = open( filepath, "r+b" )
        return file.read()
      else :
        return None

  def deleteLocalData( self ) :
    '''
    Delete data for the C{FileFragment} local file.
    @type filepath : string
    @param filepath : L{string} containing the file path to delete.
    '''
    objectlock = resourcemanager.getObjectLock( self )
    with objectlock :
      try :
        filepath = self.getValidLocalDataPath()
        resourcelock = resourcemanager.getResourceLock( self )
        with resourcelock :
          if len(filepath) > 0 :
            os.remove( filepath )
      except Exception, error :
        logmanager.writeLogInfo( 'Error occured deleting fragment data. %s. %s' % (error, traceback.format_exc() ), level = LogLevel.ERROR )

  def parseFromXml( self, document ) :
    '''
    Parses C{FileFragment} from an xml document.
    @type document : xml.dom.minidom.Document
    @param document : L{xml.dom.minidom.Document} containing the parsed xml header for the current C{FileFragment}.
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
    Get the base directory for the current C{FileFragment}.
    @return : L{string} containing the base directory for the current C{FileFragment}.
    '''
    return self.basedirectory
  
  def getFileName( self ):
    '''
    Get the file name for the current C{FileFragment}.
    @return : L{string} containing the file name for the current C{FileFragment}.
    '''
    return self.filename

  def getFileLength( self ):
    '''
    Get the file length for the current C{FileFragment}.
    @return : L{string} containing the file length for the current C{FileFragment}.
    '''
    return self.filelength

  def getOffset( self ):
    '''
    Get the offset of the current C{FileFragment} (i.e. the index of the first C{FileFragment}
    data character in the result file).
    @return : L{long} containing the fragment offset of the current C{FileFragment}.
    '''
    return self.offset

  def getLength( self ):
    '''
    Get the length of the current C{FileFragment} (i.e. the length of the C{FileFragment} data).
    @return : L{long} containing the length of the current C{FileFragment}.
    '''
    return self.length

  def getUploadId( self ):
    '''
    Get the upload id for the current C{FileFragment}.
    @return : L{string} containing the upload id for the current C{FileFragment}.
    '''
    return self.uploadid
  
  def getSha1( self ):
    '''
    Get the sha1 key of the current C{FileFragment} (the sha1 key is used to process check sum
    on the C{FileFragment} data).
    @return : L{string} containing the sha1 key of the current C{FileFragment}.
    '''
    return self.sha1

  def getValidLocalDataPath( self ) :
    '''
    Get a local data path for C{FileFragment}. Checks on the file existence.
    @return : L{string} containing the found local data path or empty L{string} if not found.
    '''
    foundfile = ''

    directory = resourcemanager.getDirectory( 'httpupload.dirtempfilefragments' )
    if os.path.exists( directory ) :
      filepath = os.path.realpath( os.path.join( directory, self.sha1 ) )

      if os.path.exists( filepath ) :
        foundfile = filepath
    return foundfile

  def hasValidSizeLocalData( self ) :
    '''
    Check that the current C{FileFragment} has valid local data. Checks the file existence
    and the size of the file.
    @return : True if the current C{FileFragment} has valid local data using data size, False otherwise.
    '''
    filepath = self.getValidLocalDataPath()
    resourcelock = resourcemanager.getResourceLock( filepath )
    with resourcelock :
      if ( len(filepath) > 0 ):
        return ( os.path.getsize( filepath ) == self.getLength() )
      else :
        return False
      
  def hasValidLocalData( self ) :
    '''
    Check that the current C{FileFragment} has valid local data. Checks the file existence
    and sha1 key.
    @return : True if the current C{FileFragment} has valid local data, False otherwise.
    '''
    filepath = self.getValidLocalDataPath()
    return self._checkFile( filepath )

  def __str__( self ) :
    '''
    Get a L{string} representing the current C{FileFragment}.
    @return : L{string} representing the current C{FileFragment}.
    '''
    return 'self.filename : ' + self.filename + ', self.filelength : ' + unicode(self.filelength) + ', self.offset : ' + unicode(self.offset) + ', self.length : ' + unicode(self.length) + ', self.sha1 : ' + self.sha1 + ', self.getValidLocalDataPath() : ' + self.getValidLocalDataPath()
