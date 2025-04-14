"""
File Organization Model (FOM)
=============================

A FOM is a JSON file (dictionary) describing how to make filenames from a set of attributes.

FOM definition
--------------

Ex::

    {
        "fom_name": "morphologist-auto-nonoverlap-1.0",

        "fom_import": ["formats-brainvisa-1.0", "brainvisa-formats-3.2.0",
                      "shared-brainvisa-1.0"],

        "attribute_definitions" : {
          "acquisition" : {"default_value" : "default_acquisition"},
          "analysis" : {"default_value" : "default_analysis"},
          "sulci_recognition_session" :  {"default_value" : "default_session"},
          "graph_version": {"default_value": "3.1"},
        },

        "shared_patterns": {
          "acquisition": "<center>/<subject>/t1mri/<acquisition>",
          "analysis": "{acquisition}/<analysis>",
          "recognition_analysis": "{analysis}/folds/<graph_version>/<sulci_recognition_session>_auto",
        },

        "processes" : {
            "Morphologist" : {
                "t1mri":
                    [["input:{acquisition}/<subject>", "images"],
                "imported_t1mri":
                    [["output:{acquisition}/<subject>", "images"]],
                "t1mri_referential":
                    [["output:{acquisition}/registration/RawT1-<subject>_<acquisition>", "Referential"]],
                "reoriented_t1mri":
                    [["output:{acquisition}/<subject>", "images"]],
                "t1mri_nobias":
                    [["output:{analysis}/nobias_<subject>", "images" ]],
                "split_brain":
                    [["output:{analysis}/segmentation/voronoi_<subject>","images"]],
                "left_graph":
                    [["output:{analysis}/folds/<graph_version>/<side><subject>",
                        "Graph and data",
                        {"side": "L", "labelled": "No"}]],
                "left_labelled_graph":
                    [["output:{recognition_analysis}/<side><subject>_<sulci_recognition_session>_auto",
                        "Graph and data", {"side": "L"}]],
                "right_graph":
                    [["output:{analysis}/folds/<graph_version>/<side><subject>",
                        "Graph and data", {"side":"R","labelled":"No"}]],
                "right_labelled_graph":
                    [["output:{recognition_analysis}/<side><subject>_<sulci_recognition_session>_auto",
                        "Graph and data", {"side": "R"}]],
                "Talairach_transform":
                    [["output:{acquisition}/registration/RawT1-<subject>_<acquisition>_TO_Talairach-ACPC",
                        "Transformation matrix"]]
            }
        }
    }

The dictionary may contain:

**fom_name**: string
    identifier of the FOM model. Several FOMs may coexist under different
    identifiers.

**fom_import**: list
    dependencies between FOMs. A Fom may import others to benefit from its
    formats, patterns etc.

**attribute_definitions**: dict
    a dict of predefines attributes. It is generally used to define default
    values for some attributes. Each attribute defined here is also a dict. In
    this sub-dict, the key "default_value" provides the attribute default
    value.

    Attributes don't *need* to be defined here, they are automatically defined
    as they are used in path patterns. But here we can assign them additional
    information (typically default values).

**shared_patterns**: dict
    mapping of reusable patterns. Such patterns will be replaced with their
    contents when used in the file paths patterns. To use such a pattern, place
    it with brackets {} in file paths patterns::

        "input:{acquisition}/<subject>"

    here ``{acquisition}`` is the *shared pattern* "acquisition", and
    ``<subject>`` is the *attribute* "subject"

    A pattern definition may also use attributes between ``<attribute_name>``
    quotes, and / or reuse other patterns between ``{pattern}`` curly brackets.

**processes**: dict
    dictionary of processes supported by the FOM, and path definitions for
    their parameters. The dict is organized by process, then in each process a
    sub-dict contains its parameters definitions. For a given parameter, a list
    of the FOM rules is given: several rules are allowed.

    Process names keys may be a fully qualified module/class name, or a short
    identifier, or a "contextual" name: the name a process has in the context
    of a pipeline.

    A FOM rule is a list of 2 or 3 elements::

        [patterrn, formats, attributes]

    *pattern*: string
        the FOM pattern for the file path of the given parameter. A pattern
        starts with a directory identifier (``input``, ``output``,
        ``shared``), followed by a semicolon (``:``), and a file pattern which
        may contain attributes (``<attrib>``) and/or shared patterns
        (``{pattern}``). Ex::

            "input:{acquisition}/<subject>"

    *formats*: string or list
        name of a format, a formats list, or a list of allowed formats names.
        The formats will rule the possible file extensions.

    *attributes*: dict, optional
        An optional dict assigning locally some attributes values. Ex::

            {"side": "left"}

        The attributes values here are used both to replace attributes values in the current file path pattern, and to select the matching rule when attributes values are given externally (hm, to be checked actually).

A FOM file is a JSON file (actually a JSON/YAML extended file, to allow comments within it), which should be placed in a common directory where the FOM manager will look for it (``share/foms/``)

How to use FOMS
---------------

At higher level, they are used for instance in `CAPSUL <https://brainvisa.info/capsul/>`_.

At lower level, they are used through several classes:

* :class:`FileOrganizationModelManager` manages a set of FOMs, looks for them in a search path, reads them.
* :class:`FileOrganizationModels` represents a FOM rules set.
* :class:`AttributesToPaths` is used to convert a set of attributes into filenames (which is the main use of FOMs).
* :class:`PathToAttributes` performs the reverse operation: match attributes and determines their values from a given filename.

"""

import json
import sys
import os
import os.path as osp
import pprint
import re
import sqlite3
import stat
import sys
import time

try:
    import bz2
except ImportError:
    bz2 = None

from collections import OrderedDict

from soma.controller import List, undefined

try:
    import yaml

    class json_reader:
        """
        This class has a single static method load that loads an
        JSON file with two features not provided by all JSON readers:

        - JSON syntax is extended. For instance comments are allowed.
        - The order of elements in dictionaries can be preserved by
          using parameter object_pairs_hook=OrderedDict (as in Python
          2.7 JSON reader).
        """

        @staticmethod
        def load(stream, object_pairs_hook=dict):
            class OrderedLoader(yaml.Loader):
                pass

            def construct_mapping(loader, node):
                loader.flatten_mapping(node)
                return object_pairs_hook(loader.construct_pairs(node))

            OrderedLoader.add_constructor(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
            )
            return yaml.load(stream, OrderedLoader)

except ImportError:
    import json as json_reader

from soma.path import split_path


def deep_update(update, original):
    """
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    """
    for key, value in original.items():
        if key not in update:
            update[key] = value
        elif isinstance(value, dict):
            deep_update(update[key], value)
        elif value != update[key]:
            raise ValueError(
                f"In deep_update, for key {key!r}, cannot merge {update[key]!r} and {value!r}"
            )


def read_json(file_name):
    """Read a json-like file using yaml or json.
    In case of failure, issue a clearer message with filename, and when
    appropriate a warning about yaml not being installed.
    """
    try:
        with open(file_name, "r") as f:
            return json_reader.load(f, object_pairs_hook=OrderedDict)
    except ValueError as e:
        if json_reader.__name__ != "yaml":
            extra_msg = ' Check your python installation, and perhaps un a "pip install PyYAML" or "easy_install PyYAML"'
        else:
            extra_msg = ""
        raise ValueError(
            f"{file_name}: {e}. This may be due to yaml module not installed.{extra_msg}"
        ) from e


class DirectoryAsDict:
    def __new__(cls, directory, cache=None):
        if osp.isdir(directory):
            return super().__new__(cls, directory, cache)
        else:
            with open(directory) as f:
                return json.load(f)

    def __init__(self, directory, cache=None):
        self.directory = directory
        if cache is None:
            self.cache = DirectoriesCache()
        else:
            self.cache = cache

    def __repr__(self):
        return f"<DirectoryAsDict( {self.directory!r} )>"

    def iteritems(self):
        st_content = self.cache.get_directory(self.directory)
        if st_content is not None:
            st, content = st_content
            yield from content.items()
        else:
            try:
                listdir = os.listdir(self.directory)
            except OSError:
                yield "", [None, None]
                return
            for name in listdir:
                full_path = osp.join(self.directory, name)
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
        return DirectoryAsDict._get_directory(directory, debug, 0, 0, 0, 0, 0, 0, 0)[0]

    @staticmethod
    def _get_directory(
        directory,
        debug,
        directories,
        files,
        links,
        files_size,
        path_size,
        errors,
        count,
    ):
        try:
            listdir = os.listdir(directory)
            result = {}
        except OSError:
            errors += 1
            result = None
        if result is not None:
            for name in listdir:
                if debug and count % 100 == 0:
                    debug.info(
                        "%s files=%d, directories=%d, size=%d",
                        time.asctime(),
                        files + links,
                        directories,
                        files_size,
                    )
                path_size += len(name)
                count += 1
                full_path = osp.join(directory, name)
                st = os.lstat(full_path)
                if stat.S_ISREG(st.st_mode):
                    files += 1
                    files_size += st.st_size
                    result[name] = [tuple(st), None]
                elif stat.S_ISDIR(st.st_mode):
                    (
                        content,
                        directories,
                        files,
                        links,
                        files_size,
                        path_size,
                        errors,
                        count,
                    ) = DirectoryAsDict._get_directory(
                        full_path,
                        debug,
                        directories + 1,
                        files,
                        links,
                        files_size,
                        path_size,
                        errors,
                        count,
                    )
                    result[name] = [tuple(st), content]
                else:
                    links += 1
                    result[name] = [tuple(st), None]
        return result, directories, files, links, files_size, path_size, errors, count

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
        return DirectoryAsDict._get_statistics(dirdict, debug, 0, 0, 0, 0, 0, 0, 0)[:-1]

    @staticmethod
    def _get_statistics(
        dirdict, debug, directories, files, links, files_size, path_size, errors, count
    ):
        if debug and count % 100 == 0:
            debug.info(
                "%s files=%d, directories=%d, size=%d",
                time.asctime(),
                files + links,
                directories,
                files_size,
            )
        count += 1
        for name, content in dirdict.items():
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
                        (
                            directories,
                            files,
                            links,
                            files_size,
                            path_size,
                            errors,
                            count,
                        ) = DirectoryAsDict._get_statistics(
                            content,
                            debug,
                            directories + 1,
                            files,
                            links,
                            files_size,
                            path_size,
                            errors,
                            count,
                        )
                else:
                    links += 1
            else:
                errors += 1
        return (directories, files, links, files_size, path_size, errors, count)


class DirectoriesCache:
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
        if bz2:
            f = bz2.BZ2File(path, "w")
        else:
            f = open(path, "w")
        with f:
            json.dump(self.directories, f)

    @classmethod
    def load(cls, path):
        result = cls()
        if bz2:
            try:
                with bz2.BZ2File(path, "r") as f:
                    result.directories = json.load(f)
            except OSError:
                with open(path, "r") as f:
                    result.directories = json.load(f)
        else:
            with open(path, "r") as f:
                result.directories = json.load(f)
        return result


class FileOrganizationModelManager:
    """
    Manage the discovery and instantiation of available FileOrganizationModel
    (FOM). A FOM can be represented as a YAML/JSON file (or a series of
    YAML/JSON files in a directory). This class allows to identify these files
    contained in a predefined set of directories (see find_fom method) and to
    instantiate a FileOrganizationModel for each identified file (see get_fom
    method).
    """

    def __init__(self, paths=None):
        """
        Create a FOM manager that will use the given paths to find available FOMs.
        """
        if paths is None:
            paths = [
                osp.join(
                    osp.dirname(osp.dirname(osp.dirname(__file__))), "share", "foms"
                )
            ]
        self.paths = paths
        self._cache = None

    def find_foms(self):
        """Return a list of file organisation model (FOM) names.
        These FOMs can be loaded with load_foms. FOM files (or directories) are
        looked for in self.paths."""
        # print('*** find_foms ***')
        # import time
        # t0 = time.time()
        self._cache = {}
        for path in self.paths:
            # print('   ', path)
            if os.path.isdir(path):
                for i in os.listdir(path):
                    full_path = osp.join(path, i)
                    if osp.isdir(full_path):
                        for ext in (".json", ".yaml"):
                            main_file = osp.join(full_path, i + ext)
                            if osp.exists(main_file):
                                d = read_json(main_file)
                                name = d.get("fom_name")
                                if not name:
                                    raise ValueError(
                                        f"file {main_file} does not contain fom_name"
                                    )
                                self._cache[name] = full_path
                    elif i.endswith(".json") or i.endswith(".yaml"):
                        d = read_json(full_path)
                        if d:
                            name = d.get("fom_name")
                            if not name:
                                raise ValueError(
                                    f"file {full_path} does not contain fom_name"
                                )
                            self._cache[name] = full_path
        # print('    find_foms done: %f s' % (time.time() - t0))
        return list(self._cache.keys())

    def fom_files(self):
        """Return a list of file organisation model (FOM) names, as in
        :meth:`find_foms`, but does not clear and reload the cache.
        These FOMs can be loaded with load_foms. FOM files (or directories) are
        looked for in self.paths."""
        if not self._cache:
            self.find_foms()
        return list(self._cache.keys())

    def clear_cache(self):
        self._cache = None

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
                stack.extend(json.get("fom_import", []))
        jsons = list(jsons.values())
        result = jsons.pop(0)
        for json in jsons:
            for n in (
                "attribute_definitions",
                "formats",
                "format_lists",
                "shared_patterns",
                "patterns",
                "processes",
            ):
                d = json.get(n)
                if d:
                    deep_update(d, result.get(n, {}))
                    result[n] = d
            r = json.get("rules", [])
            if r:
                result.setdefault("rules", []).extend(r)
        return result


class FileOrganizationModels:
    def __init__(self):
        self._directories_regex = re.compile(r"{([A-Za-z][A-Za-z0-9_]*)}")
        self._attributes_regex = re.compile("<([^>]+)>")
        self.fom_names = []
        self.attribute_definitions = {
            "fom_name": {
                "descr": "File Organization Model (FOM) in which a pattern is defined.",
                "values": set(self.fom_names),
            },
            "fom_format": {
                "descr": "Format of a file.",
                "values": set(),
            },
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
            c = pattern[last_end : match.start()]
            if c:
                expanded_pattern.append(c)
            attribute = match.group(1)
            expanded_pattern.append(self.shared_patterns[attribute])
            last_end = match.end()
        if expanded_pattern:
            last = pattern[last_end:]
            if last:
                expanded_pattern.append(last)
            return "".join(expanded_pattern)
        else:
            return pattern

    def import_file(self, file_or_dict, foms_manager=None):
        if not isinstance(file_or_dict, dict):
            json_dict = read_json(file_or_dict)
        else:
            json_dict = file_or_dict

        foms = json_dict.get("fom_import", [])
        if foms and foms_manager is None:
            raise RuntimeError(
                "Cannot import FOM because no FileOrganizationModelManager has been provided"
            )
        for fom in foms:
            self.import_file(foms_manager.file_name(fom), foms_manager=foms_manager)

        fom_name = json_dict["fom_name"]
        if fom_name in self.fom_names:
            return
        self.fom_names.append(fom_name)

        # Update attribute definitions
        attribute_definitions = json_dict.get("attribute_definitions")
        if attribute_definitions:
            for attribute, definition in attribute_definitions.items():
                existing_definition = self.attribute_definitions.get(attribute)
                values = definition.get("values")
                if existing_definition:
                    existing_values = existing_definition.get("values")
                    # if (existing_values is None) != bool(values is None):
                    # print('ERROR:\nexisting_definition:', existing_definition)
                    # print('definition:', definition)
                    # raise ValueError(
                    #'Incompatible values redefinition for attribute '
                    #'%s, older: %s, new: %s in file: %s' % (
                    # attribute,
                    # existing_values,
                    # values,
                    # file_or_dict))
                    if (definition.get("default_value") is None) != (
                        existing_definition.get("default_value") is None
                    ):
                        raise ValueError(
                            "Incompatible default value redefinition of "
                            "attribute {}, older default: {}, new default: "
                            "{} in file: {}".format(
                                attribute,
                                existing_definition.get("default_value"),
                                definition.get("default_value"),
                                file_or_dict,
                            )
                        )
                    if values:
                        existing_values.extend(values)
                else:
                    definition = definition.copy()
                    if values is not None:
                        definition["values"] = set(values)
                    self.attribute_definitions[attribute] = definition

        # Process shared patterns to expand the ones that reference other shared
        # patterns
        self.formats.update(json_dict.get("formats", {}))
        self.format_lists.update(json_dict.get("format_lists", {}))
        self.shared_patterns.update(json_dict.get("shared_patterns", {}))
        if self.shared_patterns:
            stack = list(self.shared_patterns.items())
            while stack:
                name, pattern = stack.pop()
                if isinstance(pattern, list):
                    if pattern and isinstance(pattern[0], str):
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

        rules = json_dict.get("rules")
        patterns = json_dict.get("patterns", {}).copy()
        processes = json_dict.get("processes")

        if rules:
            patterns["fom_dummy"] = rules
        new_patterns = {}
        self._expand_json_patterns(patterns, new_patterns, {"fom_name": fom_name})
        self._parse_patterns(new_patterns, self.patterns)

        if processes:
            process_patterns = OrderedDict()
            for process, parameters in processes.items():
                process_dict = OrderedDict()
                process_patterns[process] = process_dict
                for parameter, rules in parameters.items():
                    if isinstance(rules, str):
                        rules = self.shared_patterns[rules[1:-1]]
                    parameter_rules = []
                    process_dict[parameter] = parameter_rules
                    for rule in rules:
                        if len(rule) == 2:
                            pattern, formats = rule
                            rule_attributes = {}
                        else:
                            try:
                                pattern, formats, rule_attributes = rule
                            except Exception:
                                print(
                                    f"error in FOM: {fom_name}, process: {process}, param: {parameter}, rule: {rule}"
                                )
                                raise
                        rule_attributes["fom_process"] = process
                        rule_attributes["fom_parameter"] = parameter
                        parameter_rules.append([pattern, formats, rule_attributes])
            new_patterns = OrderedDict()
            self._expand_json_patterns(
                process_patterns, new_patterns, {"fom_name": fom_name}
            )
            self._parse_patterns(new_patterns, self.patterns)

    def get_attributes_without_value(self):
        att_no_value = {}
        for att in self.shared_patterns:
            if not att.startswith("shared."):
                for attrec in self._attributes_regex.findall(self.shared_patterns[att]):
                    if attrec not in att_no_value:
                        att_no_value[attrec] = ""

        return att_no_value

    def selected_rules(self, selection, debug=None):
        if selection:
            format = selection.get("format")
            for rule_pattern, rule_attributes in self.rules:
                if debug:
                    debug.debug("selected_rules: %r, %r", rule_pattern, rule_attributes)
                rule_formats = rule_attributes.get("fom_formats", [])
                if format:
                    if format in ("fom_first", "fom_preferred"):
                        if not rule_formats:
                            if debug:
                                debug.debug("selected_rules: -- no format in rule")
                            continue
                    elif format not in rule_formats:
                        if debug:
                            debug.debug(
                                "selected_rules: -- format %r not in %r",
                                format,
                                rule_formats,
                            )
                        continue
                keep = True
                for attribute, selection_value in selection.items():
                    if attribute == "format":
                        continue
                    rule_value = rule_attributes.get(attribute)
                    if rule_value is None or rule_value != selection_value:
                        if debug:
                            debug.debug(
                                "selected_rules: -- selection value %r != rule value %r",
                                selection_value,
                                rule_value,
                            )
                        keep = False
                        break
                if keep:
                    if debug:
                        debug.debug("selected_rules: ++")
                    yield (rule_pattern, rule_attributes)
        else:
            yield from self.rules

    def _expand_json_patterns(self, json_patterns, parent, parent_attributes):
        attributes = parent_attributes.copy()
        attributes.update(json_patterns.get("fom_attributes", {}))
        for attribute, value in attributes.items():
            if attribute not in self.attribute_definitions:
                self.attribute_definitions[attribute] = {"values": set((value,))}
            else:
                values = self.attribute_definitions[attribute].setdefault(
                    "values", set()
                )
                values.add(value)

        key_attribute = json_patterns.get("fom_key_attribute", None)
        if key_attribute:
            self.attribute_definitions.setdefault(key_attribute, {})
            # raise ValueError( 'Attribute "%s" must be declared in
            # attribute_definitions' % key_attribute )

        for key, value in json_patterns.items():
            if key.startswith("fom_") and key != "fom_dummy":
                continue
            if key_attribute:
                attributes[key_attribute] = key
                self.attribute_definitions[key_attribute].setdefault(
                    "values", set()
                ).add(key)
            if isinstance(value, dict):
                self._expand_json_patterns(
                    value, parent.setdefault(key, OrderedDict()), attributes
                )
            else:
                rules = []
                parent[key] = rules
                for rule in value:
                    if len(rule) == 2:
                        pattern, format_list = rule
                        rule_attributes = attributes.copy()
                    else:
                        pattern, format_list, rule_attributes = rule
                        for attribute, value in rule_attributes.items():
                            definition = self.attribute_definitions.setdefault(
                                attribute, {}
                            )
                            values = definition.setdefault("values", set())
                            values.add(value)
                        if attributes:
                            new_attributes = attributes.copy()
                            new_attributes.update(rule_attributes)
                            rule_attributes = new_attributes

                    # Expand format_list
                    rule_formats = []
                    if isinstance(format_list, str):
                        format_list = [format_list]
                    if format_list:
                        for format in format_list:
                            formats = self.format_lists.get(format)
                            if formats is not None:
                                for f in formats:
                                    rule_formats.append(f)
                            else:
                                rule_formats.append(format)
                        rule_attributes["fom_formats"] = rule_formats

                    # Expand patterns in rules
                    while True:
                        expanded_pattern = []
                        last_end = 0
                        for match in self._directories_regex.finditer(pattern):
                            c = pattern[last_end : match.start()]
                            if c:
                                expanded_pattern.append(c)
                            attribute = match.group(1)
                            expanded_pattern.append(self.shared_patterns[attribute])
                            last_end = match.end()
                        if expanded_pattern:
                            last = pattern[last_end:]
                            if last:
                                expanded_pattern.append(last)
                            pattern = "".join(expanded_pattern)
                        else:
                            break
                    rules.append([pattern, rule_attributes])

    def _parse_patterns(self, patterns, dest_patterns):
        for key, value in patterns.items():
            if isinstance(value, dict):
                self._parse_patterns(
                    value, dest_patterns.setdefault(key, OrderedDict())
                )
            else:
                pattern_rules = dest_patterns.setdefault(key, [])
                for rule in value:
                    pattern, rule_attributes = rule
                    for attribute in self._attributes_regex.findall(pattern):
                        s = attribute.find("|")
                        if s > 0:
                            attribute = attribute[:s]
                        definition = self.attribute_definitions.setdefault(
                            attribute, {}
                        )
                        value = rule_attributes.get(attribute)
                        if value is not None:
                            definition.setdefault("values", set()).add(value)
                        elif "fom_open_value" not in definition:
                            definition["fom_open_value"] = True
                            # raise ValueError( 'Attribute "%s" must be
                            # declared in attribute_definitions' % attribute )
                        if attribute in rule_attributes:
                            pattern = pattern.replace(
                                "<" + attribute + ">", rule_attributes[attribute]
                            )
                    i = pattern.find(":")
                    if i > 0:
                        rule_attributes["fom_directory"] = pattern[:i]
                        pattern = pattern[i + 1 :]
                    pattern_rules.append([pattern, rule_attributes])
                    self.rules.append([pattern, rule_attributes])

    def pprint(self, out=sys.stdout):
        for i in (
            "fom_names",
            "attribute_definitions",
            "formats",
            "format_lists",
            "shared_patterns",
            "patterns",
            "rules",
        ):
            print("-" * 20, i, "-" * 20, file=out)
            pprint.pprint(getattr(self, i), out)


class PathToAttributes:
    """
    Utility class for file paths -> attributes set transformation.
    Part of the FOM engine.
    """

    def __init__(self, foms, selection=None):
        self._attributes_regex = re.compile("<([^>]+)>")
        self.hierarchical_patterns = OrderedDict()
        for rule_pattern, rule_attributes in foms.selected_rules(selection):
            rule_formats = rule_attributes.get("fom_formats", [])
            parent = self.hierarchical_patterns
            attributes_found = set()
            splited_pattern = rule_pattern.split("/")
            count = 0
            for pattern in splited_pattern:
                count += 1
                regex = ["^"]
                last_end = 0
                for match in self._attributes_regex.finditer(pattern):
                    c = pattern[last_end : match.start()]
                    if c:
                        regex.append(re.escape(c))
                    attribute = match.group(1)
                    s = attribute.find("|")
                    if s > 0:
                        attribute_re = attribute[s + 1 :]
                        attribute = attribute[:s]
                    else:
                        attribute_re = "[^/]*"
                    if attribute in attributes_found:
                        regex.append("%(" + attribute + ")s")
                    else:
                        attribute_type = foms.attribute_definitions[attribute]
                        values = attribute_type.get("values")
                        if values and not attribute_type.get("fom_open_value", True):
                            regex.append(
                                "(?P<{}>{})".format(
                                    attribute,
                                    "|".join(f"(?:{re.escape(i)})" for i in values),
                                )
                            )
                        else:
                            regex.append(f"(?P<{attribute}>{attribute_re})")
                        attributes_found.add(attribute)
                    last_end = match.end()
                last = pattern[last_end:]
                if last:
                    regex.append(re.escape(last))
                if count == len(splited_pattern):
                    if rule_formats:
                        for format in rule_formats:
                            if format not in foms.formats:
                                print(
                                    f'format "{format}" not if FOM "{foms.fom_names}"'
                                )
                            extension = foms.formats[format]
                            d = rule_attributes.copy()
                            d["fom_format"] = format
                            d.pop("fom_formats", None)
                            parent.setdefault(
                                "".join(regex) + "$", [OrderedDict(), OrderedDict()]
                            )[0].setdefault(extension, []).append(d)
                    else:
                        parent.setdefault(
                            "".join(regex) + "$", [OrderedDict(), OrderedDict()]
                        )[0].setdefault("", []).append(rule_attributes)
                else:
                    parent = parent.setdefault(
                        "".join(regex) + "$", [OrderedDict(), OrderedDict()]
                    )[1]

    def pprint(self, file=sys.stdout):
        self._pprint(file, self.hierarchical_patterns, 0)

    def _pprint(self, file, node, indent):
        if node:
            print("  " * indent + "{", file=file)
            for pattern, rules_subpattern in node.items():
                ext_rules, subpattern = rules_subpattern
                print("  " * (indent + 1) + repr(pattern) + ": { (", file=file)
                if ext_rules:
                    print("  " * (indent + 1) + "{", file=file)
                    for ext, rules in ext_rules.items():
                        print(
                            "  " * (indent + 2) + repr(ext) + ": ",
                            repr(rules),
                            file=file,
                        )
                    print("  " * (indent + 1) + "},", file=file)
                else:
                    print("  " * (indent + 1) + "{},", file=file)
                self._pprint(file, subpattern, indent + 1)
                print("),", file=file)
            print("  " * indent + "}", file=file, end=" ")
        else:
            print("  " * indent + "{}", file=file, end=" ")

    def parse_directory(self, dirdict, single_match=False, all_unknown=False, log=None):
        if isinstance(dirdict, str):
            dirdict = DirectoryAsDict.paths_to_dict(dirdict)
        return self._parse_directory(
            dirdict,
            [([], self.hierarchical_patterns, {})],
            single_match,
            all_unknown,
            log,
        )

    def _parse_directory(self, dirdict, parsing_list, single_match, all_unknown, log):
        for name, content in dirdict.items():
            st, content = content
            # Split extension on left most dot
            l = name.split(".")
            possible_extension_split = [
                (".".join(l[:i]), ".".join(l[i:])) for i in range(1, len(l) + 1)
            ]
            # split = name.split('.', 1)
            # name_no_ext = split[0]
            # if len(split) == 2:
            # ext = split[1]
            # else:
            # ext = ''

            matched_directories = []
            matched = False
            sent = False
            recurse_parsing_list = []
            for path, hierarchical_patterns, pattern_attributes in parsing_list:
                if log:
                    log.debug(
                        "?? %s %r %r",
                        name,
                        pattern_attributes,
                        list(hierarchical_patterns.keys()),
                    )
                branch_matched = False
                for pattern, rules_subpattern in hierarchical_patterns.items():
                    stop_parsing = False
                    for name_no_ext, ext in possible_extension_split:
                        ext_rules, subpattern = rules_subpattern
                        pattern = pattern % pattern_attributes
                        match = re.match(pattern, name_no_ext)
                        if log:
                            log.debug("try %r for %r", pattern, name_no_ext)
                        if match:
                            if log:
                                log.debug("match %s", pattern)
                            new_attributes = match.groupdict()
                            new_attributes.update(pattern_attributes)

                            rules = ext_rules.get(ext)
                            if (
                                subpattern
                                and not ext
                                and (st is None or stat.S_ISDIR(st[0]))
                                and content is not None
                            ):
                                matched = branch_matched = True
                                stop_parsing = single_match
                                full_path = path + [name]
                                if log:
                                    log.debug(
                                        "directory matched: %r %r",
                                        full_path,
                                        (
                                            [i[0] for i in content.items()]
                                            if content
                                            else None
                                        ),
                                    )
                                matched_directories.append(
                                    (full_path, subpattern, new_attributes)
                                )
                            else:
                                if log:
                                    log.debug("no directory matched for %r", name)
                            if rules is not None and ext:
                                matched = branch_matched = True
                                if log:
                                    log.debug("extension matched: %r", ext)
                                for rule_attributes in rules:
                                    yield_attributes = new_attributes.copy()
                                    yield_attributes.update(rule_attributes)
                                    stop_parsing = single_match or yield_attributes.pop(
                                        "fom_stop_parsing", False
                                    )
                                    if log:
                                        log.debug(
                                            "-> %s %r",
                                            "/".join(path + [name], yield_attributes),
                                        )
                                    sent = True
                                    yield path + [name], st, yield_attributes
                                break
                            else:
                                if log:
                                    log.debug("no extension matched: %r", ext)
                        if stop_parsing:
                            break
                    if stop_parsing:
                        break
                if branch_matched:
                    for full_path, subpattern, new_attributes in matched_directories:
                        if content:
                            recurse_parsing_list.append(
                                (full_path, subpattern, new_attributes)
                            )
            if recurse_parsing_list:
                for i in self._parse_directory(
                    content, recurse_parsing_list, single_match, all_unknown, log
                ):
                    yield i
            if not matched and all_unknown:
                if log:
                    log.debug("-> %s None", "/".join(path + [name]))
                sent = True
                yield path + [name], st, None
                if content:
                    for i in self._parse_unknown_directory(content, path + [name], log):
                        yield i
            if not sent and all_unknown:
                if log:
                    log.debug("-> %s None", "/".join(path + [name]))
                yield path + [name], st, None

    def _parse_unknown_directory(self, dirdict, path, log):
        for name, content in dirdict.items():
            st, content = content
            if log:
                log.debug("?-> %s None", "/".join(path + [name]))
            yield path + [name], st, None
            if content is not None:
                yield from self._parse_unknown_directory(content, path + [name], log)

    def parse_path(self, path, single_match=False, log=None):
        dirdict = DirectoryAsDict.paths_to_dict(path)
        spath = split_path(path)
        for p, s, a in self.parse_directory(
            dirdict, single_match=single_match, log=log
        ):
            if spath == p:
                yield (p, s, a)


class AttributesToPaths:
    """
    Utility class for attributes set -> file paths transformation.
    Part of the FOM engine.
    """

    def __init__(
        self, foms, selection=None, directories=None, preferred_formats=None, debug=None
    ):
        self.foms = foms
        self.selection = selection or {}
        self.directories = directories or {}
        self._db = sqlite3.connect(":memory:", check_same_thread=False)
        self._db.execute("PRAGMA journal_mode = OFF;")
        self._db.execute("PRAGMA synchronous = OFF;")
        self.all_attributes = tuple(
            i for i in self.foms.attribute_definitions if i != "fom_formats"
        )
        self.default_values = dict(
            (i, self.foms.attribute_definitions[i]["default_value"])
            for i in self.all_attributes
            if "default_value" in self.foms.attribute_definitions[i]
        )
        self.non_discriminant_attributes = set(
            i
            for i in self.all_attributes
            if not self.foms.attribute_definitions[i].get("discriminant", True)
        )
        preferred_formats = preferred_formats or set()
        fom_format_index = self.all_attributes.index("fom_format")
        sql = "CREATE TABLE rules ( {}, _fom_first, _fom_preferred_format, _fom_rule )".format(
            ",".join(repr("_" + str(i)) for i in self.all_attributes)
        )
        if debug:
            debug.debug(sql)
        self._db.execute(sql)
        columns = [
            f"_{i}" for i in self.all_attributes + ("fom_first", "fom_preferred_format")
        ]
        sql = "CREATE INDEX rules_index ON rules ({})".format(",".join(columns))
        self._db.execute(sql)
        for i in columns:
            sql = f"CREATE INDEX rules{i}_index ON rules ({i})"
            self._db.execute(sql)
        sql_insert = "INSERT INTO rules VALUES ( {} )".format(
            ",".join("?" for i in range(len(self.all_attributes) + 3))
        )
        self.rules = []
        for pattern, rule_attributes in foms.selected_rules(
            self.selection, debug=debug
        ):
            if debug:
                debug.debug("pattern: " + pattern + " " + repr(rule_attributes))
            pattern_attributes = set(
                (i if "|" not in i else i[: i.find("|")])
                for i in self.foms._attributes_regex.findall(pattern)
            )
            values = []
            for attribute in self.all_attributes:
                value = rule_attributes.get(attribute)
                if not value and attribute in pattern_attributes:
                    value = ""
                values.append(value)
            values.append(True)
            values.append(False)
            values.append(len(self.rules))
            self.rules.append(
                (re.sub(r"<([^>|]*)(\|[^>]*)?>", r"%(\1)s", pattern), rule_attributes)
            )
            fom_formats = rule_attributes.get("fom_formats")
            if fom_formats and "fom_format" not in rule_attributes:
                first = True
                for format in fom_formats:
                    if format in preferred_formats:
                        preferred_format = format
                        break
                else:
                    preferred_format = fom_formats[0]
                sys.stdout.flush()
                for format in fom_formats:
                    values[fom_format_index] = format
                    values[-3] = first
                    values[-2] = bool(format == preferred_format)
                    first = False
                    if debug:
                        debug.debug(sql_insert + " " + repr(values))
                    self._db.execute(sql_insert, values)
            else:
                if debug:
                    debug.debug(sql_insert + " " + repr(values))
                self._db.execute(sql_insert, values)
        self._db.commit()

    def find_paths(self, attributes=None, debug=None):
        attributes = attributes or {}
        if debug:
            debug.debug("!find_path! %r", attributes)
        d = self.selection.copy()
        d.update(attributes)
        attributes = d
        select = []
        values = []
        selection_attributes = {}
        default_values = []
        for attribute in self.all_attributes:
            value = attributes.get(attribute)
            if value is None:
                value = self.selection.get(attribute)
            if value is None:
                default_value = self.default_values.get(attribute)
                if default_value is not None:
                    default_values.append((attribute, default_value))
                    if attribute not in self.non_discriminant_attributes:
                        select.append(
                            f"(_{attribute} IN ('','{default_value}') OR "
                            f"_{attribute} IS NULL )"
                        )
                else:
                    if attribute not in self.non_discriminant_attributes:
                        select.append(f"(_{attribute} != '' OR _{attribute} IS NULL )")
            elif attribute == "fom_format":
                selected_format = attributes.get("fom_format")
                if selected_format == "fom_first":
                    select.append("_fom_first = 1")
                elif selected_format == "fom_preferred":
                    select.append("_fom_preferred_format = 1")
                elif isinstance(value, list):
                    select.append(
                        "_"
                        + attribute
                        + " IN ({})".format(",".join("?" for i in value))
                    )
                    values.extend(value)
                else:
                    select.append("_" + attribute + " = ?")
                    values.append(value)
            elif isinstance(value, list):
                if attribute not in self.non_discriminant_attributes:
                    select.append(
                        "_"
                        + attribute
                        + " IN ( {}, '' )".format(",".join("?" for i in value))
                    )
                    values.extend(value)
            else:
                if attribute not in self.non_discriminant_attributes:
                    select.append("_" + attribute + " IN ( ?, '' )")
                    values.append(value)
                    selection_attributes[attribute] = value
        columns = ["_fom_rule", "_fom_format"] + ["_" + i[0] for i in default_values]
        sql = "SELECT {} FROM rules WHERE {}".format(
            ",".join(columns),
            " AND ".join(select),
        )
        if debug:
            debug.debug(
                "!sql! %s", sql.replace("?", "%s") % tuple(repr(i) for i in values)
            )
        for row in self._db.execute(sql, values):
            rule_index, format = row[:2]
            row = row[2:]
            # bool_output = False
            rule, rule_attributes = self.rules[rule_index]
            rule_attributes = rule_attributes.copy()
            default_attributes = {}
            for i in range(len(default_values)):
                if not row[i]:
                    rule_attributes[default_values[i][0]] = default_values[i][1]
                    default_attributes[default_values[i][0]] = default_values[i][1]
            # rule_attributes = self.foms.rules[ rule_index ][ 1 ].copy()
            fom_formats = rule_attributes.pop("fom_formats", [])

            # if rule_attributes.get( 'fom_directory' ) == 'output':
            # bool_output=True

            if debug:
                debug.debug("!rule matching! %r", (rule, fom_formats, rule_attributes))
            if format:
                ext = self.foms.formats[format]
                if ext != "":
                    ext = "." + ext
                rule_attributes["fom_format"] = format
                default_attributes.update(attributes)
                try:
                    path = rule % default_attributes + ext
                except KeyError:
                    continue
                if debug:
                    debug.debug("!single format! %s: %s", format, path)
                r = self._join_directory(path, rule_attributes, selection_attributes)
                if r:
                    if debug:
                        debug.debug(f"!-->! {repr(r)}")
                    yield r
            else:
                if fom_formats:
                    for f in fom_formats:
                        ext = self.foms.formats[f]
                        if ext != "":
                            ext = "." + ext
                        rule_attributes["fom_format"] = f
                        default_attributes.update(attributes)
                        try:
                            path = rule % default_attributes + ext
                        except KeyError:
                            continue
                        if debug:
                            debug.debug("!format from fom_formats! %s: %s", f, path)
                        r = self._join_directory(
                            path, rule_attributes, selection_attributes
                        )
                        if r:
                            if debug:
                                debug.debug("!-->! %r", r)
                            yield r
                else:
                    default_attributes.update(attributes)
                    try:
                        path = rule % default_attributes
                    except KeyError:
                        continue
                    if debug:
                        debug.debug("!no format! %s", path)
                    r = self._join_directory(
                        path, rule_attributes, selection_attributes
                    )
                    if r:
                        if debug:
                            debug.debug("!-->! %r", r)
                        yield r

    def find_discriminant_attributes(self, **selection):
        result = []
        if self.rules:
            for attribute in self.all_attributes:
                sql = f'SELECT DISTINCT "_{attribute}" FROM rules'
                if selection:
                    sql += " WHERE " + " AND ".join("_" + i + " = ?" for i in selection)
                    values = list(self._db.execute(sql, list(selection.values())))
                else:
                    values = list(self._db.execute(sql))
                if values and (len(values) > 1 or ("",) in values):
                    result.append(attribute)
        return result

    def find_attributes_values(self, **selection):
        result = {}
        if self.rules:
            for attribute in self.all_attributes:
                sql = f'SELECT DISTINCT "_{attribute}" FROM rules'
                if selection:
                    sql += " WHERE " + " AND ".join("_" + i + " = ?" for i in selection)
                    values = list(self._db.execute(sql, list(selection.values())))
                else:
                    values = list(self._db.execute(sql))
                result[attribute] = values
        return result

    def _join_directory(self, path, rule_attributes, selection_attributes):
        attributes = selection_attributes.copy()
        attributes.update(rule_attributes)
        fom_directory = rule_attributes.get("fom_directory")
        if fom_directory:
            directory = self.directories.get(fom_directory)
            if directory:
                return (osp.join(directory, *path.split("/")), attributes)
                # return (osp.join(directory, path), attributes)
        return (osp.join(*path.split("/")), attributes)
        # return (path, attributes)

    def allowed_formats_for_parameter(self, process_name, param):
        formats = []
        for rule, attributes in self.rules:
            if (
                attributes.get("fom_process") == process_name
                and attributes.get("fom_parameter") == param
            ):
                rformats = attributes.get("fom_formats", [])
                for format in rformats:
                    if format not in formats:
                        formats.append(format)
        return formats

    def allowed_extensions_for_parameter(self, **kwargs):
        """
        Either formats or (process_name and param) should be passed
        kwargs
        ------
        formats: list of str
            if provided only this parameter will be used
        process_name: str
            name of the process
        param: str
            name of the process parameter
        """
        if "formats" in kwargs:
            formats = list(kwargs["formats"])
        elif "process_name" in kwargs and "param" in kwargs:
            process_name = kwargs["process_name"]
            param = kwargs["param"]
            formats = self.allowed_formats_for_parameter(process_name, param)
        else:
            raise KeyError(
                "Either formats or (process_name and param) should be passed"
            )
        exts = set()
        while formats:
            format = formats.pop(0)
            if format not in self.foms.formats and format in self.foms.format_lists:
                formats += self.foms.format_lists[format]
                continue
            exts.add(self.foms.formats[format])

        return sorted(exts)


def call_before_application_initialization(application):
    application.add_field(
        "fom_path",
        List[str],
        doc="Path for finding file organization models",
        default_factory=lambda: [],
    )
    if getattr(application, "install_directory", undefined):
        application.fom_path = [
            osp.join(application.install_directory, "share", "foms")
        ]


def call_after_application_initialization(application):
    application.fom_manager = FileOrganizationModelManager(application.fom_path)


if __name__ == "__main__":
    from soma.application import Application

    # First thing to do is to create an Application with name and version
    app = Application("soma.fom", "1.0")
    # Register module to load and call functions before and/or after
    # initialization
    app.plugin_modules.append("soma.fom")
    # Application initialization (e.g. configuration file may be read here)
    app.initialize()
    # process_completion( sys.argv[1], {'spm' : '/here/is/spm', 'shared' :
    # '/volatile/bouin/build/trunk/share/brainvisa-share-4.4' })

    import logging

    # logging.root.setLevel( logging.DEBUG )
    fom = app.fom_manager.load_foms("morphologist-brainvisa-pipeline-1.0")
    # atp = AttributesToPaths( fom, selection={ 'fom_process':'morphologistSimp.SimplifiedMorphologist' },
    # preferred_formats=set( ('NIFTI',) ),
    # debug=logging )
    # form='MINC'
    # form=','+'MESH'
    # print('form',form)
    directories = {
        "input_directory": "/input",
        "output_directory": "/output",
        "shared_directory": "/shared",
    }
    fomr = ["NIFTI", "MESH"]
    atp = AttributesToPaths(
        fom,
        selection={"fom_process": "morphologistPipeline.HeadMesh"},
        preferred_formats=fomr,
        directories=directories,
        debug=logging,
    )
    d = {
        "protocol": "subjects",
        "analysis": "default_analysis",
        "fom_parameter": "head_mesh",
        "acquisition": "default_acquisition",
        "subject": "002_S_0816_S18402_I40732",
        "fom_format": "fom_preferred",
    }
    for p, a in atp.find_paths(d, debug=logging):
        print("->", repr(p), a)
    # for parameter in fom.patterns[ 'morphologistSimp.SimplifiedMorphologist' ]:
    # print('- %s' % parameter)
    # for p, a in atp.find_paths( { 'fom_parameter': parameter,
    #'protocol': 'c',
    #'subject': 's',
    #'analysis': 'p',
    #'acquisition': 'a',
    #'fom_format': 'fom_preferred',
    # } ):
    # print(' ', repr( p ), a)
