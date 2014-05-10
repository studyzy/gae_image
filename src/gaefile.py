import sys
import os
from google.appengine.ext import db
import logging
'''
simulate python file operation.
gf=GaeFile("/a/test.txt",'rw'); 
gf.write("hello gaefile");
gf,close()
logging.info(gf.read())

'''
M_BUFFLEN=1000000-1


class GFBits(db.Model):
	bits=db.BlobProperty()
	
class GFInfoTable(db.Model):
	name=db.StringProperty()
	path=db.StringProperty()
	property=db.StringProperty()
	buffList=db.ListProperty(db.Key)
	filesize=db.IntegerProperty()
	download=db.IntegerProperty()
	date=db.DateTimeProperty(auto_now_add=True)

	
class GFDir(db.Model):
	path=db.StringProperty()
	FileList=db.ListProperty(db.Key)

class GaeFile():
	path=""
	property=""
	filebuff=""
	ret=0
	gfInfoTable=None
	gfDir = GFDir()
	def __init__(self,path="",property="wr"):
		self.gfInfoTable=GFInfoTable()
		dirs=self.gfDir.all().filter("path","/").fetch(20)
		logging.info("len(dirs) %d ",len(dirs))
		
		if len(dirs) == 1:
			self.gfDir=dirs[0]
		elif len(dirs) == 0:
			self.gfDir.path="/"

	def open(self,path,property):
		self.path=path
		self.property=property
		if len(self.gfDir.FileList) == 0:
			self.gfInfoTable.path=path
			self.gfInfoTable.property=property
			self.gfInfoTable.download=0
			return
			
		for filekey in self.gfDir.FileList:
			file=db.get(filekey)
			if file == None:
				self.gfDir.FileList.remove(filekey)
			elif file.path == path:
				self.ret=1
				return 1
			else:
				self.gfInfoTable.path=path
				self.gfInfoTable.property=property
				self.gfInfoTable.download=0
			
	def write(self,buff):
		if self.gfInfoTable == None:
			self.ret=1
			return 1
		buffLen=len(buff)		
		self.gfInfoTable.filesize= buffLen
		i=0
		if buffLen > M_BUFFLEN :
			for i in range(0,buffLen/M_BUFFLEN+1):				
				self.filebuff=self.filebuff+buff[i*M_BUFFLEN:(i+1)*M_BUFFLEN]
				gfBits=GFBits()				
				gfBits.bits=buff[i*M_BUFFLEN:(i+1)*M_BUFFLEN]
				key=gfBits.put()				
				self.gfInfoTable.buffList.append(key)
		else:
			gfBits=GFBits()
			gfBits.bits=buff
			key=gfBits.put()			
			self.gfInfoTable.buffList.append(key)			
										
		pass
	def read(self,path):
		fb=""
		filebits=GFBits()
		for filekey in self.gfDir.FileList:
			file = db.get(filekey)
			if file.path == path:
				for i in range(0,len(file.buffList)):
					key=file.buffList[i]
					filebits=db.get(key)	
					fb=fb+filebits.bits
				return fb
			else:
				logging.info("can't find file %s",path)
			
	def remove(self,path):
		for filekey in self.gfDir.FileList:
			file = db.get(filekey)
			if file.path == path:
				for i in range(0,len(file.buffList)):
					key=file.buffList[i]
					bit=db.get(key)
					if bit != None:
						db.delete(bit)
				file.delete()
				self.gfDir.FileList.remove(filekey)
				self.gfDir.put()
				logging.info("delete file %s ok",path)
				return
		else:
			logging.info("can't find file %s",path)
			
	def close(self):
		if self.gfInfoTable == None:
			logging.info("close error filehandle=None");
			return 1
		if self.ret != 0:
			logging.info("can't close")
			return 1
		key=self.gfInfoTable.put()
		file = db.get(key)
		self.gfDir.FileList.append(key)
		self.gfDir.put()
		return key.id()
	
def main():		
	pass
	
if __name__ == "__main__":
    main()
