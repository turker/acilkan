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

'''
  App Engine data model for Emergecny Blood Request Application
'''

# Python imports
import logging
import re

# AppEngine imports
from google.appengine.ext import db
from google.appengine.api import memcache

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
