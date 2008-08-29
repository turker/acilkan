# Python imports
import datetime
import types
import os

# Appengine imports
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext import db

from django.utils import simplejson
import yaml

# Local imports
import rest

class ResourceModel(rest.Resource, db.Expando):
    """A REST Resource wrapper around a Google datastore model"""

    def exposed_attrs(self):
        return self.properties().keys() + self.dynamic_properties()


class RestHandler(webapp.RequestHandler, rest.Dispatcher):
    """Responsible for returning the correct view to the end user.
    """
    caching = True
    cache_time = 300
    
    @property
    def template_dir(self):
        this_directory = os.path.dirname(__file__)
        parent_directory = os.path.dirname(this_directory)
        return parent_directory + "templates"
    
    def get(self):
        if self.caching:
            out = memcache.get(self.request.url)
            if out:
                self.response.out.write(out)
            else:
                self.dispatch_request()
                out = self.response.out.getvalue()
                memcache.set(self.request.url, out, self.cache_time)
        else:
            self.dispatch_request()
        
    def put(self):
        self.dispatch_request()
        
    def post(self):
        self.dispatch_request()
        
    def delete(self):
        self.dispatch_request()
        
    def dispatch_request(self):
        params = {}
        for key in self.request.params:
            params[str(key)] = self.request.get(key)
            
        if "format" in params:
            format = params["format"]
            del params["format"]
        else:
            format = "html"
            
        if "callback" in params and format == "json":
            callback = params["callback"]
            del params["callback"]
        else:
            callback = None
            
        obj = self.dispatch(self.request.path, self.request.method, params)
        obj = self.preserialize(obj)
        
        if format == "html":
            self.response.headers["Content-Type"] = "text/html"
            out = self.obj_to_html(obj)
        elif format == "json":
            self.response.headers["Content-Type"] = "application/json"
            out = simplejson.dumps(obj)
            if callback:
                out = callback + "(" + out + ")"
        elif format == "yaml":
            self.response.headers["Content-Type"] = "text/yaml"
            out = yaml.safe_dump(obj)
        elif format == "python":
            self.response.headers["Content-Type"] = "text/python"
            out = str(obj)
        elif format == "xml":
            self.response.headers["Content-Type"] = "text/xml"
            out = self.obj_to_xml(obj)
            
        self.response.out.write(out)
    
    def translate(self, obj, depth):
        """Object preserialization hook. Called while the dispatched object is 
        traversed recursively. 
        
        Args:
            depth - The depth of nesting within the dispatched object.
                    The dispatched object has a depth of 0.  Child objects 
                    have a depth of 1 or more.
            
        Returns:
            The translated object
        """
        return obj
    
    def preserialize(self, obj, depth=0):
        """
        Recursively translates objects to a serializable form:
            datetime.datetime -> iso formatted date string
            db.users.User -> user nickname
            db.GeoPt -> string
            db.IM -> string
            db.Key -> string          
            
        Returns:
            A shallow copy of the object
            
        Reference:
        http://code.google.com/appengine/docs/datastore/typesandpropertyclasses.html
        """
        obj = self.translate(obj, depth)
        
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, db.users.User):
            return obj.nickname()
        elif isinstance(obj, (db.GeoPt, db.IM, db.Key)):
            return str(obj)
        elif isinstance(obj, types.ListType):
            return [self.preserialize(item, depth+1) for item in obj]
        elif isinstance(obj, (types.DictType, rest.Resource)):
            copy = {}
            for key in obj:
                copy[key] = self.preserialize(obj[key], depth+1)
            return copy
        return obj
        
    def obj_to_html(self, obj):
        """Converts basic python objects to HTML"""
        type = obj.__class__.__name__.lower()
        filename = type + ".html"
        
        # try getting a template
        path = os.path.join(self.template_dir, filename)
        if os.path.isfile(path):
            return webapp.template.render(path, obj, debug=True)

        # if no template exists, return yaml representation of the object
        return "<html><body><pre>" + yaml.safe_dump(obj) + "</pre></body></html>"

    def obj_to_xml(self, obj, name="response"):
        """Converts basic python objects to XML"""
        xml = "<" + name + ">"
        if isinstance(obj, (types.DictType, rest.Resource)):
            for key in obj:
                xml += self.obj_to_xml(obj[key], key)
        elif isinstance(obj, (types.ListType, types.TupleType)):
            # try to convert item name to singular
            if name.endswith("s"):
                item_name = name.rstrip("s")
            else:
                item_name = name
                
            for item in obj:
                xml += self.obj_to_xml(item, item_name)
        else:
            try:
                xml += str(obj)
            except UnicodeEncodeError:
                try:
                    xml += unicode(obj, errors='ignore')
                except TypeError:
                    xml += obj
        return xml + "</" + name + ">"
