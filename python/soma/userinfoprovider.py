import operator
import types

from soma.signature.api import Signature, VariableSignature, Unicode, Sequence, Integer, Choice
from soma.wip.configuration import ConfigurationGroup
from soma.wip.application.api import Application

def getFormatted( dataset, formats, keys, sorts ) :
  '''
  Format a dataset (i.e. a L{list} of L{list}s. For each record of
  the dataset it applies formats. Each new record of the resulting
  dataset is a list that contains result of the formats applied to
  the record. In the resulting dataset their is as many columns as
  there is formats to apply.
  @type dataset : list
  @param dataset : L{list} of L{list}s that contain data
  @type formats : list.
  @param formats : L{list} of L{string}s that contain formats to apply.
  @type keys : list.
  @param keys : L{list} of L{string}s that contain the keys for each
                dataset column. The keys must be used in formats.
                As an example, keys can be [ 'cn', 'guid' ] and
                formats [ '%(cn)s-%(guid)s', '%(cn)s', '%(guid)s' ].
                This example will result in a dataset with 3 columns.
  @type sorts : list.
  @param sorts : L{list} of L{int}s that contain the indexes of columns to
                 use for sorting the resulting dataset.
  @type return : L{list} of L{list}s containing the resulting data
                 sorted using the sort indexes.
  '''
  resultset = list()

  for datarecord in dataset :
    if (len(keys) == len(datarecord)):
      resultrecord = list()
      for format in formats :
        formatted = format % dict(zip(keys, datarecord))
        resultrecord.append(formatted.lstrip().rstrip())
      resultset.append(resultrecord)

  resultset.sort(key=operator.itemgetter(*sorts))
  return resultset

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
    @type return : C{UserInfoProvider} instance for the provider
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
    @type return : L{list} of {list}s containing users infos.
    '''
    pass
   
class LdapUserInfoProvider( UserInfoProvider ) :
  '''
  C{LdapUserInfoProvider} is the ldap implementation of the
  L{UserInfoProvider} class.
  '''
  def getUsers( self, **kwargs ) :
    '''
    Method that retrieve users info for the C{LdapUserInfoProvider}.
    It uses a ldap server.
    @type return : L{list} of {list}s containing users infos.
    '''
    import ldap
    
    appli = Application()
    server = kwargs.get('server', appli.configuration.userinfoprovider.ldap.server)
    base = kwargs.get('base', appli.configuration.userinfoprovider.ldap.base)
    filter = kwargs.get('filter', appli.configuration.userinfoprovider.ldap.filter)
    attributes = kwargs.get('attributes', appli.configuration.userinfoprovider.ldap.attributes)
    formats = kwargs.get('formats', appli.configuration.userinfoprovider.ldap.formats)
    sorts = kwargs.get('sorts', appli.configuration.userinfoprovider.ldap.sorts)
        
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

    return getFormatted( resultset, formats, attributes, sorts )

class NisUserInfoProvider( UserInfoProvider ) :
  '''
  C{NisUserInfoProvider} is the nis implementation of the
  L{UserInfoProvider} class.
  '''
  def getUsers( self, **kwargs ) :
    '''
    Method that retrieve users info for the C{NisUserInfoProvider}.
    It uses a nis server.
    @type return : L{list} of {list}s containing users infos.
    '''
    import nis
    import re
    appli = Application()
    map = kwargs.get('map', appli.configuration.userinfoprovider.nis.map)
    domain = kwargs.get('domain', appli.configuration.userinfoprovider.nis.domain)
    separator = kwargs.get('separator', appli.configuration.userinfoprovider.nis.separator)
    indexes = kwargs.get('indexes', appli.configuration.userinfoprovider.nis.indexes)
    filter = kwargs.get('filter', appli.configuration.userinfoprovider.nis.filter)
    attributes = kwargs.get('attributes', appli.configuration.userinfoprovider.nis.attributes)
    formats = kwargs.get('formats', appli.configuration.userinfoprovider.nis.formats)
    sorts = kwargs.get('sorts', appli.configuration.userinfoprovider.nis.sorts)

    resultset = list()
    for value in nis.cat(map, domain).itervalues():
      if not re.match(filter, value) is None :
        resultrecord = list()
        nisvalues = value.split(separator)
        resultrecord = [ nisvalues[ index ] for index in indexes ]
        resultset.append( resultrecord )
    
    return getFormatted( resultset, formats, attributes, sorts )

class LdapUserInfoProviderConfigurationGroup( ConfigurationGroup ) :
  signature = Signature(
    'server', Unicode, dict(defaultValue='localhost', doc='Set ldap server address or name here.'),
    'domain', Unicode, dict(defaultValue='', doc='Set ldap domain here.'),
    'base', Unicode, dict(defaultValue='', doc='Set ldap base here (it the ldap query for the base container object used).'),
    'filter', Unicode, dict(defaultValue='(cn=* *)', doc='Set ldap filter here.'),
    'attributes', Sequence(Unicode), dict(defaultValue=[ 'cn', 'uid' ], doc='Set ldap attributes to use here.'),
    'formats', Sequence(Unicode), dict(defaultValue=[ '%(cn)s', '%(uid)s' ], doc='Set formats to apply here.' ),
    'sorts', Sequence(Integer), dict(defaultValue=[0], doc='Set sort attributes here.')
  )

class NisUserInfoProviderConfigurationGroup( ConfigurationGroup ) :
  signature = Signature(
    'domain', Unicode, dict(defaultValue='', doc='Set nis domain here.'),
    'map', Unicode, dict(defaultValue='passwd', doc='Set nis map here.'),
    'separator', Unicode, dict(defaultValue=':', doc='Set nis map record separator here.'),
    'indexes', Sequence(Integer), dict(defaultValue=[ 4, 0 ], doc='Set indexes of nis map record here.' ),
    'filter', Unicode, dict(defaultValue='^[A-Za-z]{2}\d{6}[^@]*$', doc='Set nis map record filter here.' ),
    'attributes', Sequence(Unicode), dict(defaultValue=[ 'cn', 'uid' ], doc='Set nis keys here (key order must match with indexes order).' ),
    'formats', Sequence(Unicode), dict(defaultValue=[ '%(cn)s', '%(uid)s' ], doc='Set formats to apply here.' ),
    'sorts', Sequence(Integer), dict(defaultValue=[0], doc='Set sort attributes here.')
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

