from flask import Flask, session, redirect, url_for, escape, request, render_template,jsonify
import sendmail
import keygen
import time
from pymongo import MongoClient

client = MongoClient()
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
    if db.accounts.find_one({"email":e}) is not None :
        #unique email
        return jsonify({'status': 'error', 'error':'Email Address already in use'})
    u= req['username']
    if db.accounts.find_one({"username":u}) is not None :
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
    if db.accounts.find_one({"username": u, "password": p, "verified":"true"}) is not None:
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
    if db.accounts.find_one({"email":e, "key":k})is not None:
        db.accounts.update_one({"email":e, "key":k},{'$set':{'verified':'true'}})
        return jsonify({'status': 'OK'})
    else:
        return jsonify({'status': 'error', 'error':'Email/Key combination could not be verified'})

@application.route("/additem", methods=['POST'])
def additem():
    req=request.get_json()
    if session.get('username') is None:
        return jsonify({'status': 'error', 'error':'User not logged in.'})
    else:
        con=req['content']
        db.counter.update_one({"item_id":"itemid"},{'$inc':{"seq":1}})#update counter
        counter= db.counter.find_one({"item_id":"itemid"},{"seq":1})# get current id counter
        if req.get('childType') is None:
            new= {"item_id":counter['seq'],"timestamp":time.time(), "username":session['username'], "content":con, "retweeted":0, "property":{"likes":0}}
        else:
            ct=req['childType'] #if child: retweet or reply, if not child: null
            if req.get('parent') is not None: # parent optional
                p=req['parent'] # item id of the original item being responded to
                new= {"item_id":counter['seq'],"timestamp":time.time(), "username":session['username'], "content":con, "childType":ct,"retweeted":0, "property":{"likes":0},"parent":p}
                if ct == "retweet": #increase parent retweet counter if retweeted
                    db.items.update_one({"item_id":p},{'$inc': {"retweeted":1}})# increment retweet count of parent by one         
    db.items.insert(new)
    #any other error situations?
    return jsonify({'status': 'OK', 'id':str(counter['seq'])})  

@application.route("/item/<id>", methods=['GET'])
def item(id):
    #id=request.args.get('id') 
    item= db.items.find_one({"item_id":int(float(id))}) #lmao
    if item is None:
        return jsonify({'status': 'error', 'error':'Chirp not found'})
    return jsonify({'status': 'OK', 'item':{'id':item['item_id'],'username':item['username'],'property':item['property'],'retweeted':item['retweeted'],'content':item['content'],'timestamp':item['timestamp']}})
@application.route("/search", methods=['POST'])
def search():
    req=request.get_json()
    if req.get('timestamp') is None:
        ts=time.time() #default is current time
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
   
    chirps=db.items.find({"timestamp":{ '$lte':ts}}).limit(l) # limits amount pulled by l (L NOT 1)
    out= {'status':'OK'}
    items=[]
    for chirp in chirps:
        c= {'id':chirp['item_id'],'username':chirp['username'],'property':chirp['property'],'retweeted':chirp['retweeted'],'content':chirp['content'],'timestamp':chirp['timestamp']}
        items.append(c)
    out['items']=items
    out['timestamp']=ts
    out['limit']=l

    return jsonify(out)

    
if __name__ ==     "__main__":
    application.run(host='0.0.0.0', port = 80)
