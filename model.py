# Copyright 2008 Turker Keskinpala
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

''' App Engine data model for Emergecny Blood Request Application
    Some parts of this code was taken from Rietveld application
    http://code.google.com/p/rietveld/
'''


# Python imports
import logging
import re

# AppEngine imports
from google.appengine.ext import db
from google.appengine.api import memcache


### GQL query cache ###
_query_cache = {}

def gql(cls, clause, *args, **kwds):
  """Return a query object, from the cache if possible.

  Args:
    cls: a db.Model subclass.
    clause: a query clause, e.g. 'WHERE draft = TRUE'.
    *args, **kwds: positional and keyword arguments to be bound to the query.

  Returns:
    A db.GqlQuery instance corresponding to the query with *args and
    **kwds bound to the query.
  """
  query_string = 'SELECT * FROM %s %s' % (cls.kind(), clause)
  query = _query_cache.get(query_string)
  if query is None:
    _query_cache[query_string] = query = db.GqlQuery(query_string)
  query.bind(*args, **kwds)
  return query


class Hospital(db.Model):
    name = db.StringProperty(required=True)
    city = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    
class Blood(db.Model):
    type = db.StringProperty(required=True, 
                        choices=('0-','0+', 'A+','A-','B+','B-','AB+','AB-'))
    hospital = db.ReferenceProperty(Hospital,
                                    required=True,
                                    collection_name='blood_types')
    created = db.DateTimeProperty(auto_now_add=True)

class BloodRequest(db.Model):
    #user info
    author = db.UserProperty()
    
    created = db.DateTimeProperty(auto_now_add=True)
    
    #hospital info
    hospital = db.ReferenceProperty(Hospital,
                                    required=True,
                                    collection_name = 'requests')
    #Blood Information
    blood = db.ReferenceProperty(Blood,
                                 required=True,
                                 collection_name = 'requests')
    
    #Contact information
    patient_name = db.StringProperty()
    phone_number = db.PhoneNumberProperty()
    
    #Request status
    is_served = db.BooleanProperty()
