import functools
import logging
import os
import re
import time

import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

import model


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

       logging.debug('adding new request by %s' % req_author.nickname)
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
                blood_bytype = model.Blood.all().filter('type = ', blood_type)
                if not memcache.add("blood_bytype", blood_bytype, 10):
                    logging.error("Memcache set failed in get_blood.")
                return blood_bytype
        else:
            bloods = model.Blood.all()
            return bloods.fetch(10)

class AboutHandler(webapp.RequestHandler):
    pass

class MainHandler(webapp.RequestHandler):
    def get(self):
        util = Utility()
        hospital_name = self.request.get('hospital')
        hospital_city = self.request.get('city')
        blood_type = self.request.get('bloodtype')
        filter_byhospital = False
        filter_byblood = False
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
            'curr_url': curr_url,
            }

        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))

class NewRequestHandler(webapp.RequestHandler):
    def post(self):
        util = Utility()
        if users.get_current_user():
            req_author = users.get_current_user()

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


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/about', AboutHandler),
                                          ('/duyuru', NewRequestHandler),
                                         ],
                                         debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()

