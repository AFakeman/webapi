import urllib.request
import urllib.parse
import json

class RemoteOpener:
    'Function-like object, opens url with provided data and headers'
    def __init__(self, url, data = None, headers = None):
        if data:
            url = "{0}?{1}".format(url, urllib.parse.urlencode(data))
        if headers:
            headers = {}
        self.request = urllib.request.Request(url, headers=headers)

    def __call__(self):
        return urllib.request.urlopen(self.request)

class RefreshMethod:
    'Method that is used to fetch new data for a provided CacheMethod'
    def __init__(self, method_name, cache, openers):
        self.method_name = method_name
        self.cache = cache
        self.openers = openers
    def __call__(self):
        self.cache[self.method_name] = self.openers[self.method_name]()

class CacheMethod:
    """Method that is used as a proxy for opening urls like DirectMethod,
    but operates using cached version provided by RefreshMethod"""
    def __init__(self, method_name, cache, refresh_method):
        self.method_name = method_name
        self.cache = cache
        self.refresh_method = refresh_method
    def __call__(self):
        if not self.method_name in self.cache:
            self.refresh_method()
        return self.cache[self.method_name]

class DirectMethod:
    "Method that is used as a proxy for opening urls"
    def __init__(self, method_name, openers):
        self.method_name = method_name
        self.openers = openers
    def __call__(self):
        return self.openers[self.method_name]()

class JSONParseMethod:
    "Used as a public function in API, decodes json provided by method"
    def __init__(self, method):
        self.method = method
    def __call__(self):
        return json.loads(self.method().read().decode("UTF-8"), "UTF-8")

def template_init (self, **kwargs):
    """Templated initializer, accepts all arguments from config, and only them,
    also adds all the methods from config"""
    self.cache = {}
    self.openers = {}
    for key, value in kwargs.items():
        found = False
        for method_name, method in self.methods.items():
            if key in method["data_args"]:
                method["data"][method["data_args"][key]] = value
                found = True
            if key in method["header_args"]:
                method["headers"][method["header_args"][key]] = value
                found = True
        if not found:
            raise ValueError("Unknown kwarg: " + key)
    for method_name, method in self.methods.items():
        self.openers[method_name] = RemoteOpener(url=method["url"], headers=method["headers"], data=method["data"])
        if method["refresh_method"]:
            refresh_method = RefreshMethod(method_name=method_name, cache=self.cache, openers=self.openers)
            cache_method = CacheMethod(method_name=method_name, cache=self.cache, refresh_method=refresh_method)
            self.__dict__[method["refresh_method"]] = refresh_method
            self.__dict__[method_name] = JSONParseMethod(cache_method)
        else:
            direct_method = DirectMethod(method_name=method_name, openers=self.openers)
            self.__dict__[method_name] = JSONParseMethod(direct_method)


class WebApi:
    def __init__(self, config):
        self.classes = {}
        with open(config, "r") as f:
            config_dict = json.load(f)
        if "variables" in config_dict:
            variables = config_dict["variables"]
        else:
            variables = {}
        for class_name, class_ in config_dict["classes"].items():
            methods = {}
            method_set = set()
            if "fields" in class_:
                fields = class_["fields"]
            else:
                fields = {}

            if "arguments" in class_:
                arguments = class_["arguments"]
            else:
                arguments = {}

            for method_name, method in class_["methods"].items():
                if method_name in method_set:
                    raise NameError("Redeclaration of " + method_name)
                else:
                    method_set.add(method_name)

                url = method["url"]

                if "headers" in method:
                    headers = method["headers"]
                else:
                    headers = {}
                header_args = {}
                for header, value in headers.items():
                    if value.startswith("$"):
                        var = value[1:]
                        if var in variables:
                            headers[header] = variables[var]
                        else:
                            headers[header] = class_["fields"][var]
                    if value.startswith("@"):
                        header_args[value[1:]] = header

                if "data" in method:
                    data = method["data"]
                else:
                    data = {}
                data_args = {}
                for key, value in data.items():
                    if value.startswith("$"):
                        var = value[1:]
                        if var in variables:
                            data[key] = variables[var]
                        else:
                            data[key] = class_["fields"][var]
                    if value.startswith("@"):
                        data_args[value[1:]] = key

                if "refresh_method" in method:
                    refresh_method = method["refresh_method"]
                else:
                    refresh_method = None

                if refresh_method in method_set:
                    raise NameError("Redeclaration of " + method_name)
                else:
                    method_set.add(refresh_method)

                methods[method_name] = {
                    "url": url,
                    "data": data,
                    "data_args": data_args,
                    "headers": headers,
                    "header_args": header_args,
                    "refresh_method": refresh_method
                }
            self.classes[class_name] = type(class_name, (object,), {
                "methods": methods,
                "__init__": template_init
            })