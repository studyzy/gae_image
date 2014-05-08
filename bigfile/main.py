import wsgiref.handlers
import logging
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from gaefile import *
import time


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
		path = os.path.join(os.path.dirname(__file__), 'views/base.html') 
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

class Map(webapp.RequestHandler):
	def get(self):
		path = os.path.join(os.path.dirname(__file__), 'views/map.html') 
		template_values = {}
		self.response.out.write(template.render(path, template_values))
		
def main():
    webapp.template.register_template_library('filter')
    application = webapp.WSGIApplication(
       [('/',FileManager),
        ('/upload',Upload),        
		('/media/([^/]*)/{0,1}.*',getMedia),
		('/map',Map),
       ],
       debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
