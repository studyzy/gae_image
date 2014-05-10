#coding:utf-8
import wsgiref.handlers
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import db
from gaefile import *
from admin import requires_admin
import time
import methods
import logging
import urllib


def format_date(dt):
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

class PublicPage(webapp.RequestHandler):
    def render(self, template_file, template_value):
        path = os.path.join(os.path.dirname(__file__), template_file)
        self.response.out.write(template.render(path, template_value))
    
    def error(self,code):
        if code==400:
            self.response.set_status(code)
        else:
            self.response.set_status(code)
            
    def is_admin(self):
        return users.is_current_user_admin()
    
    def head(self, *args):
        return self.get(*args) 
    
class MainPage(PublicPage):
    @requires_admin
    def get(self,page):
        index=0 if page=="" else int(page)
        images=methods.getAllImages(index)
        prev,next=methods.getPageing(len(images), index)
        tags=methods.getAllTags()
        template_value={"images":images[:24],"prev":prev,"next":next,"tags":tags}
        self.render('views/index.html', template_value)

class ShowImage(PublicPage):
    def get(self,id):
        image=methods.getImage(id)
        if not image:return self.error(404)
        template_value={"image":image,"admin":self.is_admin(),"webm":image.filetype=="video/webm"}
        self.render('views/show.html', template_value)
class ShowTagImage(PublicPage):
    def get(self,tag):
        tagString=urllib.unquote_plus(tag)
        images=methods.getAllImagesByTag(tagString)
        template_value={"images":images[:24],"tag": tagString }
        self.render('views/tagimage.html', template_value)    
    
class GetImage(PublicPage):
    def get(self,size,id):
        dic=self.request.headers
        key=dic.get("If-None-Match")
        self.response.headers['ETag']=size+id
        if key and key==size+id:
            return self.error(304)
        image=methods.downImage(id, size)
        if not image:
            return self.error(404)
        if image.width==-1:
            self.redirect(image.description)
        else:
            self.response.headers['Content-Type'] = str(image.mime) 
            self.response.headers['Cache-Control']="max-age=315360000"
            self.response.headers['Last-Modified']=format_date(image.created_at)
            self.response.out.write(image.bf)

class Error(PublicPage):
    def get(self):
        return self.error(404)

class Media():
    name =""
    mtype=""
    filesize=0
    date=time.strftime("%Y-%m-%d %X", time.localtime() )  
    download=0   
    keyid=db.Key
    
    def size(self):
        return self.filesize


class Pager(object):
    def __init__(self, model=None,query=None, items_per_page=10):
        if model:
            self.query = model.all()
        elif query:
            self.query=query
        self.items_per_page = items_per_page

    def fetch(self, p):
        max_offset = self.query.count()
        n = max_offset / self.items_per_page
        if max_offset % self.items_per_page != 0:
            n += 1
        if p < 0 or p > n:
            p = 1
        offset = (p - 1) * self.items_per_page
        results = self.query.fetch(self.items_per_page, offset)
        links = {'count':max_offset,'page_index':p,'prev': p - 1, 'next': p + 1, 'last': n}
        if links['next'] > n:
            links['next'] = 0
        return (results, links)

class getMedia(webapp.RequestHandler):
    def get(self,slug):
        media=0
        buf=""
        file=GFInfoTable()
        gf=GaeFile()
        key=self.request.get('key')
        for filekey in gf.gfDir.FileList:
            if str(filekey.id()) == key:
                file=db.get(filekey)
                file.download+=1
                buf=gf.read(file.path)
                file.put()
                mtype=file.property
                media=1
        
        if media:
            self.response.headers['Expires'] = 'Thu, 15 Apr 3010 20:00:00 GMT'
            self.response.headers['Cache-Control'] = 'max-age=3600,public'
            self.response.headers['Content-Type'] = str(mtype)
            self.response.out.write(buf)
            
                     
class Upload(webapp.RequestHandler):
    def post(self):
        name = self.request.get('filename')
        mtype = self.request.get('fileext')
        bits = self.request.get('upfile')       
        gf=GaeFile()
        gf.open(name,mtype);        
        gf.write(bits)
        gf.close()
        self.redirect('/')

class FileManager(webapp.RequestHandler):

    def __init__(self):
        self.current='files'

    def get(self):
        try:
            page_index=int(self.request.get('page'))
        except:
            page_index=1
        files=[]
        gf=GaeFile()
        for filekey in gf.gfDir.FileList:
            file = db.get(filekey)            
            tmp = Media()
            tmp.name = file.path
            tmp.filesize=file.filesize
            tmp.mtype= file.property
            tmp.keyid = filekey.id()
            tmp.date=file.date
            tmp.download=file.download
            files.append(tmp)
        links = {'count':10,'page_index':5,'prev': 5 - 1, 'next': 5 + 1, 'last': 2}        
        template_values = {'files' : files,'pager':links,}
        path = os.path.join(os.path.dirname(__file__), 'views/filebase.html') 
        self.response.out.write(template.render(path, template_values))
        
    def post(self): # delete files
        delids = self.request.POST.getall('del')
        if delids:
            for id in delids:
                gf=GaeFile()
                for filekey in gf.gfDir.FileList:
                    if str(filekey.id()) == id:
                        file=db.get(filekey)
                        gf.remove(file.path)
        self.redirect('/')    

def main():
    application = webapp.WSGIApplication(
                                       [('/(?P<page>[0-9]*)/?', MainPage),
                                        (r'/(?P<size>image)/(?P<id>[0-9]+)/?',GetImage),
                                        (r'/(?P<size>s)/(?P<id>[0-9]+)/?',GetImage),
                                        (r'/tag/(?P<tag>.+)/?',ShowTagImage),
                                        (r'/show/(?P<id>[0-9]+)/?',ShowImage),
                                        ('/file',FileManager),
                                        ('/upload',Upload),        
                                        ('/media/([^/]*)/{0,1}.*',getMedia),
                                        ('.*',Error)
                                       ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()