# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys, os, stat, posix, time, re, pprint, sqlite3
try:
  import yaml as json_reader
except ImportError:
  import json as json_reader

try:
  from traits.api import ListStr
except ImportError:
  from enthought.traits.api import ListStr

from soma.path import split_path
from soma.application import Application
from soma.config import short_version

class DirectoryAsDict( object ):
  def __init__( self, directory ):
    self.directory = directory


  def __repr__( self ):
    return '<DirectoryAsDict( %s )>' % repr( self.directory )
  
  
  def iteritems( self ):
    try:
      listdir = os.listdir( self.directory )
    except OSError:
      yield '', [ None, None ]
      return
    for name in listdir:
      full_path = os.path.join( self.directory, name )
      st = os.lstat( full_path )
      if stat.S_ISDIR( st.st_mode ):
        yield ( name, [ tuple( st ), DirectoryAsDict( full_path ) ] )
      else:
        yield ( name, [ tuple( st ), None ] )

        
  @staticmethod
  def get_directory( directory, debug=None ):
    return DirectoryAsDict._get_directory( directory, debug, 0, 0, 0, 0, 0, 0, 0 )[ 0 ]
  
  @staticmethod
  def _get_directory( directory, debug, directories, files, links,
                      files_size, path_size, errors, count ):
    try:
      listdir = os.listdir( directory )
      result = {}
    except OSError:
      errors += 1
      result = None
    if result is not None:
      for name in listdir:
        if debug and count % 100 == 0:
          print >> debug, time.asctime(), 'files=%d, directories=%d, size=%d' % ( files+links, directories, files_size )
        path_size += len( name )
        count += 1
        full_path = os.path.join( directory, name )
        st = os.lstat( full_path )
        if stat.S_ISREG( st.st_mode ):
          files += 1
          files_size += st.st_size
          result[ name ] = [ tuple( st ), None ]
        elif stat.S_ISDIR( st.st_mode ):
          content, directories, files, links, files_size, path_size, errors, count =  DirectoryAsDict._get_directory( full_path, debug, directories + 1, files, links, files_size, path_size, errors, count )
          result[ name ] = [ tuple( st ), content ]
        else:
          links += 1
          result[ name ] = [ tuple( st ), None ]
    return result, directories, files, links, files_size, path_size, errors, count

    
  @staticmethod
  def paths_to_dict( *paths ):
    result = {}
    for path in paths:
      current_dir = result
      path_list = split_path( path )
      for name in path_list[ :-1 ]:
        st_content = current_dir.setdefault( name, [ None, {} ] )
        if st_content[ 1 ] is None:
          st_content[ 1 ] = {}
        current_dir = st_content[ 1 ]
      current_dir.setdefault( path_list[ -1 ], [ None, None ] )
    return result


  @staticmethod
  def get_statistics( dirdict, debug=None ):
    return PathToAttributes._get_statistics( dirdict, debug, 0, 0, 0, 0, 0, 0, 0 )[ :-1 ]
    
  
  @staticmethod
  def _get_statistics( dirdict, debug, directories, files, links, files_size, path_size, errors, count ):
    
    if debug and count % 100 == 0:
      print >> debug, time.asctime(), 'files=%d, directories=%d, size=%d' % ( files+links, directories, files_size )
    count += 1
    for name, content in dirdict.iteritems():
      path_size += len( name )
      st, content = content
      if st:
        st = posix.stat_result( st )
        if stat.S_ISREG( st.st_mode ):
          files += 1
          files_size += st.st_size
        elif stat.S_ISDIR( st.st_mode ):
          if content is None:
            directories += 1
            errors += 1
          else:
            directories, files, links, files_size, path_size, errors, count = PathToAttributes._get_statistics( content, debug, directories + 1, files, links, files_size, path_size, errors, count )
        else:
          links += 1
      else:
        errors += 1
    return ( directories, files, links, files_size, path_size, errors, count )

        
class FileOrganizationModelManager( object ):
  '''
  Manage the discovery and instanciation of available FileOrganizationModel (FOM). A FOM can be represented as a JSON file (or a series of JSON files in a directory). This class allows to identify these files contained in a predefined set of directories (see find_fom method) and to instanciate a FileOrganizationModel for each identified file (see get_fom method).
  '''
  def __init__( self, paths ):
    '''
    Create a FOM manager that will use the given paths to find available FOMs.
    '''
    self.paths = paths
    self._cache = None
  
  
  def find_foms( self ):
    '''Return a list of file organisation model (FOM) names. 
    These FOMs can be loaded with load_foms. FOM files (or directories) are
    looked for in self.paths.'''
    self._cache = {}
    for path in self.paths:
      for i in os.listdir( path ):
        full_path = os.path.join( path, i )
        if os.path.isdir( full_path ):
          for ext in ( '.json', '.yaml' ):
            main_file = os.path.join( full_path, i + ext )
            if os.path.exists( main_file ):
              d = json_reader.load( open( main_file ) )
              name = d.get( 'fom_name' )
              if not name:
                raise ValueError( 'file %s does not contain fom_name' % main_file )
              self._cache[ name ] = full_path
        elif i.endswith( '.json' ) or i.endswith( '.yaml' ):
          d = json_reader.load( open( full_path ) )
          name = d.get( 'fom_name' )
          if not name:
            raise ValueError( 'file %s does not contain fom_name' % full_path )
          self._cache[ name ] = full_path
    return self._cache.keys()
   
   
  def load_foms( self, *names ):
    if self._cache is None:
      self.find_foms()
    foms = FileOrganizationModels()
    for name in names:
      foms.import_file( self._cache[ name ], foms_manager=self )
    return foms

    
  def file_name( self, fom ):
    if self._cache is None:
      self.find_foms()
    return self._cache[ fom ]

    
class FileOrganizationModels( object ):
  def __init__( self ):
    self._directories_regex = re.compile( r'{([^}]*)}' )
    self._attributes_regex = re.compile( '<([^>]*)>' )
    self.fom_names = set()
    self.attribute_definitions = {
      "fom_name" : {
        "descr" : "File Organization Model (FOM) in which a pattern is defined.",
        "values" : self.fom_names,
      },
      "fom_format" : {
        "descr" : "Format of a file.",
        "values" : set(),
      }
    }
    self.formats = {}
    self.format_lists = {}
    self.shared_patterns = {}
    self.patterns = {}
    self.rules = []
    
  
  def import_file( self, file_or_dict, foms_manager=None ):
    if not isinstance( file_or_dict, dict ):
      json_dict = json_reader.load( open( file_or_dict, 'r' ) )
    else:
      json_dict = file_or_dict
    
    foms = json_dict.get( 'fom_import', [] )
    if foms and foms_manager is None:
      raise RuntimeError( 'Cannot import FOM because no FileOrganizationModelManager has been provided' ) 
    for fom in foms:
      self.import_file( foms_manager.file_name( fom ) )
    
    fom_name = json_dict[ 'fom_name' ]
    if fom_name in self.fom_names:
      return
    self.fom_names.add( fom_name )
    
    # Update attribute definitions
    attribute_definitions = json_dict.get( 'attribute_definitions' )
    if attribute_definitions:
      for attribute, definition in attribute_definitions.iteritems():
        existing_definition = self.attribute_definitions.get( attribute )
        values = definition.get( 'values' )
        if existing_definition:
          existing_values = definition.get( 'values' )
          if ( existing_values is None ) != bool( values is None ):
            raise ValueError( 'Incompatible values redefinition for attribute %s' % attribute )
          if ( definition.get( 'default_value' ) is None ) != ( existing_definition.get( 'default_value' ) is None ):
            raise ValueError( 'Incompatible default value redefinition of attribute %s' % attribute )
          if values:
            existing_values.extend( values )
        else:
          definition = definition.copy()
          if values is not None:
            definition[ 'values' ] = set( values )
          self.attribute_definitions[ attribute ] = definition
    
    # Process shared patterns to expand the ones that reference other shared
    # patterns
    self.formats.update( json_dict.get( 'formats', {} ) )
    self.format_lists.update( json_dict.get( 'format_lists', {} ) )
    self.shared_patterns.update( json_dict.get( 'shared_patterns', {} ) )
    if self.shared_patterns:
      stack = self.shared_patterns.items()
      while stack:
        name, pattern = stack.pop()
        expanded_pattern = []
        last_end = 0
        for match in self._directories_regex.finditer( pattern ):
          c = pattern[ last_end : match.start() ]
          if c:
            expanded_pattern.append( c )
          attribute = match.group( 1 )
          expanded_pattern.append( self.shared_patterns[ attribute ] )
          last_end = match.end()
        if expanded_pattern:
          last = pattern[ last_end : ]
          if last:
            expanded_pattern.append( last )
          stack.append( ( name, ''.join( expanded_pattern ) ) )
        else:
          self.shared_patterns[ name ] = pattern
    
    rules = json_dict.get( 'rules' )
    patterns = json_dict.get( 'patterns', {} ).copy()
    processes = json_dict.get( 'processes' )      
            
    if rules:
      patterns[ 'fom_dummy' ] = rules
    new_patterns = {}
    self._expand_json_patterns( patterns, new_patterns, { 'fom_name' : fom_name } )
    self._parse_patterns( new_patterns, self.patterns )

    if processes:
      process_patterns = {}
      for process, parameters in processes.iteritems():
        process_dict = {}
        process_patterns[ process ] = process_dict
        for parameter, rules in parameters.iteritems():
          parameter_rules = []
          process_dict[ parameter ] = parameter_rules
          for rule in rules:
            if len( rule ) == 2:
              pattern, formats = rule
              rule_attributes = {}
            else:
              #print '!', rule, len( rule )
              pattern, formats, rule_attributes = rule
            rule_attributes[ 'fom_process' ] = process
            rule_attributes[ 'fom_parameter' ] = parameter
            parameter_rules.append( [ pattern, formats, rule_attributes ] )
      new_patterns = {}
      self._expand_json_patterns( process_patterns, new_patterns, { 'fom_name' : fom_name } )
      self._parse_patterns( new_patterns, self.patterns )

      
  def selected_rules( self, selection ):
    if selection:
      format = selection.get( 'format' )
      for rule_pattern, rule_attributes in self.rules:
        rule_formats = rule_attributes.get( 'fom_formats', [] )
        if format:
          if format == 'fom_first':
            if not rule_formats:
              continue
          elif format not in rule_formats:
            continue
        keep = True
        for attribute, selection_value in selection.iteritems():
          if attribute == 'format':
            continue
          rule_value = rule_attributes.get( attribute )
          if rule_value is not None and rule_value != selection_value:
            keep = False
            break
        if keep:
          yield ( rule_pattern, rule_attributes )
    else:
      for rule in self.rules:
        yield rule
  
  
  def _expand_json_patterns( self, json_patterns, parent, parent_attributes ):
    attributes = parent_attributes.copy()
    attributes.update( json_patterns.get( 'fom_attributes', {} ) )
    for attribute, value in attributes.iteritems():
      if attribute not in self.attribute_definitions:
        self.attribute_definitions[ attribute ] = { 'values' : set( (value,) ) }
      else:
        values = self.attribute_definitions[ attribute ].get( 'values' )
        if values:
          values.add( value )
          
    key_attribute = json_patterns.get( 'fom_key_attribute', None )
    if key_attribute:
      self.attribute_definitions.setdefault( key_attribute, {} )
      #raise ValueError( 'Attribute "%s" must be declared in attribute_definitions' % key_attribute )
    
    for key, value in json_patterns.iteritems():
      if key.startswith( 'fom_' ) and key != 'fom_dummy':
        continue
      if key_attribute:
        attributes[ key_attribute ] = key
        self.attribute_definitions[ key_attribute ].setdefault( 'values', set() ).add( key )
      if isinstance( value, dict ):
        self._expand_json_patterns( value, parent.setdefault( key, {} ), attributes )
      else:
        rules = []
        parent[ key ] = rules
        for rule in value:
          if len( rule ) == 2:
            pattern, format_list = rule
            rule_attributes = attributes.copy()
          else:
            pattern, format_list, rule_attributes = rule
            for attribute, value in rule_attributes.iteritems():
              definition = self.attribute_definitions.setdefault( attribute, {} )
              if definition is not None:
                values = definition.setdefault( 'values', set() )
                if values is not None:
                  values.add( value )
              #else:
                #raise ValueError( 'Attribute "%s" must be declared in attribute_definitions' % attribute )
            if attributes:
              new_attributes = attributes.copy()
              new_attributes.update( rule_attributes )
              rule_attributes = new_attributes
          
          # Expand format_list
          rule_formats = []
          if isinstance( format_list, basestring ):
            format_list = [ format_list ]
          if format_list:
            for format in format_list:
              formats = self.format_lists.get( format )
              if formats is not None:
                for f in formats:
                  rule_formats.append( f )
              else:
                rule_formats.append( format )
            rule_attributes[ 'fom_formats' ] = rule_formats
          
          # Expand patterns in rules
          while True:
            expanded_pattern = []
            last_end = 0
            for match in self._directories_regex.finditer( pattern ):
              c = pattern[ last_end : match.start() ]
              if c:
                expanded_pattern.append( c )
              attribute = match.group( 1 )
              expanded_pattern.append( self.shared_patterns[ attribute ] )
              last_end = match.end()
            if expanded_pattern:
              last = pattern[ last_end : ]
              if last:
                expanded_pattern.append( last )
              pattern = ''.join( expanded_pattern )
            else:
              break
          rules.append( [ pattern, rule_attributes ] )
  
  
  def _parse_patterns( self, patterns, dest_patterns ):
    for key, value in patterns.iteritems():
      if isinstance( value, dict ):
        self._parse_patterns( value, dest_patterns.setdefault( key, {} ) )
      else:
        pattern_rules = dest_patterns.setdefault( key, [] )
        for rule in value:
          pattern, rule_attributes = rule          
          for attribute in self._attributes_regex.findall( pattern ):
            definition = self.attribute_definitions.setdefault( attribute, {} )
            value = rule_attributes.get( attribute )
            if value is not None:
              definition[ 'values' ] = set( ( value, ) )
            elif 'fom_open_value' not in definition:
              definition[ 'fom_open_value' ] = True
              #raise ValueError( 'Attribute "%s" must be declared in attribute_definitions' % attribute )
            if attribute in rule_attributes:
              pattern = pattern.replace( '<' + attribute + '>', rule_attributes[ attribute ] )
          i = pattern.find( ':' )
          if i > 0:
            rule_attributes[ 'fom_directory' ] = pattern[ :i ]
            pattern = pattern[ i+1: ]
          pattern_rules.append( [ pattern, rule_attributes ] )
          self.rules.append( [ pattern, rule_attributes ] )

          
  def pprint( self, out=sys.stdout ):
    for i in ( 'fom_names', 'attribute_definitions', 'formats', 'format_lists', 'shared_patterns', 'patterns', 'rules' ):
      print >> out, '-' * 20, i, '-' * 20 
      pprint.pprint( getattr( self, i ), out )

       
class PathToAttributes( object ):
  def __init__( self, foms, selection=None ):
    self._attributes_regex = re.compile( '<([^>]*)>' )
    self.hierarchical_patterns = {}
    for rule_pattern, rule_attributes in foms.selected_rules( selection ):
      rule_formats = rule_attributes.get( 'fom_formats', [] )
      parent = self.hierarchical_patterns
      attributes_found = set()
      splited_pattern = rule_pattern.split( '/' )
      count = 0
      for pattern in splited_pattern:
        count += 1
        regex = [ '^' ]
        last_end = 0
        for match in self._attributes_regex.finditer( pattern ):
          c = pattern[ last_end : match.start() ]
          if c:
            regex.append( re.escape( c ) )
          attribute = match.group( 1 )
          if attribute in attributes_found:
            regex.append( '%(' + attribute + ')s' )
          else:
            attribute_type = foms.attribute_definitions[ attribute ]
            values = attribute_type.get( 'values' )
            if values:
              regex.append( '(?P<%s>%s)' % ( attribute, '|'.join( '(?:' + re.escape(i) + ')' for i in values ) ) )
            else:
              regex.append( '(?P<%s>.*)' % attribute )
            attributes_found.add( attribute )
          last_end = match.end()
        last = pattern[ last_end : ]
        if last:
          regex.append( re.escape( last ) )
        if count == len( splited_pattern ):
          if rule_formats:
            for format in rule_formats:
              extension = foms.formats[ format ]
              d = rule_attributes.copy()
              d[ 'fom_format' ] = format
              d.pop( 'fom_formats', None )
              parent.setdefault( ''.join( regex ) + '$', [ {}, {} ] )[ 0 ].setdefault( extension, [] ).append( d )
          else:
            parent.setdefault( ''.join( regex ) + '$', [ {}, {} ] )[ 0 ].setdefault( '', [] ).append( rule_attributes )
        else:
          parent = parent.setdefault( ''.join( regex ) + '$', [ {}, {} ] )[ 1 ]

          
  def parse_directory( self, dirdict, single_match=False, all_unknown=False ):
    return self._parse_directory( dirdict, [], self.hierarchical_patterns, {}, single_match, all_unknown )
  
  
  def _parse_directory( self, dirdict, path, hierarchical_patterns, pattern_attributes, single_match, all_unknown ):
    for name, content in dirdict.iteritems():
      st, content = content
      
      # Split extention on left most dot
      split = name.split( '.', 1 )
      name_no_ext = split[ 0 ]
      if len( split ) == 2:
        ext = split[ 1 ]
      else:
        ext = ''
      
      matched_directories = []
      matched = False
      #print '!parse!', name, pattern_attributes
      for pattern, rules_subpattern in hierarchical_patterns.iteritems():
        ext_rules, subpattern = rules_subpattern
        pattern = pattern % pattern_attributes
        match = re.match( pattern, name_no_ext )
        if match:
          #print '!parse! match', pattern
          matched = True
          new_attributes = match.groupdict()
          new_attributes.update( pattern_attributes )
          
          rules = ext_rules.get( ext )
          if rules:
            for rule_attributes in rules:
              new_attributes.update( rule_attributes )
              yield path + [ name ], st, new_attributes
              matched = True
              if single_match:
                break
          if subpattern:
            full_path = path + [ name ]
            matched_directories.append( ( full_path, subpattern, new_attributes ) )
            if single_match:
              break
      if not matched and all_unknown:
        yield path + [ name ], st, None
        if content:
          for i in self._parse_unknown_directory( content, path + [ name ] ):
            yield i
      else:
        for full_path, subpattern, new_attributes in matched_directories:
          if content:
            for i in self._parse_directory( content, full_path, subpattern, new_attributes, single_match, all_unknown ):
              yield i


  def _parse_unknown_directory( self, dirdict, path ):
    for name, content in dirdict.iteritems():
      st, content = content
      yield path + [ name ], st, None
      if content is not None:
        for i in self._parse_unknown_directory( content, path + [ name ] ):
          yield i

  
class AttributesToPaths( object ):
  def __init__( self, foms, selection=None, directories={} ):
    self.foms = foms
    self.selection = selection
    self.directories = directories
    self._db = sqlite3.connect( ':memory:' )
    self._db.execute( 'PRAGMA journal_mode = OFF;' )
    self._db.execute( 'PRAGMA synchronous = OFF;' )
    self.all_attributes = tuple( i for i in self.foms.attribute_definitions if i != 'fom_formats' )
    fom_format_index = self.all_attributes.index( 'fom_format' )
    sql = 'CREATE TABLE rules ( %s, fom_first, fom_rule )' % ','.join( repr( i ) for i in self.all_attributes )
    #print '!', sql
    self._db.execute( sql )
    sql_insert = 'INSERT INTO rules VALUES ( %s )' % ','.join( '?' for i in xrange( len( self.all_attributes ) + 2 ) )
    self.rules = []
    for pattern, rule_attributes in foms.selected_rules( self.selection ):
      pattern_attributes = set( self.foms._attributes_regex.findall( pattern ) )
      values =[]
      for attribute in self.all_attributes:
        value = rule_attributes.get( attribute )
        if not value and attribute in pattern_attributes:
          value = ''
        values.append( value )
      values.append( True )
      values.append( len( self.rules ) )
      self.rules.append( pattern.replace( '<', '%(' ).replace( '>', ')s' ) )
      fom_formats = rule_attributes.get( 'fom_formats' )
      if fom_formats and 'fom_format' not in rule_attributes:
        first = True
        for format in fom_formats:
          values[ -2 ] = first
          first = False
          values[ fom_format_index ] = format
          #print '!', sql_insert, values
          self._db.execute( sql_insert, values )
        #values[ fom_format_index ] = ''
        #print '!', sql_insert, values
        #self._db.execute( sql_insert, values )
      else:
        #print '!', sql_insert, values        
        self._db.execute( sql_insert, values )
    self._db.commit()
  
  
  def find_paths( self, attributes={} ):
    d = self.selection.copy()
    d.update( attributes )
    attributes = d
    #print '!1!', attributes, self.selection
    select = []
    select_attributes = []
    for attribute in self.all_attributes:
      value = attributes.get( attribute )
      if value is None:
        value = self.selection.get( attribute )
      if value is None:
        select.append( '(' + attribute + " != '' OR " + attribute + ' IS NULL )' )
      elif attribute == 'fom_format':
        selected_format = attributes.get( 'fom_format' )
        if selected_format == 'fom_first':
          select.append( 'fom_first = 1' )
        else:
          select.append( attribute + " = ?" )
          select_attributes.append( attribute )
      else:
        #select.append( '(' + attribute + " IN ( ?, '' ) OR " + attribute + ' IS NULL )' )
        select.append( attribute + " IN ( ?, '' )" )
        select_attributes.append( attribute )
    sql = 'SELECT fom_rule, fom_format FROM rules WHERE %s' % ' AND '.join( select )
    values = [ attributes[ i ] for i in select_attributes ]
    #print '!2!', sql, values
    for rule_index, format in self._db.execute( sql, values ):
      rule = self.rules[ rule_index ]
      rule_attributes = fom_formats = self.foms.rules[ rule_index ][ 1 ].copy()
      fom_formats = rule_attributes.pop( 'fom_formats', None )
      #print '!2.1!', rule
      if format:
        ext = self.foms.formats[ format ]
        rule_attributes[ 'fom_format' ] = format
        #print '!2.2!',rule % attributes + '.' + ext
        r = self._join_directory( rule % attributes + '.' + ext, rule_attributes )
        if r:
          yield r
      else:
        if fom_formats:
          rule_attributes = rule_attributes.copy()
          del rule_attributes[ 'fom_formats' ]
          for f in fom_formats:
            ext = self.foms.formats[ f ]
            #print '!2.3!',rule % attributes + '.' + ext
            rule_attributes[ 'fom_format' ] = f
            r = self._join_directory( rule % attributes + '.' + ext, rule_attributes )
            if r:
              yield r
        else:
          #print '!2.4!',rule % attributes
          r = self._join_directory( rule % attributes, rule_attributes )
          if r:
            yield r

  def find_discriminant_attributes( self ):
    result = []
    if self.rules:
      for attribute in self.all_attributes:
        sql = 'SELECT DISTINCT %s FROM rules' % attribute
        values = list( self._db.execute( sql ) )
        #print '!', attribute, values
        if len( values ) > 1 or values[ 0 ][ 0 ] == '':
          result.append( attribute )
    return result
      
      
    
    
  def _join_directory( self, path, rule_attributes ):
    fom_directory = rule_attributes.get( 'fom_directory' )
    if fom_directory:
      directory = self.directories.get( fom_directory )
      if directory:
        return ( os.path.join( directory, *path.split( '/' ) ), rule_attributes )
    return ( os.path.join( *path.split( '/' ) ), rule_attributes )
  
      
    
def call_before_application_initialization( application ):
    application.add_trait( 'fom_path', 
      ListStr( descr='Path for finding file organization models' ) )
    if application.install_directory:
        application.fom_path = [ os.path.join( application.install_directory, 
            'share', 'soma-base-' + short_version, 'foms' ) ]

            
def call_after_application_initialization( application ):
    application.fom_manager = FileOrganizationModelManager( application.fom_path )

if __name__ == '__main__':
    # First thing to do is to create an Application with name and version
    app = Application( 'soma.fom', '1.0' )
    # Register module to load and call functions before and/or after
    # initialization
    app.plugin_modules.append( 'soma.fom' )
    # Application initialization (e.g. configuration file may be read here)
    app.initialize()

    print app.fom_manager.find_foms()
    foms = app.fom_manager.load_foms( 'morphologist-brainvisa-1.0' )
    foms.pprint()
    print '=' * 40
    
    #pta = PathToAttributes( foms )
    #for path, st, attributes in pta.parse_directory( DirectoryAsDict( os.path.join( os.environ[ 'HOME' ], 'imagen_bv' ) ) ):
      #print os.path.join( *path ), '->', attributes
    
    atp = AttributesToPaths( foms, selection=dict( fom_process='morphologistProcess', fom_parameter='t1mri' ),
                             directories={ 'output' : '/output', 'input' : '/input', 'spm' : '/spm', 'shared' : '/shared' } )
    pprint.pprint( atp.rules )
    print '-' * 40
    print atp.all_attributes, ':', atp.find_discriminant_attributes()
    print '=' * 40
    
    atp = AttributesToPaths( foms, selection=dict( fom_process='morphologistProcess', fom_parameter='normalized_t1mri' ),
                             directories={ 'output' : '/output', 'input' : '/input', 'spm' : '/spm', 'shared' : '/shared' } )
    pprint.pprint( atp.rules )
    print '-' * 40
    print atp.all_attributes, ':', atp.find_discriminant_attributes()
    
    #selection = dict( protocol='P', subject='S', acquisition='A' )
    #for path, attributes in atp.find_paths( selection ):
      #print path, '\n  ->', attributes
    #print '=' * 40
    #selection[ 'fom_format' ] = 'fom_first'
    #for path, attributes in atp.find_paths( selection ):
      #print path, '\n  ->', attributes
    