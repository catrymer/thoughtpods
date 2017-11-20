from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ThoughtPod, PodItem
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "ThoughtPods"


engine = create_engine('sqlite:///thoughtpods.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Returns a list of the existing ThoughtPods
@app.route('/')
@app.route('/pods/')
def Home():
    allpods = session.query(ThoughtPod)
    return render_template('index.html', allpods=allpods)


# Build a login page and process
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Log out functionality
@app.route('/gdisconnect/')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Returns a list of the items in a ThoughtPod List
@app.route('/pods/<int:pod_id>/')
def podList(pod_id):
    thoughtpod = session.query(ThoughtPod).filter_by(id=pod_id).one()
    items = session.query(PodItem).filter_by(thought_pod_id=thoughtpod.id)
    return render_template('podlist.html', thoughtpod=thoughtpod, items=items)


# Functionality to create a new ThoughtPod
@app.route('/pods/new/', methods=['GET', 'POST'])
def newThoughtPod():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newPod = ThoughtPod(pod_title=request.form['title'], description=request.form['description'])
        session.add(newPod)
        session.commit()
        return redirect(url_for('Home'))
    else:
        return render_template('newpod.html')


# Functionality to add a new item to an existing ThoughtPod List
@app.route('/pods/<int:pod_id>/new/', methods=['GET', 'POST'])
def newPodListItem(pod_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = PodItem(
            title=request.form['title'], url=request.form['url'],
            description=request.form['description'], time_investment=request.form['time_investment'],
            difficulty_level=request.form['difficulty_level'], thought_pod_id=pod_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('podList', pod_id=pod_id))
    else:
        return render_template('newpodlistitem.html', pod_id=pod_id)


# Functionality to edit individual items on the ThoughtPod Lists
@app.route('/pods/<int:pod_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editPodListItem(pod_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(PodItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['url']:
            editedItem.url = request.form['url']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['time_investment']:
            editedItem.time_investment = request.form['time_investment']
        if request.form['difficulty_level']:
            editedItem.difficulty_level = request.form['difficulty_level']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('podList', pod_id=pod_id))
    else:
        return render_template(
            'editpodlistitem.html', pod_id=pod_id, item_id=item_id, item=editedItem)


# Functionality to delete individual items from the ThoughtPod Lists
@app.route('/pods/<int:pod_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deletePodListItem(pod_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(PodItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('podList', pod_id=pod_id))
    else:
        return render_template('deletepodlistitem.html', item=itemToDelete)


# Add JSON endpoints
@app.route('/pods/JSON/')
def thoughtPodJSON():
    thoughtPods = session.query(ThoughtPod).all()
    return jsonify(thoughtPods=[i.serialize for i in thoughtPods])


@app.route('/pods/<int:pod_id>/JSON/')
def thoughtPodListJSON(pod_id):
    thoughtpod = session.query(ThoughtPod).filter_by(id=pod_id).one()
    allPodItems = session.query(PodItem).filter_by(thought_pod_id=thoughtpod.id).all()
    return jsonify(allPodItems=[i.serialize for i in allPodItems])


@app.route('/pods/<int:pod_id>/<int:item_id>/JSON/')
def podListItemJSON(pod_id, item_id):
    onePodItem = session.query(PodItem).filter_by(id=item_id).one()
    return jsonify(onePodItem=onePodItem.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
