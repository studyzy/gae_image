#coding:utf-8
from models import Images
from models import Tag
from models import ImageViewCount
from google.appengine.api import memcache
from google.appengine.api import images
from getimageinfo import getImageInfo
from google.appengine.ext import db
from google.appengine.api import urlfetch
from gaefile import *

def addImage(name, mime,description,tag,bf):
    'Add Image'
    image=Images(name=name, mime=mime,description=description,tag=tag.split(','), bf=bf)
    image.size=len(image.bf)
    image.filetype,image.width,image.height=getImageInfo(bf)
    image.put()
    AddTags(image.tag)
    return image

def addImage2(bf):
    image=Images(bf=bf)
    image.size=len(bf)
    image.filetype,image.width,image.height=getImageInfo(bf)
    if not image.filetype:return None
    image.mime=image.filetype
    image.put()
    return image

def getImage(id):
    id=int(id)
    return Images.get_by_id(id)

def resizeImage(id,size="image"):
    image=getImage(id)
    if not image:return None
    if size=="image":return image
    if image.width==-1:return image
    img=images.Image(image.bf)
    img.resize(width=240, height=240)
    img.im_feeling_lucky()
    image.bf=img.execute_transforms(output_encoding=images.JPEG)
    return image

def downImage(id,size="image"):
    key=id+size
    image=memcache.get(key)
    if not image:
        image=resizeImage(id, size)
        memcache.set(key,image,3600*24)
    imagecount= db.GqlQuery("SELECT * FROM ImageViewCount WHERE imageid=:1",int(id))
    x=imagecount.count()
    
    if x:
        ivc=imagecount[0]
        ivc.viewcount=ivc.viewcount+1
        db.put(ivc)
    else:
        ivc=ImageViewCount(imageid=int(id),viewcount=1) 
        db.put(ivc)               
    return image

def delImage(key):
    image=Images.get(key)
    if image:
        DelTags(image.tag)
        image.delete()

def delImageByid(id):
    image=Images.get_by_id(int(id))
    if image:
        DelTags(image.tag)
        image.delete()

def getAllImages(index=0):
    return Images.all().order('-created_at').fetch(25,index*24)

def getAllImagesByTag(tag):
    #return db.GqlQuery(u"SELECT * FROM Images WHERE tag=:1",unicode(tag, 'UTF-8'))
    return Images.all().filter('tag =', unicode(tag, 'UTF-8')).order('-created_at') 

def getPageing(index,page=0):
    s="/%s/"
    if page==0:
        if index==25:return (None,"/1/")
        else:return (None,None)
    if index==25:
        return ("/",s%(page+1)) if page==1 else (s %(page-1),s%(page+1))
    return ("/",None) if page==1 else (s %(page-1),None)

def AddImageByUrl(url,fileName,tag):
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        name = fileName
        mtype = result.headers.get('Content-Type', '')
        bits = result.content
        gf=GaeFile()
        gf.open(name,mtype);
        gf.write(bits)
        id=gf.close()
        
        image=Images(description="/media/?key="+str(id))
        image.mime=result.headers.get('Content-Type', '')
        image.filetype=image.mime
        # if image.mime.find('image')==-1:
            # return None
        image.size=len(bits)
        image.width=-1;
        image.height=-1;
        # image.name=fileName
        # image.filetype,image.width,image.height=getImageInfo(image.bf)
        image.tag=tag.split(',')
        image.put()
        AddTags(image.tag)
        return image
    else:
        return None

def AddImageByUrlBak(url,fileName,tag):
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        image=Images(description=url,bf=result.content)
        image.mime=result.headers.get('Content-Type', '')
        if image.mime.find('image')==-1:
            return None
        image.size=len(image.bf)
        image.name=fileName
        image.filetype,image.width,image.height=getImageInfo(image.bf)
        image.tag=tag.split(',')
        image.put()
        AddTags(image.tag)
        return image
    else:
        return None

        
        
def getAllTags():
    return Tag.all().order('-useCount')
def AddTags(tags):
    for t in tags:
        if t:
            tag= db.GqlQuery("SELECT * FROM Tag WHERE tagName=:1",t)      
            if tag.count()>0:
                thistag=tag[0]
                thistag.useCount=thistag.useCount+1
                db.put(thistag)
            else:
                newtag=Tag(tagName=t,useCount=1)
                db.put(newtag)
def DelTags(tags):
    for t in tags:
        tag= db.GqlQuery("SELECT * FROM Tag WHERE tagName=:1",t)
        if tag.count()>0:
            thistag=tag[0]
            thistag.useCount=thistag.useCount-1
            db.put(thistag)            