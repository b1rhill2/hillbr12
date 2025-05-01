# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
from flask import current_app as app
from flask import render_template, redirect, request, session, url_for, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from datetime import  datetime
from typing import Dict
from .utils.database.database  import database
from werkzeug.datastructures   import ImmutableMultiDict
from pprint import pprint
import json
import random
import functools
from . import socketio
db = database()


#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return secure_function

def getUser():
    return session['email'] if 'email' in session else 'Unknown'

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', default=None)
    return redirect('/home')

@app.route('/processlogin', methods = ["POST","GET"])
def processlogin():
    # Extract credentials from the form
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))


    # Authenticate the user against the database
    authentication_result = db.authenticate(form_fields['email'], form_fields['password'])

    print(f'auth result: {authentication_result}')

    if authentication_result.get('success') == 1:
        # If authentication is successful, store encrypted email in session
        session['email'] = db.reversibleEncrypt('encrypt', form_fields['email'])
        status = {'success': 1}
    else:
        # If authentication fails, return failure status
        status = {'success': 0}

    # Return status as JSON for AJAX processing
    return json.dumps(status)


#######################################################################################
# CHATROOM RELATED
#######################################################################################
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=getUser())

@socketio.on('joined', namespace='/chat')
def joined(message):
    join_room('main')
    user = getUser()
    user = db.reversibleEncrypt("decrypt", user)
    # If user is bytes, decode it to string
    if isinstance(user, bytes):
        user = user.decode('utf-8')
    emit('status', {'msg': user + ' has entered the room.', 'style': 'width: 100%;color:blue;text-align: center'}, room='main')

@socketio.on('text', namespace='/chat')
def text(message):

    current_user = getUser()

    # If current_user is bytes, decode it
    if isinstance(current_user, bytes):
        current_user = current_user.decode('utf-8')

    #checks if decryption if needed
    if hasattr(db, 'reversibleEncrypt'):
        current_user = db.reversibleEncrypt("decrypt", current_user)
        if isinstance(current_user, bytes):
            current_user = current_user.decode('utf-8')

    msg_text = message.get("msg", "")

    is_owner = (current_user == "owner@email.com")

    # create and emit the message
    emit('message', {
        'msg': f"{current_user}: {msg_text}",
        'style': 'color:blue;text-align: right' if is_owner else 'color:grey;text-align: left'
    }, room='main')

@socketio.on('left', namespace='/chat')
def left(message):
    leave_room('main')
    #leaving message
    user = getUser()
    user = db.reversibleEncrypt("decrypt", user)
    if isinstance(user, bytes):
        user = user.decode('utf-8')

    emit('status', {'msg': user + ' has left the room.',
                   'style': 'width: 100%;color:red;text-align: center'},
         room='main')

#######################################################################################
# OTHER
#######################################################################################
@app.route('/')

def root():
    return redirect('/home')

@app.route('/home')

def home():
    print(db.query('SELECT * FROM users'))
    x = random.choice(['I started university when I was a wee lad of 15 years.','I have a pet sparrow.','I write poetry.'])
    return render_template('home.html', user=getUser(), fun_fact = x)


@app.route('/projects')

def projects():
    return render_template('projects.html', user=getUser())

@app.route('/piano')

def piano():
    return render_template('piano.html', user=getUser())

@app.route('/resume')

def resume():
    resume_data = db.getResumeData()
    pprint(resume_data)
    return render_template('resume.html', user=getUser(), resume_data = resume_data)


# @app.route("/static/<path:path>")
# def static_dir(path):
#     return send_from_directory("static", path)

s.html