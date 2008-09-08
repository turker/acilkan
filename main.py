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
  App Engine Entry Point to Emergecny Blood Request Application
'''

import functools
import logging
import os
import re
import time
import urllib
 

import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template

import model
import utils


class AboutHandler(webapp.RequestHandler):
    pass

class MainHandler(webapp.RequestHandler):
    def get(self):
        util = utils.Utility()
        hospital_name = self.request.get('hospital')
        hospital_city = self.request.get('city')
        blood_type = self.request.get('bloodtype')
        filter_byhospital = False
        filter_byblood = False
        namefilter = False
        cityfilter = False
        filteredrequest = [ ]
        if (hospital_name is not '') & (hospital_city is ''):
            #handle filtering by hospital name 
            hospitals = util.get_hospitals(hospital_name)
            filter_byhospital = True
        elif (hospital_city is not '') & (hospital_name is ''):
            #handle filtering by hospital city
            hospitals = util.get_hospitals(None, hospital_city)
            filter_byhospital = True
        elif (hospital_name is not '') & (hospital_city is not ''):
            #handle filtering by both
            hospitals = util.get_hospitals(hospital_name, hospital_city)
            filter_byhospital = True
        else:
            hospitals = util.get_hospitals()

        if blood_type is not '':
            bloods = util.get_blood(blood_type)
            filter_byblood = True
        else:
            bloods = util.get_blood()

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Cikis Yap'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Giris Yap'

        if (filter_byhospital) & (filter_byblood):
            if hospital_name is not '':
                namefilter = True
            if hospital_city is not '':
                cityfilter = True
            for r in bloods.requests:
                if (namefilter) & (cityfilter):
                    if r.hospital.name == hospital_name:
                        if r.hospital.city == hospital_city:
                                filteredrequest.append(r)
                if (not namefilter) & (cityfilter):
                    if r.hospital.city == hospital_city:
                        filteredrequest.append(r)
                if (namefilter) & (not cityfilter):
                    if r.hospital.name == hospital_name:
                        filteredrequest.append(r)

        reqs = util.get_requests()
        curr_url = self.request.url 
        template_values = {
            'title': 'Acil Kan Duyurularinda Ne Durum?',
            'reqs': reqs,
            'hospitals': hospitals,
            'hospital_name' : hospital_name,
            'hospital_city' : hospital_city,
            'blood_type' : blood_type,
            'bloods': bloods,
            'url': url,
            'url_linktext': url_linktext,
            'filter_byhospital': filter_byhospital,
            'filter_byblood' : filter_byblood,
            'filteredrequest': filteredrequest,
            'curr_url': curr_url,
            }

        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))

class ShowRequest(webapp.RequestHandler):
    def get(self):
        request_key = self.request.get('id')
        request = db.get(db.Key(request_key))
        curr_url = self.request.uri
        template_values = {
            'title': 'Acil Kan Duyurularinda Ne Durum?',
            'curr_url': curr_url,
            'request': request,
            }

        path = os.path.join(os.path.dirname(__file__), 'templates/acilkan.html')
        self.response.out.write(template.render(path, template_values))

class TwitterHandler(webapp.RequestHandler):
    def get(self):
        url = self.request.get('link')
        msg = "Testing " + url
        util = utils.Utility()
        util.postToTwitter(msg)
        self.redirect('/')

class NewRequestHandler(webapp.RequestHandler):
    def post(self):
        util = utils.Utility()
        if users.get_current_user():
            req_author = users.get_current_user()
        else:
            req_author = None

        hospital_name = self.request.get('hospital_name')
        hospital_city = self.request.get('hospital_city')
        
        req_blood_type = self.request.get('blood_type')
        
        req_patient_name = self.request.get('patient_name')
        req_phone_number = self.request.get('phone_number')
        
        req_hospital = util.add_hospital(hospital_name, hospital_city)
        
        req_blood = util.add_blood(req_blood_type, req_hospital)

        util.add_new_request(req_author, req_hospital, req_blood,
                                            req_patient_name, req_phone_number)
        self.redirect('/')

class PersonalPageHandler(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            user = users.get_current_user()

class ProfileHandler(webapp.RequestHandler):
    pass

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/about', AboutHandler),
                                          ('/duyuru', NewRequestHandler),
                                          ('/acilkan', ShowRequest),
                                          ('/twit', TwitterHandler),
                                          ('/kisisel', PersonalPageHandler),
                                          ('/profil', ProfileHandler),
                                         ],
                                         debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()

