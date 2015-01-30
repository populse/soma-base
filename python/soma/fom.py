# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys
import os
import stat
import time
import re
import pprint
import sqlite3
import bz2
import json
try:
    import yaml as json_reader
except ImportError:
    import json as json_reader


from soma.path import split_path
try :
  from collections import OrderedDict
except :
  # It is necessary to keep this for compatibility with python 2.6.*
  from soma.sorted_dictionary import SortedDictionary as OrderedDict


def deep_update(update, original):
    '''
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    '''
    for key, value in original.iteritems():
        if not key in update:
            update[key] = value
        elif isinstance(value, dict):
            deep_update(update[key], value)
        elif value != update[key]:
            raise ValueError('In deep_update, for key %s, cannot merge %s and %s' % (repr(key), repr(update[key]), repr(value)))


def read_json(file_name):
    ''' Read a json-like file using yaml or json.
    In case of failure, issue a clearer message with filename, and when
    appropriate a warning about yaml not being installed.
    '''
    try:
        return json_reader.load(open(file_name, 'r'))
    except ValueError, e:
        if json_reader.__name__ != 'yaml':
            extra_msg = ' Check your python installation, and perhaps un a "pip install PyYAML" or "easy_install PyYAML"'
        else:
            extra_msg = ''
        raise ValueError('%s: %s. This may be due to yaml module not installed.%s' % (file_name, str(e), extra_msg))


class DirectoryAsDict(object):

    def __new__(cls, directory, cache=None):
        if os.path.isdir(directory):
            return super(DirectoryAsDict, cls).__new__(cls, directory, cache)
        else:
            return json.load(open(directory))

    def __init__(self, directory, cache=None):
        self.directory = directory
        if cache is None:
            self.cache = DirectoriesCache()
        else:
            self.cache = cache

    def __repr__(self):
        return '<DirectoryAsDict( %s )>' % repr(self.directory)

    def iteritems(self):
        st_content = self.cache.get_directory(self.directory)
        if st_content is not None:
            st, content = st_content
            for i in content.iteritems():
                yield i
        else:
            try:
                listdir = os.listdir(self.directory)
            except OSError:
                yield '', [None, None]
                return
            for name in listdir:
                full_path = os.path.join(self.directory, name)
                st_content = self.cache.get_directory(full_path)
                if st_content is not None:
                    yield st_content
                else:
                    st = os.stat(full_path)
                    if stat.S_ISDIR(st.st_mode):
                        yield (name, [tuple(st), DirectoryAsDict(full_path)])
                    else:
                        yield (name, [tuple(st), None])

    @staticmethod
    def get_directory(directory, debug=None):
        return DirectoryAsDict._get_directory(
            directory, debug, 0, 0, 0, 0, 0, 0, 0)[0]

    @staticmethod
    def _get_directory(directory, debug, directories, files, links,
                       files_size, path_size, errors, count):
        try:
            listdir = os.listdir(directory)
            result = {}
        except OSError:
            errors += 1
            result = None
        if result is not None:
            for name in listdir:
                if debug and count % 100 == 0:
                    debug.info('%s files=%d, directories=%d, size=%d'
                               % (time.asctime(), files + links, directories,
                                  files_size))
                path_size += len(name)
                count += 1
                full_path = os.path.join(directory, name)
                st = os.lstat(full_path)
                if stat.S_ISREG(st.st_mode):
                    files += 1
                    files_size += st.st_size
                    result[name] = [tuple(st), None]
                elif stat.S_ISDIR(st.st_mode):
                    content, directories, files, links, files_size, \
                        path_size, errors, count =  \
                        DirectoryAsDict._get_directory(full_path, debug,
                                                       directories +
                                                       1, files, links, files_size,
                                                       path_size, errors, count)
                    result[name] = [tuple(st), content]
                else:
                    links += 1
                    result[name] = [tuple(st), None]
        return result, directories, files, links, files_size, path_size, \
            errors, count

    @staticmethod
    def paths_to_dict(*paths):
        result = {}
        for path in paths:
            current_dir = result
            path_list = split_path(path)
            for name in path_list[:-1]:
                st_content = current_dir.setdefault(name, [None, {}])
                if st_content[1] is None:
                    st_content[1] = {}
                current_dir = st_content[1]
            current_dir.setdefault(path_list[-1], [None, None])
        return result

    @staticmethod
    def get_statistics(dirdict, debug=None):
        return DirectoryAsDict._get_statistics(
            dirdict, debug, 0, 0, 0, 0, 0, 0, 0)[:-1]

    @staticmethod
    def _get_statistics(dirdict, debug, directories, files, links, files_size,
                        path_size, errors, count):

        if debug and count % 100 == 0:
            debug.info('%s files=%d, directories=%d, size=%d'
                       % (time.asctime(), files + links, directories, files_size))
        count += 1
        for name, content in dirdict.iteritems():
            path_size += len(name)
            st, content = content
            if st:
                st = os.stat(st)
                if stat.S_ISREG(st.st_mode):
                    files += 1
                    files_size += st.st_size
                elif stat.S_ISDIR(st.st_mode):
                    if content is None:
                        directories += 1
                        errors += 1
                    else:
                        directories, files, links, files_size, path_size, \
                            errors, count \
                            = DirectoryAsDict._get_statistics(
                                content, debug, directories + 1, files, links,
                                files_size, path_size, errors, count)
                else:
                    links += 1
            else:
                errors += 1
        return (directories, files, links, files_size, path_size, errors,
                count)


class DirectoriesCache(object):

    def __init__(self):
        self.directories = {}

    def add_directory(self, directory, content=None, debug=None):
        if content is None:
            st = tuple(os.stat(directory))
            content = DirectoryAsDict.get_directory(directory, debug=debug)
        else:
            st = None
        self.directories[directory] = [st, content]

    def remove_directory(self, directory):
        del self.directories[directory]

    def has_directory(self, directory):
        return directory in self.directories

    def get_directory(self, directory):
        return self.directories.get(directory)

    def save(self, path):
        f = bz2.BZ2File(path, 'w')
        json.dump(self.directories, f)

    @classmethod
    def load(cls, path):
        result = cls()
        f = bz2.BZ2File(path, 'r')
        result.directories = json.load(f)
        return result


class FileOrganizationModelManager(object):

    '''
    Manage the discovery and instanciation of available FileOrganizationModel
    (FOM). A FOM can be represented as a YAML/JSON file (or a series of
    YAML/JSON files in a directory). This class allows to identify these files
    contained in a predefined set of directories (see find_fom method) and to
    instanciate a FileOrganizationModel for each identified file (see get_fom
    method).
    '''

    def __init__(self, paths):
        '''
        Create a FOM manager that will use the given paths to find available FOMs.
        '''
        self.paths = paths
        self._cache = None

    def find_foms(self):
        '''Return a list of file organisation model (FOM) names.
        These FOMs can be loaded with load_foms. FOM files (or directories) are
        looked for in self.paths.'''
        self._cache = {}
        for path in self.paths:
            for i in os.listdir(path):
                full_path = os.path.join(path, i)
                if os.path.isdir(full_path):
                    for ext in ('.json', '.yaml'):
                        main_file = os.path.join(full_path, i + ext)
                        if os.path.exists(main_file):
                            d = read_json(main_file)
                            name = d.get('fom_name')
                            if not name:
                                raise ValueError(
                                    'file %s does not contain fom_name'
                                    % main_file)
                            self._cache[name] = full_path
                elif i.endswith('.json') or i.endswith('.yaml'):
                    d = read_json(full_path)
                    if d:
                        name = d.get('fom_name')
                        if not name:
                            raise ValueError(
                                'file %s does not contain fom_name'
                                % full_path)
                        self._cache[name] = full_path
        return self._cache.keys()

    def load_foms(self, *names):
        if self._cache is None:
            self.find_foms()
        foms = FileOrganizationModels()
        for name in names:
            foms.import_file(self._cache[name], foms_manager=self)
        return foms

    def file_name(self, fom):
        if self._cache is None:
            self.find_foms()
        return self._cache[fom]


    def read_definition(self, fom_name, done=None):
        jsons = OrderedDict()
        stack = [fom_name]
        while stack:
            fom_name = stack.pop(0)
            if fom_name not in jsons:
                json = jsons[fom_name] = read_json(self.file_name(fom_name))
                stack.extend(json.get('fom_import', []))
        jsons = jsons.values()
        result = jsons.pop(0)
        for json in jsons:
            for n in ('attribute_definitions','formats', 'format_lists', 'shared_patterns', 'patterns', 'processes'):
                d = json.get(n)
                if d:
                    deep_update(d, result.get(n,{}))
                    result[n] = d
            r = json.get('rules',[])
            if r:
                result.setdefault('rules',[]).extend(r)
        return result


class FileOrganizationModels(object):

    def __init__(self):
        self._directories_regex = re.compile(r'{([A-Za-z][A-Za-z0-9_]*)}')
        self._attributes_regex = re.compile('<([^>]+)>')
        self.fom_names = []
        self.attribute_definitions = {
            "fom_name": {
                "descr": "File Organization Model (FOM) in which a pattern is defined.",
                "values": set(self.fom_names),
            },
            "fom_format": {
                "descr": "Format of a file.",
                "values": set(),
            }
        }
        self.formats = {}
        self.format_lists = {}
        self.shared_patterns = {}
        self.patterns = {}
        self.rules = []

    def _expand_shared_pattern(self, pattern):
        expanded_pattern = []
        last_end = 0
        for match in self._directories_regex.finditer(pattern):
            c = pattern[last_end: match.start()]
            if c:
                expanded_pattern.append(c)
            attribute = match.group(1)
            expanded_pattern.append(self.shared_patterns[attribute])
            last_end = match.end()
        if expanded_pattern:
            last = pattern[last_end:]
            if last:
                expanded_pattern.append(last)
            return ''.join(expanded_pattern)
        else:
            return pattern

    def import_file(self, file_or_dict, foms_manager=None):
        if not isinstance(file_or_dict, dict):
            json_dict = read_json(file_or_dict)
        else:
            json_dict = file_or_dict

        foms = json_dict.get('fom_import', [])
        if foms and foms_manager is None:
            raise RuntimeError(
                'Cannot import FOM because no FileOrganizationModelManager has been provided')
        for fom in foms:
            self.import_file(
                foms_manager.file_name(fom), foms_manager=foms_manager)

        fom_name = json_dict['fom_name']
        if fom_name in self.fom_names:
            return
        self.fom_names.append(fom_name)

        # Update attribute definitions
        attribute_definitions = json_dict.get('attribute_definitions')
        if attribute_definitions:
            for attribute, definition in attribute_definitions.iteritems():
                existing_definition = self.attribute_definitions.get(
                    attribute)
                values = definition.get('values')
                if existing_definition:
                    existing_values = existing_definition.get('values')
                    if (existing_values is None) != bool(values is None):
                        raise ValueError(
                            'Incompatible values redefinition for attribute %s' % attribute)
                    if (definition.get('default_value') is None) != (existing_definition.get('default_value') is None):
                        raise ValueError(
                            'Incompatible default value redefinition of attribute %s' % attribute)
                    if values:
                        existing_values.extend(values)
                else:
                    definition = definition.copy()
                    if values is not None:
                        definition['values'] = set(values)
                    self.attribute_definitions[attribute] = definition

        # Process shared patterns to expand the ones that reference other shared
        # patterns
        self.formats.update(json_dict.get('formats', {}))
        self.format_lists.update(json_dict.get('format_lists', {}))
        self.shared_patterns.update(json_dict.get('shared_patterns', {}))
        if self.shared_patterns:
            stack = self.shared_patterns.items()
            while stack:
                name, pattern = stack.pop()
                if isinstance(pattern, list):
                    if pattern and isinstance(pattern[0], basestring):
                        pattern[0] = self._expand_shared_pattern(pattern[0])
                    else:
                        for i in pattern:
                            i[0] = self._expand_shared_pattern(i[0])
                else:
                    expanded_pattern = self._expand_shared_pattern(pattern)
                    if expanded_pattern != pattern:
                        stack.append((name, expanded_pattern))
                    else:
                        self.shared_patterns[name] = pattern

        rules = json_dict.get('rules')
        patterns = json_dict.get('patterns', {}).copy()
        processes = json_dict.get('processes')

        if rules:
            patterns['fom_dummy'] = rules
        new_patterns = {}
        self._expand_json_patterns(
            patterns, new_patterns, {'fom_name': fom_name})
        self._parse_patterns(new_patterns, self.patterns)

        if processes:
            process_patterns = {}
            for process, parameters in processes.iteritems():
                process_dict = {}
                process_patterns[process] = process_dict
                for parameter, rules in parameters.iteritems():
                    if isinstance(rules, basestring):
                        rules = self.shared_patterns[rules[1:-1]]
                    parameter_rules = []
                    process_dict[parameter] = parameter_rules
                    for rule in rules:
                        if len(rule) == 2:
                            pattern, formats = rule
                            rule_attributes = {}
                        else:
                            # print '!', rule, len( rule )
                            try:
                                pattern, formats, rule_attributes = rule
                            except Exception, e:
                                print 'error in FOM: %s, process: %s, param: %s, rule:' % (fom_name, process, parameter), rule
                                raise
                        rule_attributes['fom_process'] = process
                        rule_attributes['fom_parameter'] = parameter
                        parameter_rules.append(
                            [pattern, formats, rule_attributes])
            new_patterns = {}
            self._expand_json_patterns(
                process_patterns, new_patterns, {'fom_name': fom_name})
            self._parse_patterns(new_patterns, self.patterns)


    def get_attributes_without_value(self):
        att_no_value = {}
        for att in self.shared_patterns:
            if not att.startswith('shared.'):
                for attrec in self._attributes_regex.findall(self.shared_patterns[att]):
                    if attrec not in att_no_value:
                        att_no_value[attrec] = ''

        return att_no_value

    def selected_rules(self, selection, debug=None):
        if selection:
            format = selection.get('format')
            for rule_pattern, rule_attributes in self.rules:
                if debug:
                    debug.debug('selected_rules: %s, %s' %
                                (repr(rule_pattern), repr(rule_attributes)))
                rule_formats = rule_attributes.get('fom_formats', [])
                if format:
                    if format in ('fom_first', 'fom_prefered'):
                        if not rule_formats:
                            if debug:
                                debug.debug(
                                    'selected_rules: -- no format in rule')
                            continue
                    elif format not in rule_formats:
                        if debug:
                            debug.debug('selected_rules: -- format %s not in %s' % (repr(
                                format), repr(rule_formats)))
                        continue
                keep = True
                for attribute, selection_value in selection.iteritems():
                    if attribute == 'format':
                        continue
                    rule_value = rule_attributes.get(attribute)
                    if rule_value is None or rule_value != selection_value:
                        if debug:
                            debug.debug('selected_rules: -- selection value %s != rule value %s' %
                                        (repr(selection_value), repr(rule_value)))
                        keep = False
                        break
                if keep:
                    if debug:
                        debug.debug('selected_rules: ++')
                    yield (rule_pattern, rule_attributes)
        else:
            for rule in self.rules:
                yield rule

    def _expand_json_patterns(self, json_patterns, parent, parent_attributes):
        attributes = parent_attributes.copy()
        attributes.update(json_patterns.get('fom_attributes', {}))
        for attribute, value in attributes.iteritems():
            if attribute not in self.attribute_definitions:
                self.attribute_definitions[
                    attribute] = {'values': set((value,))}
            else:
                values = self.attribute_definitions[
                    attribute].setdefault('values', set())
                values.add(value)

        key_attribute = json_patterns.get('fom_key_attribute', None)
        if key_attribute:
            self.attribute_definitions.setdefault(key_attribute, {})
            # raise ValueError( 'Attribute "%s" must be declared in
            # attribute_definitions' % key_attribute )

        for key, value in json_patterns.iteritems():
            if key.startswith('fom_') and key != 'fom_dummy':
                continue
            if key_attribute:
                attributes[key_attribute] = key
                self.attribute_definitions[key_attribute].setdefault(
                    'values', set()).add(key)
            if isinstance(value, dict):
                self._expand_json_patterns(
                    value, parent.setdefault(key, {}), attributes)
            else:
                rules = []
                parent[key] = rules
                for rule in value:
                    if len(rule) == 2:
                        pattern, format_list = rule
                        rule_attributes = attributes.copy()
                    else:
                        pattern, format_list, rule_attributes = rule
                        for attribute, value in rule_attributes.iteritems():
                            definition = self.attribute_definitions.setdefault(
                                attribute, {})
                            values = definition.setdefault('values', set())
                            values.add(value)
                        if attributes:
                            new_attributes = attributes.copy()
                            new_attributes.update(rule_attributes)
                            rule_attributes = new_attributes

                    # Expand format_list
                    rule_formats = []
                    if isinstance(format_list, basestring):
                        format_list = [format_list]
                    if format_list:
                        for format in format_list:
                            formats = self.format_lists.get(format)
                            if formats is not None:
                                for f in formats:
                                    rule_formats.append(f)
                            else:
                                rule_formats.append(format)
                        rule_attributes['fom_formats'] = rule_formats

                    # Expand patterns in rules
                    while True:
                        expanded_pattern = []
                        last_end = 0
                        for match in self._directories_regex.finditer(pattern):
                            c = pattern[last_end: match.start()]
                            if c:
                                expanded_pattern.append(c)
                            attribute = match.group(1)
                            expanded_pattern.append(
                                self.shared_patterns[attribute])
                            last_end = match.end()
                        if expanded_pattern:
                            last = pattern[last_end:]
                            if last:
                                expanded_pattern.append(last)
                            pattern = ''.join(expanded_pattern)
                        else:
                            break
                    rules.append([pattern, rule_attributes])

    def _parse_patterns(self, patterns, dest_patterns):
        for key, value in patterns.iteritems():
            if isinstance(value, dict):
                self._parse_patterns(
                    value, dest_patterns.setdefault(key, {}))
            else:
                pattern_rules = dest_patterns.setdefault(key, [])
                for rule in value:
                    pattern, rule_attributes = rule
                    for attribute in self._attributes_regex.findall(pattern):
                        s = attribute.find('|')
                        if s > 0:
                            attribute = attribute[:s]
                        definition = self.attribute_definitions.setdefault(
                            attribute, {})
                        value = rule_attributes.get(attribute)
                        if value is not None:
                            definition.setdefault('values', set()).add(value)
                        elif 'fom_open_value' not in definition:
                            definition['fom_open_value'] = True
                            # raise ValueError( 'Attribute "%s" must be
                            # declared in attribute_definitions' % attribute )
                        if attribute in rule_attributes:
                            pattern = pattern.replace(
                                '<' + attribute + '>', rule_attributes[attribute])
                    i = pattern.find(':')
                    if i > 0:
                        rule_attributes['fom_directory'] = pattern[:i]
                        pattern = pattern[i + 1:]
                    pattern_rules.append([pattern, rule_attributes])
                    self.rules.append([pattern, rule_attributes])

    def pprint(self, out=sys.stdout):
        for i in ('fom_names', 'attribute_definitions', 'formats', 'format_lists', 'shared_patterns', 'patterns', 'rules'):
            print >> out, '-' * 20, i, '-' * 20
            pprint.pprint(getattr(self, i), out)


class PathToAttributes(object):
    '''
    Utility class for file paths -> attributes set transformation.
    Part of the FOM engine.
    '''

    def __init__(self, foms, selection=None):
        self._attributes_regex = re.compile('<([^>]+)>')
        self.hierarchical_patterns = OrderedDict()
        for rule_pattern, rule_attributes in foms.selected_rules(selection):
            rule_formats = rule_attributes.get('fom_formats', [])
            parent = self.hierarchical_patterns
            attributes_found = set()
            splited_pattern = rule_pattern.split('/')
            count = 0
            for pattern in splited_pattern:
                count += 1
                regex = ['^']
                last_end = 0
                for match in self._attributes_regex.finditer(pattern):
                    c = pattern[last_end: match.start()]
                    if c:
                        regex.append(re.escape(c))
                    attribute = match.group(1)
                    s = attribute.find('|')
                    if s > 0:
                        attribute_re = attribute[s + 1:]
                        attribute = attribute[:s]
                    else:
                        attribute_re = '[^/]*'
                    if attribute in attributes_found:
                        regex.append('%(' + attribute + ')s')
                    else:
                        attribute_type = foms.attribute_definitions[attribute]
                        values = attribute_type.get('values')
                        if values and not attribute_type.get('fom_open_value', True):
                            regex.append(
                                '(?P<%s>%s)' % (attribute, '|'.join('(?:' + re.escape(i) + ')' for i in values)))
                        else:
                            regex.append(
                                '(?P<%s>%s)' % (attribute, attribute_re))
                        attributes_found.add(attribute)
                    last_end = match.end()
                last = pattern[last_end:]
                if last:
                    regex.append(re.escape(last))
                if count == len(splited_pattern):
                    if rule_formats:
                        for format in rule_formats:
                            extension = foms.formats[format]
                            d = rule_attributes.copy()
                            d['fom_format'] = format
                            d.pop('fom_formats', None)
                            parent.setdefault(''.join(regex) + '$', [{}, {}])[
                                0].setdefault(extension, []).append(d)
                    else:
                        parent.setdefault(''.join(regex) + '$', [{}, {}])[
                            0].setdefault('', []).append(rule_attributes)
                else:
                    parent = parent.setdefault(
                        ''.join(regex) + '$', [{}, {}])[1]

    def pprint(self, file=sys.stdout):
        self._pprint(file, self.hierarchical_patterns, 0)

    def _pprint(self, file, node, indent):
        if node:
            print >> file, '  ' * indent + '{'
            for pattern, rules_subpattern in node.iteritems():
                ext_rules, subpattern = rules_subpattern
                print >> file, '  ' * (indent + 1) + repr(pattern) + ': { ('
                if ext_rules:
                    print >> file, '  ' * (indent + 1) + '{'
                    for ext, rules in ext_rules.iteritems():
                        print >> file, '  ' * \
                            (indent + 2) + repr(ext) + ': ', repr(rules)
                    print >> file, '  ' * (indent + 1) + '},'
                else:
                    print >> file, '  ' * (indent + 1) + '{},'
                self._pprint(file, subpattern, indent + 1)
                print >> file, '),'
            print >> file, '  ' * indent + '}',
        else:
            print >> file, '  ' * indent + '{}',

    def parse_directory(self, dirdict, single_match=False, all_unknown=False, log=None):
        return self._parse_directory(dirdict, [([], self.hierarchical_patterns, {})], single_match, all_unknown, log)

    def _parse_directory(self, dirdict, parsing_list, single_match, all_unknown, log):
        for name, content in dirdict.iteritems():
            st, content = content
            # Split extention on left most dot
            l = name.split('.')
            possible_extension_split = [('.'.join(l[:i]),'.'.join(l[i:])) for i in range(1,len(l)+1)]
            #split = name.split('.', 1)
            #name_no_ext = split[0]
            #if len(split) == 2:
                #ext = split[1]
            #else:
                #ext = ''

            matched_directories = []
            matched = False
            recurse_parsing_list = []
            for path, hierarchical_patterns, pattern_attributes in parsing_list:
                if log:
                    log.debug('?? ' + name + ' ' + repr(
                        pattern_attributes) + ' ' + repr(hierarchical_patterns.keys()))
                branch_matched = False
                for pattern, rules_subpattern in hierarchical_patterns.iteritems():
                    stop_parsing = False
                    for name_no_ext, ext in possible_extension_split:
                        ext_rules, subpattern = rules_subpattern
                        pattern = pattern % pattern_attributes
                        match = re.match(pattern, name_no_ext)
                        if log:
                            log.debug(
                                'try %s for %s' % (repr(pattern), repr(name_no_ext)))
                        if match:
                            if log:
                                log.debug('match ' + pattern)
                            new_attributes = match.groupdict()
                            new_attributes.update(pattern_attributes)

                            rules = ext_rules.get(ext)
                            if subpattern and not ext \
                                    and (st is None \
                                         or stat.S_ISDIR(os.stat(st).st_mode)):
                                matched = branch_matched = True
                                stop_parsing = single_match
                                full_path = path + [name]
                                if log:
                                    log.debug('directory matched: %s %s' % (
                                        repr(full_path), (repr([i[0] for i in content.iteritems()]) if content else None)))
                                matched_directories.append(
                                    (full_path, subpattern, new_attributes))
                            else:
                                if log:
                                    log.debug(
                                        'no directory matched for %s' % repr(name))
                            if rules is not None:
                                matched = branch_matched = True
                                if log:
                                    log.debug('extension matched: ' + repr(ext))
                                for rule_attributes in rules:
                                    yield_attributes = new_attributes.copy()
                                    yield_attributes.update(rule_attributes)
                                    stop_parsing = single_match or yield_attributes.pop(
                                        'fom_stop_parsing', False)
                                    if log:
                                        log.debug(
                                            '-> ' + '/'.join(path + [name]) + ' ' + repr(yield_attributes))
                                    yield path + [name], st, yield_attributes

                                break
                            else:
                                if log:
                                    log.debug(
                                        'no extension matched: ' + repr(ext))
                        if stop_parsing:
                            break
                    if stop_parsing:
                        break
                if branch_matched:
                    for full_path, subpattern, new_attributes in matched_directories:
                        if content:
                            recurse_parsing_list.append(
                                (full_path, subpattern, new_attributes))
            if recurse_parsing_list:
                for i in self._parse_directory(content, recurse_parsing_list, single_match, all_unknown, log):
                    yield i
            if not matched and all_unknown:
                if log:
                    log.debug('-> ' + '/'.join(path + [name]) + ' None')
                yield path + [name], st, None
                if content:
                    for i in self._parse_unknown_directory(content, path + [name], log):
                        yield i

    def _parse_unknown_directory(self, dirdict, path, log):
        for name, content in dirdict.iteritems():
            st, content = content
            if log:
                log.debug('?-> ' + '/'.join(path + [name]) + ' None')
            yield path + [name], st, None
            if content is not None:
                for i in self._parse_unknown_directory(content, path + [name], log):
                    yield i


class AttributesToPaths(object):
    '''
    Utility class for attributes set -> file paths transformation.
    Part of the FOM engine.
    '''

    def __init__(self, foms, selection=None, directories={}, prefered_formats=set(), debug=None):
        self.foms = foms
        self.selection = selection or {}
        self.directories = directories
        self._db = sqlite3.connect(':memory:')
        self._db.execute('PRAGMA journal_mode = OFF;')
        self._db.execute('PRAGMA synchronous = OFF;')
        self.all_attributes = tuple(
            i for i in self.foms.attribute_definitions if i != 'fom_formats')
        fom_format_index = self.all_attributes.index('fom_format')
        sql = 'CREATE TABLE rules ( %s, _fom_first, _fom_prefered_format, _fom_rule )' % ','.join(repr('_' + i)
                                                                                                  for i in self.all_attributes)
        if debug:
            debug.debug(sql)
        self._db.execute(sql)
        sql_insert = 'INSERT INTO rules VALUES ( %s )' % ','.join(
            '?' for i in xrange(len(self.all_attributes) + 3))
        self.rules = []
        for pattern, rule_attributes in foms.selected_rules(self.selection, debug=debug):
            if debug:
                debug.debug(
                    'pattern: ' + pattern + ' ' + repr(rule_attributes))
            pattern_attributes = set((i if '|' not in i else i[: i.find('|')])
                                     for i in self.foms._attributes_regex.findall(pattern))
            values = []
            for attribute in self.all_attributes:
                value = rule_attributes.get(attribute)
                if not value and attribute in pattern_attributes:
                    value = ''
                values.append(value)
            values.append(True)
            values.append(False)
            values.append(len(self.rules))
            self.rules.append(
                (re.sub(r'<([^>|]*)(\|[^>]*)?>', r'%(\1)s', pattern), rule_attributes))
            fom_formats = rule_attributes.get('fom_formats')
            if fom_formats and 'fom_format' not in rule_attributes:
                first = True
                for format in fom_formats:
                    if format in prefered_formats:
                        prefered_format = format
                        break
                else:
                    prefered_format = fom_formats[0]
                sys.stdout.flush()
                for format in fom_formats:
                    values[fom_format_index] = format
                    values[-3] = first
                    values[-2] = bool(format == prefered_format)
                    first = False
                    if debug:
                        debug.debug(sql_insert + ' ' + repr(values))
                    self._db.execute(sql_insert, values)
            else:
                if debug:
                    debug.debug(sql_insert + ' ' + repr(values))
                self._db.execute(sql_insert, values)
        self._db.commit()

    def find_paths(self, attributes={}, debug=None):
        d = self.selection.copy()
        d.update(attributes)
        attributes = d
        select = []
        select_attributes = []
        for attribute in self.all_attributes:
            value = attributes.get(attribute)
            if value is None:
                value = self.selection.get(attribute)
            if value is None:
                select.append(
                    '(_' + attribute + " != '' OR _" + attribute + ' IS NULL )')
            elif attribute == 'fom_format':
                selected_format = attributes.get('fom_format')
                if selected_format == 'fom_first':
                    select.append('_fom_first = 1')
                elif selected_format == 'fom_prefered':
                    select.append('_fom_prefered_format = 1')
                else:
                    select.append('_' + attribute + " = ?")
                    select_attributes.append(attribute)
            else:
                select.append('_' + attribute + " IN ( ?, '' )")
                select_attributes.append(attribute)
        sql = 'SELECT _fom_rule, _fom_format FROM rules WHERE %s' % ' AND '.join(
            select)
        values = [attributes[i] for i in select_attributes]
        if debug:
            debug.debug('!sql! %s', sql.replace('?', '%s') % tuple(values))
        for rule_index, format in self._db.execute(sql, values):
            # bool_output = False
            rule, rule_attributes = self.rules[rule_index]
            rule_attributes = rule_attributes.copy()
            # rule_attributes = self.foms.rules[ rule_index ][ 1 ].copy()
            fom_formats = rule_attributes.pop('fom_formats', [])

            # if rule_attributes.get( 'fom_directory' ) == 'output':
                # bool_output=True

            if debug:
                debug.debug('!rule matching! %s' %
                            repr((rule, fom_formats, rule_attributes)))
            if format:
                ext = self.foms.formats[format]
                rule_attributes['fom_format'] = format
                if debug:
                    debug.debug('!single format! %s: %s' % (
                        format, rule % attributes + '.' + ext))
                r = self._join_directory(
                    rule % attributes + '.' + ext, rule_attributes)
                if r:
                    yield r
            else:
                if fom_formats:
                    for f in fom_formats:
                        ext = self.foms.formats[f]
                        rule_attributes['fom_format'] = f
                        if debug:
                            debug.debug('!format from fom_formats! %s: %s' %
                                        (f, rule % attributes + '.' + ext))
                        r = self._join_directory(
                            rule % attributes + '.' + ext, rule_attributes)
                        if r:
                            yield r
                else:
                    if debug:
                        debug.debug('!no format! %s' % rule % attributes)
                    r = self._join_directory(
                        rule % attributes, rule_attributes)
                    if r:
                        yield r

    def find_discriminant_attributes(self, **selection):
        result = []
        if self.rules:
            for attribute in self.all_attributes:
                sql = 'SELECT DISTINCT %s FROM rules' % ('_' + attribute)
                if selection:
                    sql += ' WHERE ' + \
                        ' AND '.join('_' + i + ' = ?' for i in selection)
                    values = list(self._db.execute(sql, selection.values()))
                else:
                    values = list(self._db.execute(sql))
                if values and (len(values) > 1 or ('',) in values):
                    result.append(attribute)
        return result

    def _join_directory(self, path, rule_attributes):
        fom_directory = rule_attributes.get('fom_directory')
        if fom_directory:
            directory = self.directories.get(fom_directory)
            if directory:
                return (os.path.join(directory, *path.split('/')), rule_attributes)
        return (os.path.join(*path.split('/')), rule_attributes)


def call_before_application_initialization(application):
    try:
        from traits.api import ListStr
    except ImportError:
        from enthought.traits.api import ListStr

    application.add_trait('fom_path',
                          ListStr(descr='Path for finding file organization models'))
    if application.install_directory:
        application.fom_path = [os.path.join(application.install_directory,
                                             'share', 'foms')]


def call_after_application_initialization(application):
    application.fom_manager = FileOrganizationModelManager(
        application.fom_path)


if __name__ == '__main__':
    from soma.application import Application
    # First thing to do is to create an Application with name and version
    app = Application('soma.fom', '1.0')
    # Register module to load and call functions before and/or after
    # initialization
    app.plugin_modules.append('soma.fom')
    # Application initialization (e.g. configuration file may be read here)
    app.initialize()
    # process_completion( sys.argv[1], {'spm' : '/here/is/spm', 'shared' :
    # '/volatile/bouin/build/trunk/share/brainvisa-share-4.4' })

    from pprint import pprint
    import logging
    # logging.root.setLevel( logging.DEBUG )
    fom = app.fom_manager.load_foms('morphologist-brainvisa-pipeline-1.0')
    # atp = AttributesToPaths( fom, selection={ 'fom_process':'morphologistSimp.SimplifiedMorphologist' },
                             # prefered_formats=set( ('NIFTI',) ),
                             # debug=logging )
    # form='MINC'
    # form=','+'MESH'
    # print 'form',form
    directories = {"input_directory": "/input",
                   "output_directory": "/output",
                   "shared_directory": "/shared"}
    fomr = ['NIFTI', 'MESH']
    atp = AttributesToPaths(
        fom, selection={'fom_process': 'morphologistPipeline.HeadMesh'},
        prefered_formats=fomr, directories=directories,
        debug=logging)
    d = {
        'protocol': u'subjects', 'analysis': 'default_analysis', 'fom_parameter': 'head_mesh',
        'acquisition': 'default_acquisition', 'subject': u'002_S_0816_S18402_I40732', 'fom_format': 'fom_prefered'}
    for p, a in atp.find_paths(d, debug=logging):
        print '->', repr(p), a
    # for parameter in fom.patterns[ 'morphologistSimp.SimplifiedMorphologist' ]:
        # print '- %s' % parameter
        # for p, a in atp.find_paths( { 'fom_parameter': parameter,
                                      #'protocol': 'c',
                                      #'subject': 's',
                                      #'analysis': 'p',
                                      #'acquisition': 'a',
                                      #'fom_format': 'fom_prefered',
                                #} ):
        # print ' ', repr( p ), a
