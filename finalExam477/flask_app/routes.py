import functools

from flask import current_app as app
from flask import render_template, redirect, request, session, url_for, abort, copy_current_request_context, jsonify
from .utils.database.database import database
from functools import wraps
from datetime import datetime, timedelta
from pprint import pprint
import json
import random

db = database()


#####################################################################################
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
    return redirect('/dashboard')

@app.route('/processlogin', methods = ["POST","GET"])
def processlogin():
    # Extract credentials from the form
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))


    # Authenticate the user against the database
    authentication_result = db.authenticate(form_fields['email'], form_fields['password'])

    print(f'auth result: {authentication_result}')

    if authentication_result.get('success') == 1:
        # If authentication is successful, store encrypted email in session
        session['email'] = form_fields['email']
        status = {'success': 1}
    else:
        # If authentication fails, return failure status
        status = {'success': 0}

    # Return status as JSON for AJAX processing
    return json.dumps(status)

#######################################################################################
# Sign Up RELATED
######################################################################################

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/processSignup', methods = ["PUT"])
def processSignup():
    # Extract credentials from the form
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))


    # Authenticate the user against the database
    register_result = db.createUser(form_fields['email'], form_fields['password'], form_fields['role'])

    print(f'auth result: {register_result}')

    if register_result.get('success') == 1:
        # If authentication is successful, store encrypted email in session
        status = {'success': 1}
    else:
        # If authentication fails, return failure status
        status = {'success': 0}

    # Return status as JSON for AJAX processing
    return json.dumps(status)



#######################################################################################
# Event functions
#####################################################################################
def event_access_required(func):
    @wraps(func)
    def secure_function(id, *args, **kwargs):
        user_email = session.get('email')
        if not user_email:
            return redirect(url_for('login', next=request.url))

        event_data = db.get_event_access(id, user_email)

        if event_data:
            return func(event_data, *args, **kwargs)  # Pass event_data to the route
        else:
            abort(403)  # Forbidden - User is not authorized

    return secure_function


@app.route('/event/<int:id>', methods=["POST", "GET"])
@login_required
@event_access_required
def event(authorized_event_data):
    event_id = authorized_event_data['event_id']
    print(f"Route /event/{event_id}: Accessed")

    detailed_event_data = db.eventDataRequest(event_id)
    print(f"Route /event/{event_id}: Detailed event data fetched: {detailed_event_data}")

    if detailed_event_data and detailed_event_data.get(event_id):
        event = detailed_event_data[event_id]
        event['start_date'] = datetime.strptime(event['start_date'], '%Y-%m-%d').date()
        event['end_date'] = datetime.strptime(event['end_date'], '%Y-%m-%d').date()
        print(f"Route /event/{event_id}: Parsed start and end dates: {event['start_date']}, {event['end_date']}")

        user_email = session.get('email')
        user_data = db.getUserByID(user_email)  # Get the user data

        if user_data and 'user_id' in user_data:
            user_id = user_data['user_id']
            print(f"Route /event/{event_id}: Current user: {user_email} (ID: {user_id})")

            # Get all participants' availability data
            all_participants_availability = db.get_all_participants_availability(event_id)
            print(f"Route /event/{event_id}: All participants availability data fetched")
            all_availability_json = json.dumps(all_participants_availability)

            return render_template('/event.html',
                                  data=detailed_event_data,
                                  user_data=user_data,  # Pass user data to the template
                                  others_availability=all_availability_json)
        else:
            print(f"Route /event/{event_id}: Could not retrieve user ID")
            abort(500)  # Or handle this error appropriately
    else:
        print(f"Route /event/{event_id}: Detailed event data not found")
        abort(404)
# ... (rest of your routes) ...

@app.route('/create-event')
@login_required
def createEvent():
    return render_template('create-event.html', user=getUser())

@app.route('/joinEvent')
@login_required
def joinEvent():
    user = getUser()
    user_events_with_creator_info = db.myEvents(user)
    return render_template('/join-event.html', data=user_events_with_creator_info)

@app.route('/processCreateEvent', methods=["POST", "GET"])
def processCreateEvent():
    current_user = getUser()
    print(f"Current User: {current_user}")

    if current_user == "Unknown":
        return redirect('/login')

    #extract credentials from the form
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))

    #authenticate the user against the database
    createEvent_result = db.createEvent(current_user, form_fields['eventName'], form_fields['startDate'], form_fields['endDate'],
                                        form_fields['startTime'], form_fields['endTime'], form_fields['invitees'])

    print(f'Event result: {createEvent_result}')

    if createEvent_result.get('success') == 1:
        # If event created is successful, store encrypted email in session
        status = {'success': 1, 'event_id': createEvent_result.get('event_id')}
    else:
        # If event created fails, return failure status
        status = {'success': 0, 'error': createEvent_result.get('error', 'Unknown error')}

    # Return status as JSON for AJAX processing
    return json.dumps(status)


####################################################################################
# User Availibility data manipulation
####################################################################################
@app.route('/save-availability', methods=['POST'])
@login_required
def save_availability():
    data = request.json

    if not data or 'eventId' not in data or 'availabilityData' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    # Get the current user's ID from your authentication system
    user = getUser()
    user_id = db.getUserByID(user)
    # user_id = current_user.id  # Adjust this based on how you identify users
    event_id = data['eventId']
    availability_data = data['availabilityData']

    # Call database function to save the data
    success = db.save_user_availability(user_id, event_id, availability_data)

    if success:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': 'Failed to save availability data'}), 500


@app.route('/get-all-availability', methods=['GET'])
@login_required
def get_all_availability():
    event_id = request.args.get('eventId')
    if not event_id:
        return jsonify({'error': 'Event ID is required'}), 400

    # Call database function to get all participants' data
    availability_data = db.get_all_participants_availability(event_id)

    return jsonify({'availabilityData': availability_data}), 200
###################################################################################
# MISC
####################################################################################


@app.route('/')
def root():
    return redirect('/dashboard')

@app.route('/dashboard')

def dashboard():
    user = getUser()
    return render_template('dashboard.html', user=user)


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r
