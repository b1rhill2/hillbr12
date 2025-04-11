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

    # def __init__(self, purge = False):
    #
    #     # Grab information from the configuration file
    #     self.database       = 'db'
    #     # self.host = '127.0.0.1'
    #     self.host = '34.60.68.195'
    #     # self.host = 'host.docker.internal'
    #     self.user           = 'master'
    #     self.port           = 3306
    #     self.password       = 'master'
    #     self.tables         = ['institutions', 'positions', 'experiences', 'skills','feedback', 'users']
    #
    def __init__(self, purge=False):
        # Get database configuration
        db_config = get_db_config()

        # Set attributes
        self.database = db_config['database']
        self.host = db_config['host']
        self.user = db_config['user']
        self.port = db_config['port']
        self.password = db_config['password']
        self.tables = ['institutions', 'positions', 'experiences', 'skills', 'feedback', 'users']

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

        cnx = mysql.connector.connect(host     = self.host,
                                      user     = self.user,
                                      password = self.password,
                                      port     = self.port,
                                      database = self.database,
                                      charset  = 'latin1'
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
        cnx = mysql.connector.connect(user=self.user, password=self.password, host=self.host, database=self.database)
        cursor = cnx.cursor()

        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        # check if tables already have data only populate if empty or purge=True
        if purge:
            # if purge is true drop the tables in reverse order of dependency
            print("Purging existing tables...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            tables = ['skills', 'experiences', 'positions', 'institutions', 'feedback', 'users']
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
                   CREATE TABLE IF NOT EXISTS institutions (
                       inst_id INT AUTO_INCREMENT PRIMARY KEY,
                       type VARCHAR(255),
                       name VARCHAR(255) NOT NULL,
                       department VARCHAR(255),
                       address VARCHAR(255),
                       city VARCHAR(255),
                       state VARCHAR(50),
                       zip VARCHAR(20),
                       UNIQUE KEY inst_name_unique (name, department)
                   );
               """)

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS positions (
                       position_id INT AUTO_INCREMENT PRIMARY KEY,
                       inst_id INT,
                       title VARCHAR(255) NOT NULL,
                       responsibilities TEXT,
                       start_date DATE,
                       end_date DATE,
                       FOREIGN KEY (inst_id) REFERENCES institutions(inst_id),
                       UNIQUE KEY position_unique (inst_id, title, start_date)
                   );
               """)

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS experiences (
                       experience_id INT AUTO_INCREMENT PRIMARY KEY,
                       position_id INT,
                       name VARCHAR(255) NOT NULL,
                       description TEXT,
                       hyperlink VARCHAR(255),
                       start_date DATE,
                       end_date DATE,
                       FOREIGN KEY (position_id) REFERENCES positions(position_id),
                       UNIQUE KEY experience_unique (position_id, name)
                   );
               """)

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS skills (
                       skill_id INT AUTO_INCREMENT PRIMARY KEY,
                       experience_id INT,
                       name VARCHAR(255) NOT NULL,
                       skill_level VARCHAR(50),
                       FOREIGN KEY (experience_id) REFERENCES experiences(experience_id),
                       UNIQUE KEY skill_unique (experience_id, name)
                   );
               """)

            cursor.execute("""
                   CREATE TABLE IF NOT EXISTS feedback (
                       feedback_id INT AUTO_INCREMENT PRIMARY KEY,
                       name VARCHAR(255),
                       email VARCHAR(255),
                       comment TEXT,
                       UNIQUE KEY feedback_unique (email, comment(100))
                   );
               """)

            cursor.execute("""
                  CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('owner', 'guest', 'user') NOT NULL
                );  
            """)

            # CSV files table columns
            csv_files = [
                ('institutions.csv', 'institutions', ['type', 'name', 'department', 'address', 'city', 'state', 'zip']),
                ('positions.csv', 'positions', ['inst_id', 'title', 'responsibilities', 'start_date', 'end_date']),
                ('experience.csv', 'experiences',
                 ['position_id', 'name', 'description', 'hyperlink', 'start_date', 'end_date']),
                ('skills.csv', 'skills', ['experience_id', 'name', 'skill_level']),
                ('feedback.csv', 'feedback', ['name', 'email', 'comment']),
                ('users.csv', 'users', ['email', 'password', 'role'])
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

            # check if institutions table exists and has data
            cursor.execute("SHOW TABLES LIKE 'institutions'")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("Tables don't exist. Creating them...")
                # call this function recursively with purge=True to create tables
                self.createTables(purge=True, data_path=data_path)
            else:
                # check if institutions table has data
                cursor.execute("SELECT COUNT(*) FROM institutions")
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


    def getResumeData(self):
        # cnx = mysql.connector.connect(user='master', password='master', host='host.docker.internal', database='db')
        cnx = mysql.connector.connect(user='master', password='master', host='34.60.68.195', database='db')
        cursor = cnx.cursor(dictionary=True)

        # start building the data
        resume_data = {}

        # fetch institutions
        cursor.execute("SELECT * FROM institutions")
        institutions = cursor.fetchall()

        # fetch positions for each institution
        for institution in institutions:
            inst_id = institution['inst_id']
            resume_data[inst_id] = {
                'name': institution['name'],
                'department': institution['department'],
                'address': institution['address'],
                'city': institution['city'],
                'state': institution['state'],
                'zip': institution['zip'],
                'type': institution['type'],
                'positions': {}
            }
            # print(f"Institution data has been inputted into the the resume {resume_data[inst_id]}")
            # fetch positions for each institution
            cursor.execute("SELECT * FROM positions WHERE inst_id = %s", (inst_id,))
            positions = cursor.fetchall()

            for position in positions:
                pos_id = position['position_id']
                resume_data[inst_id]['positions'][pos_id] = {
                    'title': position['title'],
                    'responsibilities': position['responsibilities'],
                    'start_date': position['start_date'],
                    'end_date': position['end_date'],
                    'experiences': {}
                }

                # fetch experiences for each position
                cursor.execute("SELECT * FROM experiences WHERE position_id = %s", (pos_id,))
                experiences = cursor.fetchall()

                for experience in experiences:
                    exp_id = experience['experience_id']
                    resume_data[inst_id]['positions'][pos_id]['experiences'][exp_id] = {
                        'name': experience['name'],
                        'description': experience['description'],
                        'hyperlink': experience['hyperlink'],
                        'start_date': experience['start_date'],
                        'end_date': experience['end_date'],
                        'skills': {}
                    }

                    # fetch skills for each experience
                    cursor.execute("SELECT * FROM skills WHERE experience_id = %s", (exp_id,))
                    skills = cursor.fetchall()

                    for skill in skills:
                        skill_id = skill['skill_id']
                        resume_data[inst_id]['positions'][pos_id]['experiences'][exp_id]['skills'][skill_id] = {
                            'name': skill['name'],
                            'skill_level': skill['skill_level']
                        }

        cursor.close()
        cnx.close()
        # print(resume_data)
        return resume_data

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
        cnx = mysql.connector.connect(user=self.user, password=self.password, host=self.host, database=self.database)
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
        #processing user csv file with pw encrypt
        try:
            with open(file_path, mode='r') as csv_file:
                reader = csv.reader(csv_file)
                headers = next(reader)
                #check if header match columns
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
        cnx = mysql.connector.connect(user=self.user, password=self.password, host=self.host, database=self.database)
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