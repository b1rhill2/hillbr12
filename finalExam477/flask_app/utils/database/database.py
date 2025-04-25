import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import hashlib
import os
import cryptography
from cryptography.fernet import Fernet
from math import pow
from flask_app.utils.database.db_config import get_db_config

class database:

    def __init__(self, purge=False):
        # Get database configuration
        db_config = get_db_config()

        # Set attributes
        self.database = db_config['database']
        self.user = db_config['user']
        self.password = db_config['password']

        # Check if we're using unix socket or host
        if 'unix_socket' in db_config:
            self.unix_socket = db_config['unix_socket']
            self.host = None
            self.port = None
        else:
            self.host = db_config['host']
            self.port = db_config['port']
            self.unix_socket = None

        self.tables = ['users']

        # NEW IN HW 3-----------------------------------------------------------------
        self.encryption     =  {   'oneway': {'salt' : b'averysaltysailortookalongwalkoffashortbridge',
                                                 'n' : int(pow(2,5)),
                                                 'r' : 9,
                                                 'p' : 1
                                             },
                                'reversible': { 'key' : '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE='}
                                }
        #-----------------------------------------------------------------------------

    def query(self, query = "SELECT * FROM users", parameters = None):

        # Create connection
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket,
                charset='latin1'
            )
        else:
            cnx = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                database=self.database,
                charset='latin1'
            )


        if parameters is not None:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query, parameters)
        else:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query)

        # Fetch one result
        row = cur.fetchall()
        cnx.commit()

        if "INSERT" in query:
            cur.execute("SELECT LAST_INSERT_ID()")
            row = cur.fetchall()
            cnx.commit()
        cur.close()
        cnx.close()
        return row

    def createTables(self, purge=False, data_path='flask_app/database/'):
        # mysql connection
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor()

        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        # check if tables already have data only populate if empty or purge=True
        if purge:
            # if purge is true drop the tables in reverse order of dependency
            print("Purging existing tables...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            tables = ['users']
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table};")
                    print(f"Dropped table {table}")
                except mysql.connector.Error as err:
                    print(f"Error dropping table {table}: {err}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            # create tables
            print("Creating tables...")

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users (
                     user_id INT AUTO_INCREMENT PRIMARY KEY,
                     email VARCHAR(255) UNIQUE NOT NULL,
                     password VARCHAR(255) NOT NULL,
                     role ENUM('owner', 'guest', 'user') NOT NULL
                 );  
             """)

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS events (
                     `event_id`         int(11) NOT NULL auto_increment PRIMARY KEY,
                    `event_name`       varchar(100) NOT NULL    ,        
                    `start_date`        DATE NOT NULL     ,             
                    `end_date`          DATE NOT NULL    ,               
                    `start_time`        TIME NOT NULL    ,                
                    `end_time`          TIME NOT NULL  ,                 
                    `creator_id`        INT NOT NULL                    

                 );  
             """)

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS event_participants (
                        `id`         int AUTO_INCREMENT PRIMARY KEY,
                        `event_id`   INT          NOT NULL,
                        `user_email` VARCHAR(100) NOT NULL 
                 );  
             """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_avail (
                    `avail_id`          INT AUTO_INCREMENT PRIMARY KEY,
                    `user_id`           INT NOT NULL,
                    `event_id`         int(11) NOT NULL,
                    `date`             DATE NOT NULL,                
                    `start_time`        TIME NOT NULL,                
                    `end_time`          TIME NOT NULL,                 
                    `avail_status`      TIME NOT NULL                       
                 );  
             """)

            # CSV files table columns
            csv_files = [
                ('users.csv', 'users', ['email', 'password', 'role']),
                ('events.csv', 'events', ['event_name', 'start_date', 'end_date', 'start_time', 'end_time', 'creator_id']),
                ('event_participants.csv', 'event_participants', ['event_id', 'user_email']),
                ('user_avail.csv', 'user_avail', ['user_id', 'event_id', 'date', 'start_time', 'end_time', 'avail_status'])
            ]

            # parce CSV files in order of dependency
            for csv_filename, table_name, columns in csv_files:
                file_path = os.path.join(data_path, 'initial_data', csv_filename)

                # check if file exists
                if os.path.exists(file_path):
                    print(f"{csv_filename} File found!")
                else:
                    print(f"{csv_filename} File not found at {file_path}. Check the path.")
                    continue

                # Special handling for users.csv to encrypt passwords
                if table_name == 'users':
                    self.process_users_csv(file_path, columns)
                    continue

                # process specific CSV file
                with open(file_path, mode='r') as csvfile:
                    reader = csv.reader(csvfile)
                    headers = next(reader)

                    # check CSV headers match expected columns
                    if len(headers) != len(columns):
                        print(
                            f"{csv_filename} has mismatched headers. Expected: {columns}, Found: {headers}. Skipping this file.")
                        continue

                    cursor.execute("START TRANSACTION;")

                    for row in reader:
                        # replace empty values with None
                        row = [value if value else None for value in row]

                        if len(row) != len(columns):
                            print(f"Skipping row due to incorrect format: {row}")
                            continue

                        try:
                            # build insert statement with ON DUPLICATE KEY UPDATE make sure there are no duplicate information
                            placeholders = ', '.join(['%s'] * len(columns))
                            sql = f"""
                                    INSERT INTO {table_name} ({', '.join(columns)})
                                    VALUES ({placeholders})
                                    ON DUPLICATE KEY UPDATE {', '.join([f'{col}=VALUES({col})' for col in columns])};
                                """
                            cursor.execute(sql, row)
                        except mysql.connector.Error as err:
                            print(f"Error occurred: {err} - Skipping row: {row}")

                    # commit after each file
                    cnx.commit()
                    print(f"Committed data for {table_name}")
        else:
            # if purge is False only create tables if they don't exist yet
            print("Checking if tables need to be created...")

            # check if users table exists and has data
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("Tables don't exist. Creating them...")
                # call this function recursively with purge=True to create tables
                self.createTables(purge=True, data_path=data_path)
            else:
                # check if users table has data
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                if count == 0:
                    print("Tables exist but are empty. Populating them...")
                    # call this function recursively with purge=True to populate tables
                    self.createTables(purge=True, data_path=data_path)
                else:
                    print("Tables already exist and contain data. Skipping table creation.")

        cursor.close()
        cnx.close()
        print('Database tables setup complete.')

    #######################################################################################
    # AUTHENTICATION RELATED
    #######################################################################################

    def onewayEncrypt(self, string):
        encrypted_string = hashlib.scrypt(string.encode('utf-8'),
                                          salt=self.encryption['oneway']['salt'],
                                          n=self.encryption['oneway']['n'],
                                          r=self.encryption['oneway']['r'],
                                          p=self.encryption['oneway']['p']
                                          ).hex()
        return encrypted_string

    def createUser(self, email='me@email.com', password='password', role='user'):
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor()
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            cursor.close()
            cnx.close()
            return {'success': 0, 'error': 'User already exists'}

        # Encrypt the password with a new salt
        encrypted_password = self.onewayEncrypt(password)

        try:
            # Insert the new user with encrypted password and salt
            cursor.execute(
                "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
                (email, encrypted_password, role)
            )
            cnx.commit()

            # Get the user ID
            cursor.execute("SELECT LAST_INSERT_ID()")
            user_id = cursor.fetchone()[0]

            cursor.close()
            cnx.close()
            return {'success': 1, 'user_id': user_id, 'email': email, 'role': role}

        except mysql.connector.Error as err:
            cursor.close()
            cnx.close()
            return {'success': 0, 'error': f'Database error: {str(err)}'}

    def process_users_csv(self, file_path, columns):
        print("processing users csv")
        # processing user csv file with pw encrypt
        try:
            with open(file_path, mode='r') as csv_file:
                reader = csv.reader(csv_file)
                headers = next(reader)
                # check if header match columns
                if len(headers) != len(columns):
                    print(f"users.csv has mismatched header expected: {columns}. skipping this file.")
                    return

                for row in reader:
                    if len(row) != len(columns):
                        print(f"Skipping row due to incorrect format: {row}")
                        continue

                    email = row[0]
                    password = row[1]
                    role = row[2]

                    # Create user with encrypted password
                    result = self.createUser(email, password, role)
                    if result['success']:
                        print(f"Created user: {email} with role: {role}")
                    else:
                        print(f"Failed to create user: {email} - {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"Error processing users CSV: {str(e)}")

    def authenticate(self, email='me@email.com', password='password'):
        print(f"authenticating")
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor()
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        try:
            # check if user exists
            cursor.execute("SELECT password, role FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            print(f'database result: {result}')

            if not result:
                print(f"No user found for email: {email}")
                return {'success': 0, 'error': 'Invalid email or password'}

            stored_password, role = result

            # hash the input password with same global salt
            hashed_input = self.onewayEncrypt(password)

            if hashed_input == stored_password:
                print("Authentication successful")

                return {'success': 1, 'email': email, 'role': role}
            else:
                print("Authentication failed: wrong password")
                return {'success': 0, 'error': 'Invalid email or password'}

        except mysql.connector.Error as err:
            print(f"DB error: {str(err)}")
            return {'success': 0, 'error': f'Database error: {str(err)}'}

        finally:
            cursor.close()
            cnx.close()




    def reversibleEncrypt(self, type, message):
        fernet = Fernet(self.encryption['reversible']['key'])

        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message

    def send_from_directory(self, string, data_path=''):
        print("returning path")

    #######################################################################################
    # CREATING EVENTS RELATED
    #######################################################################################
    def createEvent(self, user_email='me@email.com', eventname='name', startdate='startdate',
                    enddate='enddate', starttime='starttime', endtime='endtime', invitees=None):

        if invitees is None:
            invitees = [""]

        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor()
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        creator = user_email
        print(f"Event Creator: {creator}")

        #check if user exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (creator,))
        user_data = cursor.fetchone()  # Fetch the first (and hopefully only) matching row

        if user_data:
            creator_id = user_data[0]  # Access 'user_id' from the fetched row (assuming dictionary cursor)
            print(f"Creator User ID: {creator_id}")
        else:
            # Handle the case where the user with the given email is not found
            print(f"Error: User with email '{creator}' not found.")
            return  # Or raise an exception, depending on your application's logic

        try:
            #insert new event
            cursor.execute(
                   "INSERT INTO events (event_name, start_date, end_date, start_time, end_time, creator_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (eventname, startdate, enddate, starttime, endtime, creator_id)
            )
            cnx.commit()
            print(f"Committed data for events")
            event_id = cursor.lastrowid

            # Add creator as participant
            cursor.execute("INSERT INTO event_participants (event_id, user_email) VALUES (%s, %s)",
                           (event_id, user_email))
            print(f"Added {creator_id} as a Participant")
            # Add invitees
            invitees = [email.strip() for email in invitees.split(',')]
            for email in invitees:
                cursor.execute("INSERT INTO event_participants (event_id, user_email) VALUES (%s, %s)",
                               (event_id, email))
                print(f"Added {email}")
            cnx.commit()
            print(f"Committed Data for Participants")
            cursor.close()
            cnx.close()
            return {'success': 1, 'event_id': event_id}

        except mysql.connector.Error as err:
            cursor.close()
            cnx.close()
            return {'success': 0, 'error': f'Database error: {str(err)}'}

    def eventDataRequest(self, event_id):
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        event_data = {}

        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()

        if event:
            event_data[event['event_id']] = {
                'event_name': event['event_name'],
                'start_date': str(event['start_date']),
                'end_date': str(event['end_date']),
                'start_time': str(event['start_time']),
                'end_time': str(event['end_time']),
                'creator_id': event['creator_id'],
                'event_participants': {}
            }

            cursor.execute("SELECT * FROM event_participants WHERE event_id = %s", (event_id,))
            event_participants = cursor.fetchall()

            for participant in event_participants:
                participantID = participant['id']
                event_data[event['event_id']]['event_participants'][participantID] = {
                    'user_email': participant['user_email']
                }
        else:
            event_data = None

        print(f"event_data: {event_data}")

        cursor.close()
        cnx.close()
        return event_data

    def myEvents(self, user_email):
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        query = '''
               SELECT
                   e.event_id,
                   e.event_name,
                   e.creator_id,
                   e.start_date,
                   e.end_date,
                   u.email AS creator_email
               FROM events e
               LEFT JOIN event_participants ep ON e.event_id = ep.event_id
               JOIN users u ON e.creator_id = u.user_id
               WHERE e.creator_id = (SELECT user_id FROM users WHERE email = %s)
                  OR ep.user_email = %s
               GROUP BY e.event_id  -- avoids duplicate entries if a user is both creator and participant
           '''
        cursor.execute(query, (user_email, user_email))
        my_events_with_creator = cursor.fetchall()
        print(f'my_events_with_creator')

        cursor.close()
        cnx.close()
        return my_events_with_creator

    def getUserByID (self, user_email):
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor(dictionary=True, buffered=True)
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        cursor.execute("SELECT user_id FROM users WHERE email = %s",(user_email,))
        result = cursor.fetchone()

        cursor.close()
        cnx.close()
        return result

    def get_event_access(self, event_id, user_email):
        if self.unix_socket:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                unix_socket=self.unix_socket
            )
        else:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database
            )
        cursor = cnx.cursor(dictionary=True, buffered=True)

        try:
            cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

            query = '''
                SELECT
                    e.event_id  -- Just need the event_id to confirm access
                FROM events e
                LEFT JOIN event_participants ep ON e.event_id = ep.event_id
                LEFT JOIN users u ON e.creator_id = u.user_id
                WHERE e.event_id = %s
                  AND (u.email = %s OR ep.user_email = %s)
            '''
            cursor.execute(query, (event_id, user_email, user_email))
            event_access = cursor.fetchone()
            return event_access
        finally:
            cursor.close()
            cnx.close()

    #######################################################################################
    # USERs Availability
    #######################################################################################

    def save_user_availability(self, user_id, event_id, availability_data):
        """
        Save batch user availability data to database with improved error handling and retry logic

        Args:
            user_id (dict or int): The user's ID or a dict containing user_id
            event_id (int): The event's ID
            availability_data (list): List of dictionaries containing availability info

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Handle if user_id is a dictionary
            if isinstance(user_id, dict) and 'user_id' in user_id:
                user_id = user_id['user_id']

            # Create connection with transaction isolation level set
            if self.unix_socket:
                cnx = mysql.connector.connect(
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    unix_socket=self.unix_socket
                )
            else:
                cnx = mysql.connector.connect(
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    database=self.database
                )
            # Set transaction isolation level to READ COMMITTED to reduce lock contention
            cursor = cnx.cursor()
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            # Set a longer timeout for locks to reduce deadlocks
            cursor.execute("SET SESSION innodb_lock_wait_timeout = 120")

            # Begin transaction
            cnx.start_transaction()

            max_retries = 3
            retry_count = 0
            success = False

            while not success and retry_count < max_retries:
                try:
                    # Process each availability item
                    for item in availability_data:
                        # Use INSERT ... ON DUPLICATE KEY UPDATE to handle both insert and update in one query
                        # This is more efficient and reduces chances of race conditions
                        query = """
                        INSERT INTO user_avail 
                        (user_id, event_id, date, start_time, end_time, avail_status) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                        avail_status = VALUES(avail_status)
                        """

                        cursor.execute(
                            query,
                            (user_id, event_id, item['date'], item['startTime'],
                             item['endTime'], item['availability'])
                        )

                    # If we got here without errors, we can commit
                    cnx.commit()
                    success = True
                    print(f"Successfully saved availability data after {retry_count} retries")

                except mysql.connector.errors.InternalError as e:
                    # Handle deadlock errors by retrying
                    if e.errno == 1213:  # Deadlock error code
                        retry_count += 1
                        print(f"Deadlock encountered, retry attempt {retry_count}")
                        cnx.rollback()
                        # Add a small delay before retrying to allow locks to clear
                        import time
                        time.sleep(0.5 * retry_count)
                    else:
                        # Re-raise other internal errors
                        raise
                except mysql.connector.errors.IntegrityError as e:
                    # Handle duplicate key errors more gracefully
                    if e.errno == 1062:  # Duplicate key error code
                        print(f"Duplicate key encountered, retrying with ON DUPLICATE KEY UPDATE")
                        cnx.rollback()
                        retry_count += 1
                    else:
                        # Re-raise other integrity errors
                        raise

            cursor.close()
            cnx.close()
            return success

        except Exception as e:
            # Rollback on error
            if 'cnx' in locals() and cnx is not None:
                cnx.rollback()
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
            if 'cnx' in locals() and cnx is not None:
                cnx.close()
            print(f"Database error in save_user_availability: {str(e)}")
            return False

    def get_user_availability(self, user_id, event_id):
        """
        Get user's availability data for an event

        Args:
            user_id (dict or int): The user's ID or a dict containing user_id
            event_id (int): The event's ID

        Returns:
            list: List of dictionaries containing availability data
        """
        try:
            # Handle if user_id is a dictionary
            if isinstance(user_id, dict) and 'user_id' in user_id:
                user_id = user_id['user_id']

            if self.unix_socket:
                cnx = mysql.connector.connect(
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    unix_socket=self.unix_socket
                )
            else:
                cnx = mysql.connector.connect(
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    database=self.database
                )
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

            cursor.execute(
                "SELECT DATE_FORMAT(date, '%Y-%m-%d') AS date, TIME_FORMAT(start_time, '%H:%i') AS start_time, TIME_FORMAT(end_time, '%H:%i') AS end_time, avail_status AS availability FROM user_avail WHERE event_id = %s AND user_id = %s",
                (event_id, user_id)
            )
            availability_data = cursor.fetchall()
            return availability_data
        except mysql.connector.Error as err:
            print(f"Database error fetching availability: {err}")
            return []
        finally:
            cursor.close()
            cnx.close()

    def get_all_participants_availability(self, event_id):
        """
        Fetch availability data for all participants of an event
        """
        try:
            if self.unix_socket:
                cnx = mysql.connector.connect(
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    unix_socket=self.unix_socket
                )
            else:
                cnx = mysql.connector.connect(
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    database=self.database
                )
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

            query = """
            SELECT ua.user_id, 
                   u.email, 
                   DATE_FORMAT(ua.date, '%Y-%m-%d') AS date, 
                   TIME_FORMAT(ua.start_time, '%H:%i') AS start_time, 
                   TIME_FORMAT(ua.end_time, '%H:%i') AS end_time, 
                   ua.avail_status AS availability
            FROM user_avail ua
            JOIN users u ON ua.user_id = u.user_id
            WHERE ua.event_id = %s
            """

            cursor.execute(query, (event_id,))
            results = cursor.fetchall()

            cursor.close()
            cnx.close()

            return results
        except Exception as e:
            print(f"Error fetching all participants availability: {e}")
            return []