import wsgiref.handlers

import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

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

class Post(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    patient = db.StringProperty()
    contact = db.StringProperty(multiline=False)
    hospital = db.StringProperty()
    bloodtype = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class Hospital(db.Model):
    name = db.StringProperty(multiline=False)
    city = db.StringProperty(multiline=False)

class Blood(db.Model):
    type = db.StringProperty()

class FilterBy(webapp.RequestHandler):
    listby = '-date'
    def post(self):
        listmethod = self.request.get('btype')
        if listmethod == 'Kan Grubuna Gore Listele':
            listby = '-bloodtype'
            print listby
        self.redirect('/')
    def get(self):
        print 'get'

class BloodRequest(webapp.RequestHandler):
    def post(self):
        util = Utility()
        post = Post()
        hospital = Hospital()
        blood = Blood()

        if users.get_current_user():
            post.author = users.get_current_user()

        post.content = self.request.get('content')
        res = util.parseContent(post.content)
        hospital.name = res[0]
        hospital.city = res[1]
        blood.type = res[2]
        post.patient = res[3]
        post.contact = res[4]
        post.hospital = hospital.name
        post.bloodtype = blood.type
        post.put()
        #Store hospital only if there is no record of that hospital
        if util.isHospitalExisting(res[0]) == []:
            hospital.put()
        #Store bloodtype only if there is no record of that type 
        if util.isBloodTypeExisting(res[2]) == []:
            blood.put()
        self.redirect('/')
        

class MainPage(webapp.RequestHandler):
    def get(self):
        filtertype = FilterBy()
        posts_query = Post.all().order(filtertype.listby)
        posts = posts_query.fetch(10)
        btypes_query = Blood.all()
        btypes = btypes_query.fetch(10)
        util = Utility()

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Cikis Yap'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Giris Yap'
        
        template_values = {
                'posts': posts,
                'url': url,
                'url_linktext': url_linktext,
                'btypes': btypes,
                'filtertype': filtertype.listby,
                }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                    [('/', MainPage),
                                     ('/duyuru', BloodRequest),
                                     ('/listele',FilterBy)],
                                    debug=True)

def main():
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
