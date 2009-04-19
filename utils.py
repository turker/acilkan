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
  Utiliy functions for Emergecny Blood Request Application
'''

from google.appengine.api import memcache
from google.appengine.ext import db, webapp
import model
import logging

class Utility():
    def parseContent(self,request):
        res = request.split(' ')
        return res

    def isHospitalExisting(self, entity):
        q = Hospital.all().filter("name = ", entity)
        res = q.fetch(1)
        return res 

    def isBloodTypeExisting(self, entity):
        #res = db.GqlQuery("SELECT * from :1 WHERE :2 = :3", dbmodel, field, entity) 
        q = Blood.all().filter("type = ", entity)
        res = q.fetch(1)
        return res

    def add_hospital(self, hname, hcity):
        #check if hospital already exists
        q = model.Hospital.all().filter('name =', hname)
        q.filter('city',hcity)
        if q.get():
            return q.get()
        #add and return hospital object
        logging.debug('adding new hospital %s' % hname)
        hospital = model.Hospital(name=hname, city = hcity)
        hospital.put()
        return hospital

    def add_blood(self, btype, req_hospital):
        #check if blood already exists
        q = model.Blood.all().filter('type =', btype)
        if q.get():
            return q.get()
        #add blood type and associated hospital
        logging.debug('adding new request for %s' % btype)
        blood = model.Blood(type = btype, hospital = req_hospital)
        blood.put()
        return blood

    def add_new_request(self,
                        req_author,
                        req_hospital,
                        req_blood,
                        req_patient_name,
                        req_phone_number):

    #TODO: May need to check the existance of the exact same request

       logging.debug('adding new request by ')
       brequest = model.BloodRequest(author=req_author,
                                      hospital=req_hospital,
                                      blood = req_blood,
                                      patient_name = req_patient_name,
                                      phone_number = req_phone_number,
                                      is_served = False)
       brequest.put()

    def get_requests(self):
        rqsts = model.BloodRequest.all().order('-created')
        return rqsts

    def get_hospitals(self, hname=None, hcity=None):
        if (hname is not None) & (hcity is None):
            hospitals_byname = memcache.get("hospitals_byname")
            if hospitals_byname is not None:
                return hospitals_byname
            else:
                hospitals_byname = model.Hospital.gql("WHERE name = :1", hname)
                if not memcache.add("hospitals_byname",hospitals_byname,10):
                    logging.error("Memcache set failed in get_hospitals.")
                return hospitals_byname

        elif (hcity is not None) & (hname is None):
            hospitals_bycity = memcache.get("hospitals_bycity")
            if hospitals_bycity is not None:
                return hospitals_bycity
            else:
                hospitals_bycity = model.Hospital.gql("WHERE city = :1", hcity)
                if not memcache.add("hospitals_bycity", hospitals_bycity, 10):
                    logging.error("Memcache set failed in get_hospitals.")
                return hospitals_bycity
        elif (hcity is not None) & (hname is not None):
            hospital_specific = memcache.get("hospital_specific")
            hospital_specific = None
            if hospital_specific is not None:
                return hospital_specific
            else:
                hospital_specific = model.Hospital.all().filter('city = ', hcity)
                hospital_specific.filter('name = ', hname)
                if not memcache.add("hospital_specific", hospital_specific, 10):
                    logging.error("Memcache set failed in get_hospitals.")
                return hospital_specific
        else:
            hospitals = memcache.get("hospitals")
            if hospitals is not None:
                return hospitals
            else:
                hospitals = model.Hospital.all().fetch(10)
                if not memcache.add("hospitals", hospitals, 10):
                    logging.error("Memcache set failed in get_hospitals.")
                return hospitals

    def get_blood(self, blood_type = None):
        if (blood_type is not None):
            blood_bytype = memcache.get("blood_bytype")
            if blood_bytype is not None:
                return blood_bytype
            else:
                blood_bytype = db.get(db.Key(blood_type))
                #blood_bytype = model.Blood.all().filter('type = ', blood_type)
                if not memcache.add("blood_bytype", blood_bytype, 10):
                    logging.error("Memcache set failed in get_blood.")
                return blood_bytype
        else:
            bloods = model.Blood.all()
            return bloods.fetch(10)

    def postToTwitter(self,message):
        http = httplib.Http()
        response = http.request(
                "http://twitter.com/statuses/update.xml", 
                "POST", 
                urllib.urlencode({"status": msg})
                )
        if response:
            print "Success"
        else:
            print "error updating"

    def calculateMostHospital(self):
        nbreqs = []
        hospitals = model.Hospital.all().fetch(1000)
        for hosp in hospitals:
            reqs = hosp.requests
            print reqs



