import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import datetime
import os


class database:

    def __init__(self, purge = False):

        # Grab information from the configuration file
        self.database       = 'db'
        self.host           = 'host.docker.internal'
        self.user           = 'master'
        self.port           = 3306
        self.password       = 'master'

    def query(self, query = "SELECT CURDATE()", parameters = None):

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

    def about(self, nested=False):    
        query = """select concat(col.table_schema, '.', col.table_name) as 'table',
                          col.column_name                               as column_name,
                          col.column_key                                as is_key,
                          col.column_comment                            as column_comment,
                          kcu.referenced_column_name                    as fk_column_name,
                          kcu.referenced_table_name                     as fk_table_name
                    from information_schema.columns col
                    join information_schema.tables tab on col.table_schema = tab.table_schema and col.table_name = tab.table_name
                    left join information_schema.key_column_usage kcu on col.table_schema = kcu.table_schema
                                                                     and col.table_name = kcu.table_name
                                                                     and col.column_name = kcu.column_name
                                                                     and kcu.referenced_table_schema is not null
                    where col.table_schema not in('information_schema','sys', 'mysql', 'performance_schema')
                                              and tab.table_type = 'BASE TABLE'
                    order by col.table_schema, col.table_name, col.ordinal_position;"""
        results = self.query(query)
        if nested == False:
            return results

        table_info = {}
        for row in results:
            table_info[row['table']] = {} if table_info.get(row['table']) is None else table_info[row['table']]
            table_info[row['table']][row['column_name']] = {} if table_info.get(row['table']).get(row['column_name']) is None else table_info[row['table']][row['column_name']]
            table_info[row['table']][row['column_name']]['column_comment']     = row['column_comment']
            table_info[row['table']][row['column_name']]['fk_column_name']     = row['fk_column_name']
            table_info[row['table']][row['column_name']]['fk_table_name']      = row['fk_table_name']
            table_info[row['table']][row['column_name']]['is_key']             = row['is_key']
            table_info[row['table']][row['column_name']]['table']              = row['table']
        return table_info

    def createTables(self, purge=False, data_path='flask_app/database/'):
        #MySQL connection
        cnx = mysql.connector.connect(user='master', password='master', host='host.docker.internal', database='db')
        cursor = cnx.cursor()

        #temp handle lock wait time
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 120;")

        #CSV files table columns
        csv_files = [
            ('institutions.csv', 'institutions', ['type', 'name', 'department', 'address', 'city', 'state', 'zip']),
            ('positions.csv', 'positions', ['inst_id', 'title', 'responsibilities', 'start_date', 'end_date']),
            ('experience.csv', 'experiences', ['position_id', 'name', 'description', 'hyperlink', 'start_date', 'end_date']),
            ('skills.csv', 'skills', ['experience_id', 'name', 'skill_level']),
            ('feedback.csv', 'feedback', ['name', 'email', 'comment'])
        ]

        #loop through each CSV file
        for csv_filename, table_name, columns in csv_files:
            file_path = os.path.join(data_path, 'initial_data', csv_filename)

            #checks if file exist or not
            if os.path.exists(file_path):
                print(f" {csv_filename} File found!")
            else:
                print(f" {csv_filename} File not found. Check the path.")
                continue

            #open and process the CSV file
            with open(file_path, mode='r') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader)  # Skip header row

                #check that the CSV file has the right number of columns
                if len(headers) != len(columns):
                    print(f" {csv_filename} has mismatched headers. Skipping this file.")
                    continue

                #atarts transaction for the whole file
                cursor.execute("START TRANSACTION;")
                # #REDO!!!!! keeps duplicating data
                # for row in reader:
                #     row = [value if value else None for value in row]
                #
                #     if len(row) != len(columns):
                #         print(f" Skipping row due to incorrect format: {row}")
                #         continue
                #
                #     try:
                #         # Build the insert statement dynamically based on columns
                #         placeholders = ', '.join(['%s'] * len(columns))
                #         # sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                #         sql = f"""
                #             INSERT INTO {table_name} ({', '.join(columns)})
                #             VALUES ({placeholders})
                #             ON DUPLICATE KEY UPDATE {', '.join([f'{col}=VALUES({col})' for col in columns])};
                #         """
                #         cursor.execute(sql, row)
                #     except mysql.connector.Error as err:
                #         print(f" Error occurred: {err} - Skipping row: {row}")

                # # Iterate through each row in the CSV file
                for row in reader:
                    # Replace empty strings with None
                    row = [value if value else None for value in row]

                    if len(row) != len(columns):
                        print(f"Skipping row due to incorrect format: {row}")
                        continue

                    try:
                        #check for existing record in the table
                        unique_column = columns[0]  # Assuming the first column is a unique identifier
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {unique_column} = %s", (row[0],))
                        record_exists = cursor.fetchone()[0]

                        if record_exists == 0:  #only insert if the record doesn't exist
                            placeholders = ', '.join(['%s'] * len(columns))
                            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            cursor.execute(sql, row)
                        else:
                            print(f"Record already exists in {table_name}: {row[0]} - Skipping insertion.")
                    except mysql.connector.Error as err:
                        print(f"Error occurred: {err} - Skipping row: {row}")

                cursor.execute("COMMIT;")

        #commit changes and close the connection
        cnx.commit()
        cursor.close()
        cnx.close()

        print('I created and populated the database tables.')


    def insertRows(self, cursor, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):
        print(f'I am inserting rows into the {table} table.')


    def getResumeData(self):
        cnx = mysql.connector.connect(user='master', password='master', host='host.docker.internal', database='db')
        cursor = cnx.cursor(dictionary=True)

        # Start building the data
        resume_data = {}

        # Fetch institutions
        cursor.execute("SELECT * FROM institutions")
        institutions = cursor.fetchall()

        # Fetch positions for each institution
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
            # Fetch positions for each institution
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

                # Fetch experiences for each position
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

                #Fetch skills for each experience
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




