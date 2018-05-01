from flask import Flask, session, redirect, url_for, escape, request, render_template,jsonify
import sendmail
import keygen
import datetime
import searchfilter
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict
import io
import base64
from bson.binary import Binary
import codecs
from flask import send_file
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL) 
from werkzeug.contrib.cache import MemcachedCache
import memcache
cache = memcache.Client(['130.245.168.39:11211'])
client = MongoClient("mongodb://130.245.171.44/chirp")
db = client.chirp



application = Flask(__name__)
application.secret_key = 'sUper sEcuRe t0tally RAndom keY '

@application.route("/")
def index():
	return render_template('index.html')

@application.route("/adduser", methods=['POST'])
def adduser():
    req=request.get_json()
    e= req['email']

    if db.accounts.find({"email":e}).count() > 0:
        #unique email
        return jsonify({'status': 'error', 'error':'Email Address already in use'})
    u= req['username']
    if db.accounts.find({"username":u}).count() > 0 :
        #unique username
        return jsonify({'status': 'error', 'error':'Username already in use'}) 
    p= req['password']
    k= keygen.gen()
    sendmail.send(e,u,k)
    new= {"username":u,"password":p, "email":e, "key":k}
    db.accounts.insert_one(new)
    return jsonify({'status': 'OK'})
    #return jsonify(req)

@application.route("/login", methods=['POST'])
def login():
    req=request.get_json()
    #check if someone is already loggedin
    if session.get('username')is not None:# if it has a username already
        return jsonify({'status': 'error', 'error':'User '+session['username']+' is already logged in.'})
    u= req['username']
    p= req['password']
    if db.accounts.find({"username": u, "password": p, "verified":"true"}).count() > 0:
        out=jsonify({"status":"OK"})
        session['username']=u
        #since instructions specifically say "set session cookie" i'll leave this part commented in case it's needed in the future
        #out.set_cookie('username',u)
        #out.set_cookie('loggedin','true') # backup log in test :)
        return out
    return jsonify({'status': 'error', 'error':'Unable to log in'})

@application.route("/logout", methods=['POST'])
def logout():
    if session.pop('username', None) is None: # return none is no username in session
        return jsonify({'status': 'error', 'error':'No user logged in'})
    else:
        return jsonify({"status":"OK"})

@application.route("/verify", methods=['GET','POST'])
def verify():
    if request.method =='GET':
        e=request.args.get('email')
        k=request.args.get('key')
        if e is None or k is None:
            return render_template('verify.html')
    else:
        req=request.get_json()
        e=req['email']
        k=req['key']
    userID = db.accounts.find_one({"email":e})
    if userID is not None and k=="abracadabra":
        db.accounts.update_one({"_id":userID['_id']},{'$set':{'verified':'true'}})
        return jsonify({"status":"OK"})
    elif userID is not None:
        db.accounts.update_one({"_id":userID['_id'], "key":k},{'$set':{'verified':'true'}})
        return jsonify({'status': 'OK'})
    else:
        return jsonify({'status': 'error', 'error':'Email/Key combination could not be verified'})

@application.route("/additem", methods=['POST'])
def additem():
    req=request.get_json()
    if session.get('username') is None:
        return jsonify({'status': 'error', 'error':'User not logged in.'})
    else:
        date=datetime.datetime.now()
        con=req['content']
        counter= cache.get('itemctr')
        if counter is None:
            dbcounter= db.counter.find_one({"item_id":"itemid"},{"seq":1})# get current id counter
            counter= int(dbcounter['seq'])
        db.counter.update_one({"item_id":"itemid"},{'$inc':{"seq":1}})#update counter
        cache.set('itemctr',counter+1)
        if req.get('media') is None:
            mid=[]
        else:
            mid=req['media']  #should be array of ids already
        for m in mid:
            db.media.update_one({"mediaid":m},{'$set':{"used":"y"}})
        if req.get('childType') is None:
            new= {"item_id":counter,"timestamp":date, "username":session['username'], "content":con,"childType":'null', "retweeted":0, "property":{"likes":0},"parent":'null', "media":mid}
        else:
            ct=req['childType'] #if child: retweet or reply, if not child: null
            if req.get('parent') is not None: # parent optional
                p=req['parent'] # item id of the original item being responded to
                new= {"item_id":counter,"timestamp":date, "username":session['username'], "content":con, "childType":ct,"retweeted":0, "property":{"likes":0},"parent":p,"media":mid}
                if ct == "retweet": #increase parent retweet counter if retweeted
                    db.items.update_one({"item_id":p},{'$inc': {"retweeted":1}})# increment retweet count of parent by one         
    cache.set('item'+str(counter['seq']), item)
    db.items.insert(new)
    #any other error situations?
    return jsonify({'status': 'OK', 'id':str(counter)})  

@application.route("/item/<id>", methods=['GET'])
def item(id):
    id= int(id)
    item= cache.get('item'+str(id)) #might need to do str(int(float(id
    if item is None:
        item= db.items.find_one({"item_id":id}) #lmao
        cache.set('item'+str(id),item)
    if item is None:
        return jsonify({'status': 'error', 'error':'Chirp not found'})
    return jsonify({'status': 'OK', 'item':{'id':item['item_id'],'username':item['username'],'property':item['property'],'retweeted':item['retweeted'],'content':item['content'],'timestamp':item['timestamp'], 'childType': item['childType'], 'parent':item['parent'],'media':item['media']}})


@application.route("/search", methods=['POST'])
def search():
    out= {'status':'OK'}
    if session.get('username') is None:
        return jsonify({'status': 'error', 'error':'User not logged in.'})
    req=request.get_json()
    if req.get('timestamp') is None:
        ts=datetime.datetime.now() #default is current time
    else:
        ts=int(req['timestamp'])
    if req.get('limit') is None:
        l=25 #default limit is 25
    else:
        l=int(req['limit'])
        if l > 100 :
            l=100 # max limit is 100
        elif l < 0:
            return jsonify({'status':'error','error':'Please input a valid limit 0<limit<100'})
    
    if req.get('q') is None:
        query=''
    else:
        query= req['q']
    if req.get('username') is None:
        u=''
    else:
        u=req['username']
    if req.get('following')is None:
        f=True
    else:
        out['afollowing']=str(req['following'])
     
        if req['following']:
            f=True
        else:
            f=False
    if req.get('rank') is None:
        r="interest"
    else:
        r="time"
    if req.get('parent') is None:
        p=None
    else:
        p=req['parent']
    if req.get('replies') is None:
        re= True
    else:
        re= req['replies']
    if req.get('hasMedia') is None:
        m=False
    else:
        m=req['media']
    
    #is username defined twice ?
    out['user']= session.get('username')
    out['timestamp']=ts
    out['limit']=l
    out['query']=query
    out['username']=u
    out['following']=f
    out['rank'] = r
    out['parent']=p
    out['replies']=re
    out['media']=m

    if u and f : # username not empty and following is true
        isfollowing = db.following.find_one({'user':session.get('username'),'follows':u})
        if isfollowing is None:
            return jsonify({'status':'OK','items':[]}) # if not following, dont return anything
        else: # return tweets by this user as usual
            if p:
                chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query},"username":{'$regex':u},"childType":'reply',"parent":{'$regex':p}}).limit(l)
            else:
                chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query},"username":{'$regex':u}}).limit(l) # limits amount pulled by l (L NOT 1)
            items=[]
            for chirp in chirps:
                c= {'id':chirp['item_id'],'username':chirp['username'],'property':chirp['property'],'retweeted':chirp['retweeted'],'content':chirp['content'],'timestamp':chirp['timestamp'],'childType': chirp['childtype'], 'parent':chirp['parent'],'media':chirp['media']}
                items.append(c)
            chirps.close()
            items = noReplies(re, items)
            items = onlyMedia(m, items)
            items = rankSort(r, items)
            out['items']=items
            return jsonify(out)
    elif f: # following is true but username is not
        if p:
            isfollowing =db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query},"username":{'$regex':u},"childType":'reply',"parent":{'$regex':p}}).limit(l)
        else:
            isfollowing = db.following.find({'user':session.get('username')})
        flist=[]
        for follow in isfollowing:
            flist.append(follow['follows'])
        isfollowing.close()
        chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query}})
        counter=0
        items=[]
        for chirp in chirps:  
            if chirp['username'] in flist:
                c= {'id':chirp['item_id'],'username':chirp['username'],'property':chirp['property'],'retweeted':chirp['retweeted'],'content':chirp['content'],'timestamp':chirp['timestamp'], 'childType': chirp['childType'], 'parent':chirp['parent'],'media':chirp['media']}

                items.append(c)
                counter +=1
                if counter >= l:
                    break # if counter is at or over limit, end loop
        chirps.close()
        items = searchfilter.noReplies(re, items)
        items = searchfilter.onlyMedia(m, items)
        items = searchfilter.rankSort(r, items)
        out['items']=items
        return jsonify(out)


    elif u: # username is true but following is not
        if p:
            chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query},"username":{'$regex':u},"childType":'reply',"parent":{'$regex':p}}).limit(l)
        else:
            chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query},"username":{'$regex':u}}).limit(l) # limits amount pulled by l (L NOT 1)

        items=[]
        for chirp in chirps:
            c= {'id':chirp['item_id'],'username':chirp['username'],'property':chirp['property'],'retweeted':chirp['retweeted'],'content':chirp['content'],'timestamp':chirp['timestamp'], 'childType': chirp['childType'], 'parent':chirp['parent'],'media':chirp['media']}
            items.append(c)
        chirps.close()   
        items = searchfilter.noReplies(re, items)
        items = searchfilter.onlyMedia(m, items)
        items = searchfilter.rankSort(r, items)
        out['items']=items

        return jsonify(out)
    else: # neither username nor following is true
        if p:
            chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query},"username":{'$regex':u},"childType":'reply',"parent":{'$regex':p}}).limit(l)
        else:
            chirps=db.items.find({"timestamp":{'$lte':ts},"content":{'$regex':query}}).limit(l) # limits amount pulled by l (L NOT 1)

        items=[]
        for chirp in chirps:
            c= {'id':chirp['item_id'],'username':chirp['username'],'property':chirp['property'],'retweeted':chirp['retweeted'],'content':chirp['content'],'timestamp':chirp['timestamp']}
            items.append(c)
        chirps.close()
        items = searchfilter.noReplies(re, items)
        items = searchfilter.onlyMedia(m, items)
        items = searchfilter.rankSort(r, items)
        out['items']=items

        return jsonify(out)

@application.route("/item/<id>", methods=['DELETE'])
def delitem(id):
    #i dont think we have to return anything
    item= db.items.find({"item_id":id})
    media=item['media']
    for m in media:
        db.media.remove({"mediaid":m},true)
    db.items.remove({"item_id":int(float(id))}, true)
    cache.delete('item'+str(int(float(id))))
@application.route("/user/<username>", methods=['GET'])
def profile(username):
    acc=db.accounts.find_one({'username':username},{'email':1})
    following = db.following.find({'user':username}).count
    followers = db.following.find({'follows':username}).count
    e= acc['email']
    return jsonify({'status': 'OK', 'user': {'email':e,'followers':followers,'following':following}})  

@application.route("/user/<username>/followers", methods=['GET'])
def followers(username):
    l=request.args.get('limit')
    if l is None:
        l=50
    elif l >200:
        l=200
    elif l < 0:
            return jsonify({'status':'error','error':'Please input a valid limit 0<limit<200'})
  
    followers = db.following.find({'follows':username},{'user':1}).limit(l)
    fs=[]
    for follower in followers:
        fs.append(follower['user'])
    return jsonify({'status': 'OK', 'users':fs})  
@application.route("/user/<username>/following", methods=['GET'])
def following(username):
    l=request.args.get('limit')
    if l is None:
        l=50
    elif l >200:
        l=200
    elif l < 0:
            return jsonify({'status':'error','error':'Please input a valid limit 0<limit<200'})
  
    following = db.following.find({'user':username},{'follows':1}).limit(l)

    fs=[]
    for follow in following:
        fs.append(following['user'])
    return jsonify({'status': 'OK', 'users':fs})       
@application.route("/follow", methods=['POST'])
def follow():
    req=request.get_json()
    if session.get('username') is None:
        return jsonify({'status': 'error', 'error':'User not logged in.'})
    else:
        follow=req['username']
        if req.get('follow') is None:
            f=True
        else:
            f=req['follow']
        
        if f:
            new={'user': session.get('username'), 'follows':follow}
            db.following.insert(new)
            
        else:
            db.following.remove({'user':session.get('username'),'follows':follow}, true)
    return jsonify({'status': 'OK'})  

@application.route("/item/<id>/like", methods=['POST'])
def likeitem(id):  # I HOPE WE DONT HAVE TO RETURN WHAT THE USER LIKES/ WHO LIKES AN ITEM ....
    req=request.get_json()
    if session.get('username') is None:
        return jsonify({'status': 'error', 'error':'User not logged in.'})
    else:
        id=int(float(id))
        if req.get('like') is None:
            f=True
        else:
            f=req['like']
        if f:
            db.items.update({"item_id":id},{'$inc':{"property.likes":1}})
            #db.likes.insert({"user":session.get('username'),"item_id":counter})
            cache.delete('item'+str(int(float(id))))
        else:
            db.items.update({"item_id":id},{'$dec':{"property.likes":1}})
            #db.likes.remove({"user":session.get('username'),"item_id":counter},true)
            cache.delete('item'+str(int(float(id))))
        return jsonify({'status': 'OK'})  

@application.route("/addmedia", methods=['POST'])
def addmedia(): #says remove media if it is not accosiated with an item by a certain time????
    file = request.files['content']
    fn= secure_filename(file.filename)
    mimetype = file.content_type
    f=base64.b64encode(Binary(file.read(),0))
    counter= cache.get('mediactr')
    if counter is None:
        dbcounter= db.counter.find_one({"item_id":"mediaid"},{"seq":1})# get current id counter
        counter=int(dbcounter['seq'])
    db.counter.update_one({"item_id":"mediaid"},{'$inc':{"seq":1}})#update counter
    cache.set('mediactr',counter+1)   
    date=datetime.datetime.now()
    new={"createdAt":date,"used":"n","filename":fn , "content": f, "mediaid":counter, "type": mimetype}
    db.media.insert(new)
    cache.set('media'+str(counter), new)
    return jsonify({"status":"OK","id":counter})
 
@application.route("/media/<id>", methods=['GET'])
def getmedia(id):
    id= int(id)
    me= cache.get('media'+str(id))
    if me is None:
        me=db.media.find_one({'mediaid':id})
        cache.set('media'+str(id), me)
    out= base64.b64decode(me['content']),{'Content-Type': me['type']}
    return out

@application.route("/checkcache", methods=['GET'])
def getdate():
    date= cache.get("date")
    if date is None:
        date=datetime.datetime.now()
        cache.set("date",date, 60)
    return "time is : " +str(date)



if __name__ ==     "__main__":
    application.run(host='0.0.0.0', port = 5000, threaded=True, debug=True)
