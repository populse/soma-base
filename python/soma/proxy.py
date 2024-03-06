from collections.abc import MutableMapping, MutableSequence

"""
This module define DictWithProxy and ListWithPRoxy classes that behave like
dict and list but allows to proxy to values. When the same proxy is used at
several places in these containers, any change to one proxy value also changes
all other values of the same proxy.


Example:
--------
    from soma.api import DictWithProxy

    d = DictWithProxy()

    shared_value = d.proxy('a shared value')
    d['a list'] = ['a value', shared_value]
    d['another list'] = ['another value', shared_value]

    d['a list'][1] = 'modified shared value'
    print(d['another list'][1]) # prints "modified shared value"


Implementation is focused on the optimization of json serialization. There is
no need to recursively parse the internal structure to convert proxies to JSON.
Proxies are stored as a JSON compatible structure. Writing and reading JSON is
simply a matter of saving/loading existing structures.
"""


class ContainerWithProxy:
    """
    Class containing methods common to DictWithProxy and ListWithProxy
    """

    def __init__(self, proxy_values, content, all_proxies=None):
        """
        Create a container supporting proxy values.
        """
        super().__init__()
        self.proxy_values = proxy_values
        self.content = content
        if all_proxies is True:
            all_proxies = {}
        elif all_proxies is False:
            all_proxies = None
        self.all_proxies = all_proxies

    def proxy(self, value):
        """
        Add the value to the list of shared values of the container and the
        special structure that represents a proxy (i.e. a kind of pointer) to
        this value.
        """
        index = len(self.proxy_values)
        self.proxy_values.append(value)
        proxy = ["&", index]
        if self.all_proxies is not None:
            self.all_proxies[index] = [proxy]
        return proxy

    @staticmethod
    def is_proxy(value):
        """
        Checks if the value is a special structure representing a proxy to a
        shared value.
        """
        return isinstance(value, list) and len(value) == 2 and value[0] == "&"

    def get_value(self, value):
        """
        Transform an internal value in a user value. This does the
        following:
            - Resolve proxies to their values
            - Transform list to ListWithProxy
            - Transform dict to DictWithProxy
        """
        if self.is_proxy(value):
            return self.get_value(self.proxy_values[value[1]])
        elif isinstance(value, list):
            return ListWithProxy(
                _content=value,
                all_proxies=self.all_proxies,
                _proxy_values=self.proxy_values,
            )
        elif isinstance(value, dict):
            return DictWithProxy(
                _content=value,
                all_proxies=self.all_proxies,
                _proxy_values=self.proxy_values,
            )
        else:
            return value

    def set_proxy_value(self, proxy, value):
        """
        Modifies the value referenced by a proxy.
        """
        self.proxy_values[proxy[1]] = self.value_to_content(value)

    def value_to_content(self, value):
        """
        Transform a value given by user to a value that can be stored
        internally.
        """
        if isinstance(value, ContainerWithProxy):
            return value.content
        elif isinstance(value, dict):
            return dict((k, self.value_to_content(v)) for k, v in value.items())
        elif isinstance(value, list):
            return list(self.value_to_content(v) for v in value)
        else:
            return value

    def json_controller(self):
        """
        Return a structure that can be converted in JSON and converted back to
        a ContainerWithProxy using from_json_controller() method.
        """
        return {
            "proxy_values": self.proxy_values,
            "content": self.content,
        }

    @staticmethod
    def from_json_controller(json):
        """
        Recreate the appropriate container previously converted with json_controller()
        method.
        """
        proxy_values = json["proxy_values"]
        content = json["content"]
        if isinstance(content, list):
            return ListWithProxy(_content=content, _proxy_values=proxy_values)
        else:
            return DictWithProxy(_content=content, _proxy_values=proxy_values)

    def no_proxy(self, value=...):
        """
        Recursively resolve all proxies to shared values and return a standard dict.
        """
        if value is ...:
            value = self
        no_proxy = getattr(value, "_no_proxy", None)
        if no_proxy is not None:
            return no_proxy()
        return value


class DictWithProxy(MutableMapping, ContainerWithProxy):
    def __init__(self, init=None, all_proxies=False, _content=None, _proxy_values=None):
        """
        Creates a dict-like structure that supports proxies to shared values.
        """
        if _content is None:
            _content = {}
        if _proxy_values is None:
            _proxy_values = []
        super().__init__(_proxy_values, _content, all_proxies=all_proxies)
        if init is not None:
            for k, v in init:
                self[k] = v

    def __getitem__(self, key):
        return self.get_value(self.content[key])

    def __setitem__(self, key, value):
        current_value = self.content.get(key)
        if self.is_proxy(current_value):
            self.set_proxy_value(current_value, value)
        else:
            self.content[key] = self.value_to_content(value)

    def __delitem__(self, key):
        del self.content[key]

    def __iter__(self):
        return self.content.__iter__()

    def __len__(self):
        return self.content.__len__()

    def _no_proxy(self):
        """
        Recursively resolve all proxies to shared values and return a standard dict.
        """
        return dict((k, self.no_proxy(v)) for k, v in self.items())


class ListWithProxy(MutableSequence, ContainerWithProxy):
    def __init__(self, init=None, all_proxies=False, _content=None, _proxy_values=None):
        """
        Creates a list-like structure that supports proxies to shared values.
        """
        if _content is None:
            _content = []
        if _proxy_values is None:
            _proxy_values = []
        super().__init__(_proxy_values, _content, all_proxies=all_proxies)
        if init is not None:
            for v in init:
                self.append(v)

    def __getitem__(self, index):
        return self.get_value(self.content[index])

    def __setitem__(self, index, value):
        current_value = self.content[index]
        if self.is_proxy(current_value):
            self.set_proxy_value(current_value, value)
        else:
            self.content[index] = self.value_to_content(value)

    def __delitem__(self, key):
        del self.content[key]

    def __len__(self):
        return self.content.__len__()

    def insert(self, index, value):
        self.content.insert(index, None)
        self[index] = value

    def _no_proxy(self):
        """
        Recursively resolve all proxies to shared values and return a standard dict.
        """
        return [self.no_proxy(v) for v in self]
