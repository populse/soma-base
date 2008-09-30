import operator
import types

from soma.signature.api import Signature, VariableSignature, Unicode, Sequence, Integer, Choice
from soma.wip.configuration import ConfigurationGroup
from soma.wip.application.api import Application

def getUsersInfo( dataset, formats, keys, sorts ) :
  '''
  Get user infos from a dataset (i.e. a L{list} of L{list}s. For each record
  of the dataset it applies formats. Each new record of the resulting dataset
  is a list that contains L{UserInfo} objects, resulting of the formats applied
  to each record.
  @type dataset : list
  @param dataset : L{list} of L{list}s that contain data
  @type formats : list.
  @param formats : L{list} of L{list} of L{string}s that contains
                  resulting column name and formats to apply.
  @type keys : list.
  @param keys : L{list} of L{string}s that contain the keys for each
                dataset column. The keys must be used in formats.
                As an example, keys can be [ 'cn', 'guid' ] and
                formats [ '%(cn)s-%(guid)s', '%(cn)s', '%(guid)s' ].
                This example will result in a dataset with 3 columns.
  @type sorts : list.
  @param sorts : L{list} of L{str}s that contain the name of columns to
                 use for sorting the resulting dataset.
  @return : L{list} of L{UserInfo}s sorted using the sort fields.
  '''
  result = list()
  recordset = list()
  columnset = list()

  # Creates the columns list
  for format in formats :
    columnset.append( format[0] )

  # Creates the records set
  for datarecord in dataset :
    if (len(keys) == len(datarecord)):
      resultrecord = list()
      for format in formats :
        formatvalue = format[1]
        formatted = formatvalue % dict(zip(keys, datarecord))
        resultrecord.append(unicode(formatted, 'utf-8').lstrip().rstrip().lower())
      recordset.append(resultrecord)

  # Sorts the recordset
  sortindexes = [ columnset.index( name ) for name in sorts ]
  recordset.sort(key=operator.itemgetter(*sortindexes))

  for datarecord in recordset :
    parameters = dict()
    for index in xrange(len(columnset)) :
      parameters[ columnset[ index ] ] = datarecord[ index ]
      
    # Instanciates user info object
    yield UserInfo( **parameters )

class UserInfo( object ) :
  '''
  C{UserInfo} is a class that contains user information.
  '''

  def __init__( self, completename = None, lastname = '', firstname = '', login = '' ) :
    self.completename = completename
    self.lastname = lastname
    self.firstname = firstname
    self.login = login

  def getCompleteName( self ) :
    '''
    Get the C{UserInfo} complete name (i.e. Formatted first name and last name).
    @return : C{UserInfo} complete name.
    '''
    if ( self.completename is None ) :
      return ' '.join( [ self.lastname.title(), self.firstname.title() ] )
    else :
      return self.completename.title()
  
class UserInfoProviderType :
  LDAP = 'ldap'
  NIS = 'nis'

class UserInfoProvider( object ) :
  '''
  C{UserInfoProvider} is a base class for providers that deal with
  user information.
  '''
  @staticmethod
  def getUserInfoProviderInstance( providertype = None ) :
    '''
    Static method that instanciates a C{UserInfoProvider} object.
    @type providertype : L{UserInfoProviderType}
    @param providertype : type of the provider to instanciates.
    @return : C{UserInfoProvider} instance for the provider
                   type. If providertype is None, it tries to get
                   provider type from application configuration.
    '''
    if providertype is None :
      # try to get from application configuration
      appli = Application()
      providertype = appli.configuration.userinfoprovider.uses

    if ( providertype == UserInfoProviderType.NIS ) :
      return NisUserInfoProvider()
    else :
      return LdapUserInfoProvider()
      
  def getUsers( self ) :
    '''
    Method that retrieve users info for the C{UserInfoProvider}.
    @return : L{list} of {list}s containing users infos.
    '''
    pass
   
class LdapUserInfoProvider( UserInfoProvider ) :
  '''
  C{LdapUserInfoProvider} is the ldap implementation of the
  L{UserInfoProvider} class.
  '''
  def getUsers( self, server = None, base = None, filter = None, attributes = None, formats = None, sorts = None ) :
    '''
    Method that retrieve users info for the C{LdapUserInfoProvider}.
    It uses a ldap server.
    @type server : L{str}
    @param server : ldap server address to get data from.
    @type base : L{str}
    @param base : ldap base entity to get user info from.
    @type filter : L{str}
    @param filter : ldap filter to get filtered user info (example : (cn=*) ).
    @type attributes : L{list}
    @param attributes : list of ldap attributes to get (example : [ 'sn', 'givenName', 'uid' ] ).
    @type formats : L{list}
    @param formats : list of tuple that contains names of the matching user field and formats to apply
                     (example : [ ( 'lastname', '%(sn)s %(givenName)s'), ( 'login', '%(uid)s') ] ).
    @type sorts : L{list} of L{int}
    @param sorts : list of sorts to apply to get user information (example : [ 0 ] ).
                  Values are the indexes of output fields used to sort data.
    @return : L{list} of L{list}s containing users infos.
    '''
    import ldap
    
    appli = Application()

    if server is None :
      server = appli.configuration.userinfoprovider.ldap.server
      
    if base is None : 
      base = appli.configuration.userinfoprovider.ldap.base

    if filter is None :
      filter = appli.configuration.userinfoprovider.ldap.filter

    if attributes is None :
      attributes = appli.configuration.userinfoprovider.ldap.attributes

    if formats is None :
      formats = appli.configuration.userinfoprovider.ldap.formats

    if sorts is None :
      sorts = appli.configuration.userinfoprovider.ldap.sorts
        
    resultset = list()
    try :
      ldapaccess = ldap.open(server)
      ldapaccess.simple_bind()
      resultid = ldapaccess.search( base, ldap.SCOPE_SUBTREE, filter, attributes )
      timeout = 0
      
      while 1 :
        resulttype, resultdata = ldapaccess.result(resultid, timeout)
        if (resultdata == []):
          break
        else:
          if resulttype == ldap.RES_SEARCH_ENTRY:
            resultrecord = list()
            for attribute in attributes :
              if ( attribute in resultdata[0][1] ) :
                resultrecord.append( resultdata[0][1][attribute][0] )
            
            resultset.append(resultrecord)
          
    except ldap.LDAPError, errormessage :
      print errormessage

    return getUsersInfo( resultset, formats, attributes, sorts )

class NisUserInfoProvider( UserInfoProvider ) :
  '''
  C{NisUserInfoProvider} is the nis implementation of the
  L{UserInfoProvider} class.
  '''
  def getUsers( self, map = None, domain = None, separator = None, indexes = None, filter = None, attributes = None, formats = None, sorts = None ) :
    '''
    Method that retrieve users info for the C{NisUserInfoProvider}.
    It uses a nis server.
    @type map : L{str}
    @param map : nis map to get user info from.
    @type domain : L{str}
    @param domain : nis domain to get user info from.
    @type separator : L{str}
    @param separator : separator to use to parse nis map records.
    @type indexes : L{list}
    @param indexes : list of indexes of the columns to use in nis map records.
    @type filter : L{str}
    @param filter : regular expression used to select nis map records to get user info from.
    @type attributes : L{list}
    @param attributes : L{list} of attributes to use. They must match the order of indexes
                      (for example : [ 'sn', 'givenName', 'uid' ], this means that the column
                      corresponding to the first index value (defined by indexes) will contain the sn,
                      the column corresponding to the second index value (defined by indexes) will
                      contain the 'givenName', etc ... ).
    @type formats : L{list}
    @param formats : list of tuple that contains names of the matching user field and formats to apply
                     (example : [ ( 'lastname', '%(sn)s %(givenName)s'), ( 'login', '%(uid)s') ] ).
    @type sorts : L{list} of L{int}
    @param sorts : list of sorts to apply to get user information (example : [ 0 ] ).
                  Values are the indexes of output fields used to sort data.
    @return : L{list} of L{list}s containing users infos.
    '''
    import nis
    import re
    appli = Application()
    
    if map is None :
      map = appli.configuration.userinfoprovider.nis.map
    
    if domain is None :
      domain = appli.configuration.userinfoprovider.nis.domain

    if separator is None :
      separator = appli.configuration.userinfoprovider.nis.separator

    if indexes is None :
      indexes = appli.configuration.userinfoprovider.nis.indexes
    
    if filter is None :
      filter = appli.configuration.userinfoprovider.nis.filter
    
    if attributes is None :
      attributes = appli.configuration.userinfoprovider.nis.attributes
    
    if formats is None :
      formats = appli.configuration.userinfoprovider.nis.formats
    
    if sorts is None :
      sorts = appli.configuration.userinfoprovider.nis.sorts

    resultset = list()
    for value in nis.cat(map, domain).itervalues():
      if not re.match(filter, value) is None :
        resultrecord = list()
        nisvalues = value.split(separator)
        resultrecord = [ nisvalues[ index ] for index in indexes ]
        resultset.append( resultrecord )
    
    return getUsersInfo( resultset, formats, attributes, sorts )

class LdapUserInfoProviderConfigurationGroup( ConfigurationGroup ) :
  signature = Signature(
    'server', Unicode, dict(defaultValue='localhost', doc='Set ldap server address or name here.'),
    'domain', Unicode, dict(defaultValue='', doc='Set ldap domain here.'),
    'base', Unicode, dict(defaultValue='', doc='Set ldap base here (it the ldap query for the base container object used).'),
    'filter', Unicode, dict(defaultValue='(cn=* *)', doc='Set ldap filter here.'),
    'attributes', Sequence(Unicode), dict(defaultValue=[ 'cn', 'uid' ], doc='Set ldap attributes to use here.'),
    'formats', Sequence(Sequence(Unicode)), dict(defaultValue=[ ( 'completename', '%(cn)s' ), ( 'login', '%(uid)s' ) ], doc='Set formats to apply here.' ),
    'sorts', Sequence(Integer), dict(defaultValue=['completename'], doc='Set sort attributes here.')
  )

class NisUserInfoProviderConfigurationGroup( ConfigurationGroup ) :
  signature = Signature(
    'domain', Unicode, dict(defaultValue='', doc='Set nis domain here.'),
    'map', Unicode, dict(defaultValue='passwd', doc='Set nis map here.'),
    'separator', Unicode, dict(defaultValue=':', doc='Set nis map record separator here.'),
    'indexes', Sequence(Integer), dict(defaultValue=[ 4, 0 ], doc='Set indexes of nis map record here.' ),
    'filter', Unicode, dict(defaultValue='^[A-Za-z]{2}\d{6}[^@]*$', doc='Set nis map record filter here.' ),
    'attributes', Sequence(Unicode), dict(defaultValue=[ 'cn', 'uid' ], doc='Set nis keys here (key order must match with indexes order).' ),
    'formats', Sequence(Sequence(Unicode)), dict(defaultValue=[ ( 'completename', '%(cn)s' ), ( 'login', '%(uid)s' ) ], doc='Set formats to apply here.' ),
    'sorts', Sequence(Integer), dict(defaultValue=['completename'], doc='Set sort attributes here.')
  )
    
class UserInfoProviderConfigurationGroup( ConfigurationGroup ) :
  signature = Signature(
    'uses', Choice( UserInfoProviderType.LDAP, UserInfoProviderType.NIS ), dict(defaultValue = UserInfoProviderType.LDAP ),
    'ldap', LdapUserInfoProviderConfigurationGroup, dict(defaultValue = LdapUserInfoProviderConfigurationGroup() ),
    'nis', NisUserInfoProviderConfigurationGroup, dict(defaultValue = NisUserInfoProviderConfigurationGroup() )
  )

def initializeUserInfoProvider():
  application = Application()
  if application.verbose:
    print 'User info provider'

  application.configuration.add( 'userinfoprovider', UserInfoProviderConfigurationGroup() )

#----------------------------------------------------------------------------
Application.onInitialization.add( initializeUserInfoProvider )

