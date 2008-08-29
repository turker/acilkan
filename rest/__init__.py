"""Simple REST Library"""
import UserDict
import types


def http_get_action(func):
    """
    Decorator for exposing methods through HTTP GET requests.
    
    The method is called when a request is made with "action" 
    as a parameter and the method name as the value. Additional 
    parameters are passed in as keyword arguments.
    
    The decorated method must be idempotent (no side-effects), 
    as the results may be cached.
    
    class Person:
        @http_get_action
        def say_hi(self, times=1):
            return "hi " * int(times)
    """
    func.http_get_action = True
    return func
    
def http_post_action(func):
    """
    Decorator for exposing methods through HTTP POST requests.
    
    The method is called when a request is made with "action" 
    as a parameter and the method name as the value. Additional 
    parameters are passed in as keyword arguments.
    
    HTTP POST actions may have side effects.
    
    class Person:
        @http_post_action
        def change_name(self, name):
            self.name = name
    """
    func.http_post_action = True
    return func
    
class Dispatcher(object):
    """
    Dispatches objects based on their path.  Child objects are 
    found through dictionary access.
    
    Supports http_get(), http_put(), http_post(), and http_delete() 
    methods if available.
    
    Supports actions for methods decorated with @http_get_action
    and @http_post_action
    """
    root_object = "i am root"
    
    def obj_from_path(self, path):
        path = path.split('/')
        obj = self.root_object
        for name in path:
            if not name: continue
            try:
                # it's a dictionary
                obj = obj[name]
            except TypeError:
                # no wait, it's a list
                range = name.split('-', 1)
                if len(range) == 2 and range[0] and range[1]:
                    # 1 based indexing, includes the end range
                    start = int(range[0]) - 1
                    end = int(range[1])
                    obj = obj[start:end]
                else:
                    obj = obj[int(name)]
        return obj
        
    def dispatch(self, path, http_method, params):
        """Returns the dispatched object
        
        Args:
            path - the object path string
            http_method - must be either 'GET', 'PUT', 'POST', or 'DELETE'
            params - a dictionary containing the request parameters
        """
        obj = self.obj_from_path(path)
    
        if "action" in params:
            action = getattr(obj, params["action"], None)
            del params["action"]
        else:
            action = None
            
        out = None
        if http_method == "GET":
            if hasattr(action, "http_get_action"):
                out = action(**params)
            elif hasattr(obj, "http_get"):
                out = obj.http_get(**params)
        elif http_method == "POST":
            if hasattr(action, "http_post_action"):
                out = action(**params)
            out = obj.http_post(**params)
        elif http_method == "PUT":
            out = obj.http_put(**params)
        elif http_method == "DELETE":
            out = obj.http_delete(**params)
            
        if out: return out
        return obj

class Error(Exception):
    """Base class for Rest resource exceptions"""
    pass

class NotImplementedError(Error):
    pass

class InvalidMethodName(Error):
    pass

## Resource Helper class

def getter(func):
    """
    Decorator for a method which gets a key value.  
    The decorated method must start with "get_", followed 
    by the key name which is exposed to the dictionary.
    
    A getter will be exposed in keys(), and in iteration
    """
    if not func.__name__.startswith("get_"):
        raise InvalidMethodName("method name must start with 'get_'")
    func.getter = True 
    return func
    
def setter(func):
    """
    Decorator for a method which sets a key value.
    The decorated method must start with "set_", followed 
    by the key name.
    """
    if not func.__name__.startswith("set_"):
        raise InvalidMethodName("method name must start with 'set_'")
    func.setter = True
    return func

def deleter(func):
    """
    Decorator for a method which deletes a key value.
    The decorated method must start with "del_", followed 
    by the key name.
    """
    if not func.__name__.startswith("del_"):
        raise InvalidMethodName("method name must start with 'del_'")
    func.deleter = True
    return func

class Resource(UserDict.DictMixin):
    """A customizable dictionary. Useful for object traversal and 
    encapsulation.  Easy to serialize.

    Decorators can be used to customize key access.
        
        class Dog(Resource):
            @getter
            def get_name(self):
                return self.name
                
            @setter
            def set_name(self, value):
                self.name = value.lower()
                
            @deleter
            def del_name(self):
                del self.name
    """
    
    def exposed_attrs(self):
        """attribute names to be exposed as keys"""
        return []
    
    def hidden_keys(self):
        """Keys to hide from iteration. A Key will still be accessible if it is 
        a getter or if it is listed in exposed_attrs()"""
        return []
    
    def child_object(self, name):
        """Called to get a child object if it isn't found as a getter or an attribute"""
        raise AttributeError
        
    # Dictionary Methods
    def __getitem__(self, key):
        """Called to implement evaluation of self[key]"""
        getter = getattr(self, 'get_'+key, None)
        if hasattr(getter, 'getter'):
            return getter()
        if key in self.exposed_attrs():
            return getattr(self, key)
        return self.child_object(key)
        
    def __setitem__(self, key, value):
        """Called to implement assignment to self[key]"""
        setter = getattr(self, 'set_'+key, None)
        if hasattr(setter, 'setter'):
            return setter(value)
        
    def __delitem__(self, key):
        """Called to implement deletion of self[key]"""
        deleter = getattr(self, 'del_'+key, None)
        if hasattr(deleter, 'deleter'):
            return deleter(value)
        
    def keys(self):
        """List of keys for iteration"""
        getter_keys = [name.replace('get_', '', 1) for name in dir(self) 
                   if hasattr(getattr(self, name, None), 'getter')]
        exposed_keys = getter_keys + self.exposed_attrs()
        return [key for key in exposed_keys if key not in self.hidden_keys()]
