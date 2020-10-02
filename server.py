from flask import Flask, request, abort, Response
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
from database import SQL_Server
from json import dumps
from datetime import datetime, timedelta
import os, configparser

app  = Flask(__name__)
api  = Api(app, prefix="/api/v1")

auth = HTTPBasicAuth()
sql_server = SQL_Server()
config = configparser.ConfigParser()
config.read('config.cfg')

TIME_REQUESTS = int(config.get('ConfigInfo', 'TIME_REQUESTS'))
PORT = str(config.get('ConfigInfo', 'PORT'))
USERNAME = str(config.get('ConfigInfo', 'USERNAME'))
PASSWORD = str(config.get('ConfigInfo', 'PASSWORD'))


USER_DATA = {
    USERNAME : PASSWORD
}

""" 
App Verification method 
curl -X GET "http://localhost:5000/api/v1/user_Location?user=User&location=400,-700" --user admin:SuperSecretPwd
"""

@auth.verify_password
def verify(username, password):
    if not (username and password):
        return False
    return USER_DATA.get(username) == password


# decorator to limit flask requests
def limit_requests(function):
    def wrapper(self):
        user = request.args.get('user')
        filename = f'dates-{user}.txt'
        first_request = False
        if not os.path.exists(filename):
            datesfile = open(filename, "w+")
        else:
            datesfile = open(filename, "r") 

        if os.stat(filename).st_size == 0:
            previous_date = datetime.now()
            first_request = True
        else:
            previous_date  = sql_server.stringToDatetime(datesfile.read())

        diff_times = (datetime.now() - previous_date)
        
        if diff_times > timedelta(minutes=TIME_REQUESTS) or first_request:
            datesfile = open(filename, "w+")
            datesfile.write(str(datetime.now()))
            return function(self)
        else:
            error_message = dumps({'Message': 'Too Many Requests'})
            abort(Response(error_message, 401))
    return wrapper


# Add User location
class user_Location(Resource):
    @auth.login_required
    @limit_requests
    def get(self):
        params = request.args.get('user')
        params2 = (request.args.get('location')).replace(" ", "")
        if params != 'null':
            sql_server.insert_informaton(params, params2, str(datetime.now()))
            sql_server.save_database()
            sql_server.close_database()
        return "Location data added to User's table"
        
# write dates to file         
api.add_resource(user_Location, '/user_Location')

# Add User virus state
class user_VirusState(Resource):
    @auth.login_required
    def get(self):
        params = request.args.get('user')
        if not sql_server.checkVirusState(params, True) and params != 'null':
            sql_server.hasVirus(params)
            sql_server.save_database()
            sql_server.close_database()
            return "Virus State added to User's table"
        return "Virus State modified in past"

api.add_resource(user_VirusState, '/user_hasVirus')

# Add User virus state
class user_VirusProbability(Resource):
    @auth.login_required
    def get(self):
        params = request.args.get('user')
        if params != 'null':
            with open("victims.txt", "r") as myfile:
                existing_users = [line.rstrip() for line in myfile]
                if params in existing_users:
                    date_interaction = str(sql_server.dateTimetoString(sql_server.retrieve_date_interaction(params, sql_server.return_infected_interaction(params))))
                    return date_interaction 
            return "Safe" 
        print("no null allowed")

api.add_resource(user_VirusProbability, '/user_virusPotential')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
