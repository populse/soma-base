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
L{QLineEditModificationTimer} and L{TimeredQLineEdit} classes associate a
L{QTimer<qt.QTimer>} to a L{QLineEdit<qt.QLineEdit>} in order to signal user
modification only after an inactivity period.

@author: Yann Cointepas
@organization: U{NeuroSpin<http://www.neurospin.org>} and U{IFR 49<http://www.ifr49.org>}
@license: U{CeCILL version 2<http://www.cecill.info/licences/Licence_CeCILL_V2-en.html>}
'''
__docformat__ = "epytext en"


from turbogears.util            import Bunch
from turbogears.widgets.base    import JSLink, js_location, mochikit
from turbogears.widgets         import Widget, CompoundFormField, RemoteForm, TextField, CheckBox, SingleSelectField, FieldSet
from turbogears.widgets.forms   import update_path, get_path, build_name_from_path
from soma.tggui                 import tools
from soma.notification          import ObservableAttributes
from soma.uuid                  import Uuid

##-------------------------------------------------------------------------------
class TgAutoNamed(object) :
  '''
  Manages C{TgAutoNamed} fields that uses unique identifiers to identify themselves.
  '''
  
  def __init__( self, *args, **kwargs ):

    if 'autonamed' in kwargs :
      autonamed = kwargs[ 'autonamed' ]
      kwargs.pop( 'autonamed' )
    else :
      autonamed = True

    if autonamed :
      widgetid = unicode(Uuid()).replace('-', '')
      self.__class__._get_path = update_path( TgAutoNamed._get_path )
      self.__class__.path = property( TgAutoNamed._get_path)
      self.__class__.name_path = property( TgAutoNamed._get_name_path)
      self.widgetid = widgetid
      self.name = widgetid
      self.label = None

    super( TgAutoNamed, self ).__init__( *args, **kwargs )

  def _get_path(self):
    value = [ Bunch(widget = self, repetition = None ) ]
    return value

  def _get_name_path(self):
    value = [ Bunch(widget = self, repetition = None ) ]
    return value

  def get_auto_field_id( self ):
      return self.__class__._get_name_path( value )
  
  def get_auto_name_path( self ):
      return [ Bunch(widget = self, repetition = None ) ]

##-------------------------------------------------------------------------------
class TgBase(object) :

  def close( self ):
    '''
    @see: close method can be called during
    '''

##-------------------------------------------------------------------------------
class TgStandardBase( TgBase, TgAutoNamed, ObservableAttributes ) :

  params = ['label_attrs']
  params_doc = {'label_attrs' : 'Dictionary containing extra (X)HTML attributes for'
                          ' the label input tag' }
  label_attrs = {}
  
  def __setattr__( self, name, value ):
    '''
    @see:
    '''
    # Hack to unlock turbogears widget
    tools.unlockWidget( self )
    super( TgStandardBase, self ).__setattr__( name, value )

##-------------------------------------------------------------------------------
#class QLineEditModificationTimer( qt.QObject ):
  #'''
  #A L{QLineEditModificationTimer} instance is accociated to a 
  #L{QLineEdit<qt.QLineEdit>} instance, it listen all user modification (Qt 
  #signal C{'textChanged( const QString & )'}) and emit a 
  #C{PYSIGNAL('userModification' )} when C{timerInterval} milliseconds passed
  #since the last user modification.
  #'''
  
  ##: Default timer interval in milliseconds
  #defaultTimerInterval = 2000

  #def __init__( self, qLineEdit, timerInterval=None ):
    #'''
    #@param qLineEdit: widget associated with this L{QLineEditModificationTimer}.
    #@type  qLineEdit: L{QLineEdit<qt.QLineEdit>} instance
    #@param timerInterval: minimum inactivity period before emitting
      #C{userModification} signal. Default value is
      #L{QLineEditModificationTimer.defaultTimerInterval}
    #@type  timerInterval: milliseconds
    
    #@see: L{TimeredQLineEdit}
    #'''
    #qt.QObject.__init__( self )
    ##: L{QLineEdit<qt.QLineEdit>} instance associated with this 
    ##: L{QLineEditModificationTimer}
    #self.qLineEdit = qLineEdit
    #if timerInterval is None:
      #self.timerInterval = self.defaultTimerInterval
    #else:
      ##: minimum inactivity period before emitting C{userModification} signal.
      #self.timerInterval = timerInterval
    #self.__timer = qt.QTimer( self )
    #self.__internalModification = False
    #self.connect( self.qLineEdit, qt.SIGNAL( 'textChanged( const QString & )'), 
                  #self._userModification )
    #self.connect( self.qLineEdit, qt.SIGNAL( 'lostFocus()' ), 
                  #self._noMoreUserModification,  )
    #self.connect( self.__timer, qt.SIGNAL( 'timeout()' ), 
                  #qt.PYSIGNAL( 'userModification' ) )


  #def _userModification( self ):
    #if not self.__internalModification:
      #self.__timer.start( self.timerInterval, True )


  #def _noMoreUserModification( self ):
    #if self.__timer.isActive():
      #self.__timer.stop()
      #self.emit( qt.PYSIGNAL( 'userModification' ), () )


  #def stopInternalModification( self ):
    #'''
    #Stop emitting C{userModification} signal when associated
    #L{QLineEdit<qt.QLineEdit>} is modified.
    
    #@see: L{startInternalModification}
    #'''
    #self.__internalModification = False


  #def startInternalModification( self ):
    #'''
    #Restart emitting C{userModification} signal when associated
    #L{QLineEdit<qt.QLineEdit>} is modified.
    
    #@see: L{stopInternalModification}
    #'''
    #self.__internalModification = True


  #def stop( self ):
    #'''
    #Stop the timer if it is active.
    #'''
    #self.__timer.stop()

  
  #def isActive( self ):
    #'''
    #Returns True if the timer is active, or False otherwise.
    #'''
    #return self.__timer.isActive()


#-------------------------------------------------------------------------------
class TgTextField( TgStandardBase, TextField ):
  '''
  Create a C{TgTextField} instance.
  '''

  def stopInternalModification( self ):
    '''
    @see: L{}
    '''
    #self.__timer.stopInternalModification()
    pass


  def startInternalModification( self ):
    '''
    @see: L{}
    '''
    #self.__timer.startInternalModification()
    pass

  def setText( self, value ):
    '''
    @see: L{}
    '''
    tools.unlockWidget( self )
    self.default = value

  def setCaption( self, caption ):
    '''
    @see: L{}
    '''
    tools.unlockWidget( self )
    self.label = caption
    

  def caption( self ):
    '''
    @see: L{}
    '''
    return self.label
    
  def setIcon( self, icon ):
    '''
    @see: L{}
    '''
    pass
  
  def icon( self ):
    '''
    @see: L{}
    '''
    return None


#-------------------------------------------------------------------------------
class TgCheckBox( TgStandardBase, CheckBox ):
  '''
  Create a C{TgCheckBox} instance.
  '''

#-------------------------------------------------------------------------------
class TgSingleSelectField( TgStandardBase, SingleSelectField ):
  '''
  Create a C{TgSingleSelectField} instance.
  '''

#-------------------------------------------------------------------------------
class TgFieldSet( TgStandardBase, FieldSet ):
  '''
  Create a C{TgFieldSet} instance.
  '''
  template="""
  <fieldset xmlns:py="http://purl.org/kid/ns#"
      class="${field_class}"
      id="${field_id}"
      py:attrs="attrs"
  >
      <legend py:if="legend" py:content="legend" />
      <div py:for="field in hidden_fields"
          py:replace="field.display(value_for(field), **params_for(field))"
      />
      <table border="0" cellspacing="0" cellpadding="2" py:attrs="table_attrs">
        <tr py:for="i, field in enumerate(fields)"
            class="${i%2 and 'odd' or 'even'}"
        >
            <th py:if="field.label is not None">
                <label class="fieldlabel" for="${field.field_id}" py:content="field.label" py:attrs="field.label_attrs" />
            </th>
            <td py:attrs="{ 'colspan' : field.label and 1 or 2 }">
                <span py:replace="field.display(value_for(field), **params_for(field))" />
                <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
                <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
            </td>
        </tr>
      </table>
  </fieldset>
  """
  params = ['attrs', 'table_attrs']
  params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                          ' the fieldset input tag',
                'table_attrs' : 'Extra (X)HTML attributes for the Table tag'}
  attrs = {}
  table_attrs = {}
  
class TgExtendedApplet( TgStandardBase, Widget ):
  '''
  Create a C{TgExtendedApplet} instance.
  '''
  template="""
  <!-- Defines the correct applet tag according to the browser used -->
  <span xmlns:py="http://purl.org/kid/ns#"
      py:strip="True">
    <object py:if="tg.useragent.browser == 'msie'"
      id="${name}"
      name="${name}"
      classid="clsid:8AD9C840-044E-11D1-B3E9-00805F499D93"
      py:attrs="applet_attrs"
      >
      <param name="id" value="${name}" />
      <param py:for="param in applet_params.items()"
              py:attrs="{'name':param[0], 'value':param[1]}"/>
    </object>
    
    <embed py:if="tg.useragent.browser != 'msie'"
        id="${name}"
        name="${name}"
        pluginspage="http://java.sun.com/products/plugin/index.html#download"
        py:attrs="dict(applet_attrs.items() + applet_params.items())"
        >
        <noembed>
          ${altignored}
        </noembed>
    </embed>
  </span>
  """
  
  params = [ 'applet_attrs', 'applet_params', 'altignored', 'validator' ]
  params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                          ' the span input tag',
                'applet_attrs' : 'Extra (X)HTML attributes for the applet tag',
                'applet_params' : 'Parameters for the applet tag'}
  applet_attrs = { 'type' : 'application/x-java-applet;version=1.4',
                   'alt' : 'Your browser understands the &lt;APPLET&gt; tag but isn\'t running the applet, for some unknow reason.' }
  applet_params = {}
  applet_id = None
  altignored = 'Your browser is completely ignoring the &lt;APPLET&gt; tag!'
  validator = None

  
class TgUploadMultipleFiles( TgStandardBase, CompoundFormField ):
  '''
  Create a C{TgUploadMultipleFiles} instance.
  '''
  template="""
  <!-- Display process signature -->
  <div xmlns:py="http://purl.org/kid/ns#"
    py:strip="True">

    ${selectfiles_widget.display( value_for( selectfiles_widget ), **params_for( selectfiles_widget ) )}
    ${filesuploader_widget.display( value_for( filesuploader_widget ), **params_for( filesuploader_widget ) )}
    
    <div
      class="${field_class}"
      for="${field_id}"
      py:attrs="attrs" />
      
    <input
      type="hidden"
      id="${field_id}"
      name="${field_id}" />
  </div>
  """

  member_widgets = [ 'selectfiles_widget', 'filesuploader_widget' ]
  params = [ 'attrs', 'selectfiles_attrs', 'selectfiles_params', 'filesuploader_attrs', 'filesuploader_params' ]
  params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                          ' the text input tag',
                'selectfiles_attrs' : 'Dictionary containing extra (X)HTML attributes for'
                          ' the selectfiles applet tag',
                'selectfiles_params' : 'Dictionary containing extra (X)HTML parameters for'
                          ' the selectfiles applet tag',
                'filesuploader_attrs' : 'Dictionary containing extra (X)HTML attributes for'
                          ' the filesuploader applet tag',
                'filesuploader_params' : 'Dictionary containing extra (X)HTML parameters for'
                          ' the filesuploader applet tag',
                          }
  #attrs = { 'style' : 'height:100px;width:290px;border-color:#000000;border-style:solid;border-width:1px;float:left;overflow:auto;',
            #'class' : 'tgdisplayselectedfiles' }
  attrs = { 'class' : 'tgdisplayselectedfiles' }
  
  selectfiles_attrs = { 'class' : 'tgselectfiles',
                        'for' : None }
                        
  selectfiles_params = { 'code' : 'InputMultipleFiles.class',
                        'archive' : '/static/applets/brainvisaweb-applets.jar',
                        'scriptable' : 'true',
                        'mayscript' : 'true',
                        'onselectfiles' : 'soma.tggui.upload.selectedfiles()',
                        'buttontext' : 'Select...' }
                        
  #filesuploader_attrs = { 'style' : 'height:20px;width:186px;',
                          #'class' : 'tgfilesuploader',
                          #'for' : None }
  filesuploader_attrs = { 'class' : 'tgfilesuploader',
                          'for' : None }

  filesuploader_params = { 'code' : 'UploadMultipleFiles.class',
                          'archive' : '/static/applets/brainvisaweb-applets.jar',
                          'scriptable' : 'true',
                          'mayscript' : 'true',
                          'inputmultiplefilesappletname' : None,
                          'onuploadstart' : 'soma.tggui.upload.uploadstarted()',
                          'onuploadend' : 'soma.tggui.upload.uploadended()',
                          'not_started' : 'Upload not started',
                          'uploading' : 'Uploading files ...',
                          'building' : 'Building files ...',
                          'waiting_before_retry' : 'Waiting before retry ...',
                          'waiting_system' : 'Waiting before upload ...',
                          'failed' : 'Upload failed',
                          'successful' : 'Upload succeeded' }

  def __init__(self, *args, **kw):
    super(TgStandardBase, self).__init__(*args, **kw)
    
    self.javascript = [ mochikit, JSLink( 'static', 'js/soma.js' ) ]
    self.selectfiles_attrs[ 'for' ] = self.field_id
    self.selectfiles_widget = TgExtendedApplet()
    self.selectfiles_widget.applet_attrs = dict( self.selectfiles_widget.applet_attrs.items() + self.selectfiles_attrs.items() )
    self.selectfiles_widget.applet_params = self.selectfiles_params

    self.filesuploader_params[ 'inputmultiplefilesappletname' ] = self.selectfiles_widget.name
    self.filesuploader_attrs[ 'for' ] = self.field_id
    self.filesuploader_widget = TgExtendedApplet()
    self.filesuploader_widget.applet_attrs = dict( self.filesuploader_widget.applet_attrs.items() + self.filesuploader_attrs.items() )
    self.filesuploader_widget.applet_params = self.filesuploader_params

  def stopInternalModification( self ):
    '''
    @see: L{}
    '''
    #self.__timer.stopInternalModification()
    pass

  def startInternalModification( self ):
    '''
    @see: L{}
    '''
    #self.__timer.startInternalModification()
    pass

  def setText( self, value ):
    '''
    @see: L{}
    '''
    tools.unlockWidget( self )
    self.default = value

    
#-------------------------------------------------------------------------------
class TgRemoteForm( TgStandardBase, RemoteForm ):
  '''
  Create a C{TgRemoteForm} instance.
  '''
