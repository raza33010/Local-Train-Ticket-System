import os
from flask import Flask, request, flash, jsonify, make_response
from flask_mysqldb import MySQL
from wtforms import Form, StringField, IntegerField, validators, DateTimeField, DecimalField, DateField, TimeField, PasswordField, SelectMultipleField
from datetime import datetime
from flask_wtf.file import FileField, FileAllowed, FileRequired
from collections import OrderedDict
from flask_cors import CORS



app = Flask(__name__)
app.secret_key = 'many random bytes'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'train_ticket'
app.config['UPLOADED_DIRECTORY'] = 'uploads/'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg','.png','.pdf']
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['CORS_ALLOW_ALL_ORIGINS'] = True
CORS(app)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
# CORS(app, resources={r"/add_users": {"origins": "http://localhost:3000"}})
mysql = MySQL(app)

# Routes Apis #..............................................................
class RoutesForm(Form):
    StartStationID = IntegerField('StartStationID', [validators.InputRequired()])
    EndStationID = IntegerField('Name', [validators.InputRequired()])
    # Status = IntegerField('Status', [
    #     validators.InputRequired(),
    #     validators.AnyOf([0, 1], 'Must be 0 or 1')
    # ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

class RouteForm(Form):
    StartStationID = IntegerField('StartStationID', [validators.InputRequired()])
    EndStationID = IntegerField('Name', [validators.InputRequired()])
    Status = IntegerField('Status', [
        validators.InputRequired(),
        validators.AnyOf([0, 1], 'Must be 0 or 1')
    ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())


@app.route('/add_routes', methods=['POST'])
def add_routes():
    form = RoutesForm(request.form)
    if form.validate():
        StartStationID = form.StartStationID.data
        EndStationID = form.EndStationID.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO routes(StartStationID, EndStationID, CreatedAt, UpdatedAt) VALUES( %s, %s, %s, %s)", (StartStationID, EndStationID, CreatedAt, UpdatedAt))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'Routes added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)
        
@app.route('/routes/<int:routes_id>', methods=['GET'])
def get_routes(routes_id):
    cur = mysql.connection.cursor()
    query = """
    SELECT routes.*, 
           start_station.StationName AS startstationname, 
           end_station.StationName AS endstationname
    FROM routes
    JOIN stations AS start_station ON routes.StartStationID = start_station.id
    JOIN stations AS end_station ON routes.EndStationID = end_station.id
    WHERE routes.id=%s
"""

    cur.execute(query,(routes_id,))    
    routes = cur.fetchone()
    cur.close()

    if routes:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        routes_dict = dict(zip(column_names, routes))

        response = {'code': '200', 'status': 'true', 'data': routes_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Routes not found'}
        return jsonify(response)

@app.route('/routes_id', methods=['GET'])
def get_all_routess_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM routes")
    routess = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for routes in routess:
        routes_dict = dict(zip(column_names, routes))
        data_with_columns.append(routes_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/routes', methods=['GET'])
def get_all_routess():
    cur = mysql.connection.cursor()
    query = """
    SELECT routes.*, 
           start_station.StationName AS startstationname, 
           end_station.StationName AS endstationname
    FROM routes
    JOIN stations AS start_station ON routes.StartStationID = start_station.id
    JOIN stations AS end_station ON routes.EndStationID = end_station.id
"""

    cur.execute(query)
    routess = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for routes in routess:
        routes_dict = dict(zip(column_names, routes))
        data_with_columns.append(routes_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM routes")
    # routess = cur.fetchall()
    # cur.close()
    
    # print(routess)

    # response = {'code': '200', 'status': 'true', 'data': routess}
    # return jsonify(response)

@app.route('/del_routes/<int:id>', methods=['DELETE'])
def delete_routes(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM routes WHERE id=%s", (id,))
    routes = cur.fetchone()
    if routes:
        logo_path = routes[2]
        # delete the routes from the database
        cur.execute("DELETE FROM routes WHERE id= %s", (id,))
        mysql.connection.commit()
        # delete the routes's logo file
        os.remove(os.path.join(app.config['UPLOADED_DIRECTORY'], logo_path))
        return jsonify({'message': f'Routes with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'Routes with id {id} not found'})


@app.route('/upd_routes/<int:routes_id>', methods=['PATCH'])
def update_routes(routes_id):
    form = RouteForm(request.form)
    if form.validate():
        StartStationID = form.StartStationID.data
        EndStationID = form.EndStationID.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM routes WHERE id=%s", (routes_id,))
        routes = cur.fetchone()

        if not routes:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'Routes not found'}
            return jsonify(final_response)
        cur.execute("UPDATE routes SET StartStationID=%s, EndStationID=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (StartStationID, EndStationID, Status, UpdatedAt, routes_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'Routes updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)

# Station Apis #..............................................................
class StationForm(Form):
    StationName = StringField('StationName', [validators.InputRequired()])
    # Status = IntegerField('Status', [
    #     validators.InputRequired(),
    #     validators.AnyOf([0, 1], 'Must be 0 or 1')
    # ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())
class StationsForm(Form):
    StationName = StringField('StationName', [validators.InputRequired()])
    Status = IntegerField('Status', [
        validators.InputRequired(),
        validators.AnyOf([0, 1], 'Must be 0 or 1')
    ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())    

@app.route('/add_stations', methods=['POST'])
def add_stations():
    form = StationForm(request.form)
    if form.validate():
        StationName = form.StationName.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO stations(StationName, CreatedAt, UpdatedAt) VALUES(%s, %s, %s)", (StationName, CreatedAt, UpdatedAt))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'stations added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)
        
@app.route('/stations/<int:stations_id>', methods=['GET'])
def get_stations(stations_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM stations WHERE id=%s", (stations_id,))
    stations = cur.fetchone()
    cur.close()

    if stations:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        stations_dict = dict(zip(column_names, stations))

        response = {'code': '200', 'status': 'true', 'data': stations_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'stations not found'}
        return jsonify(response)

@app.route('/stations_id', methods=['POST'])
def get_all_stationss_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, StationName FROM stations")
    stationss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for stations in stationss:
        stations_dict = dict(zip(column_names, stations))
        data_with_columns.append(stations_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/stations', methods=['GET'])
def get_all_stationss():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM stations")
    stationss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for stations in stationss:
        stations_dict = dict(zip(column_names, stations))
        data_with_columns.append(stations_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM stations")
    # stationss = cur.fetchall()
    # cur.close()
    
    # print(stationss)

    # response = {'code': '200', 'status': 'true', 'data': stationss}
    # return jsonify(response)

@app.route('/del_stations/<int:id>', methods=['DELETE'])
def delete_stations(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM stations WHERE id=%s", (id,))
    stations = cur.fetchone()
    if stations:
        cur.execute("DELETE FROM stations WHERE id= %s", (id,))
        mysql.connection.commit()
        return jsonify({'message': f'stations with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'stations with id {id} not found'})


@app.route('/upd_stations/<int:stations_id>', methods=['PATCH'])
def update_stations(stations_id):
    form = StationsForm(request.form)
    if form.validate():
        StationName = form.StationName.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM stations WHERE id=%s", (stations_id,))
        stations = cur.fetchone()

        if not stations:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'stations not found'}
            return jsonify(final_response)
        cur.execute("UPDATE stations SET StationName=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (StationName, Status, UpdatedAt, stations_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'stations updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)

# Train Apis #..............................................................
class TrainForm(Form):
    TrainName = StringField('TrainName', [validators.InputRequired()])
    MaxCapacity = IntegerField('MaxCapacity', [validators.InputRequired()])
    Status = IntegerField('Status', [
        validators.InputRequired(),
        validators.AnyOf([0, 1], 'Must be 0 or 1')
    ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

@app.route('/add_trains', methods=['POST'])
def add_trains():
    form = TrainForm(request.form)
    if form.validate():
        TrainName = form.TrainName.data
        MaxCapacity = form.MaxCapacity.data
        Status = form.Status.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO trains(TrainName, MaxCapacity, Status, CreatedAt, UpdatedAt) VALUES(%s, %s, %s, %s, %s)", (TrainName, MaxCapacity, Status, CreatedAt, UpdatedAt))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'trains added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)
        
@app.route('/trains/<int:trains_id>', methods=['GET'])
def get_trains(trains_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM trains WHERE id=%s", (trains_id,))
    trains = cur.fetchone()
    cur.close()

    if trains:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        trains_dict = dict(zip(column_names, trains))

        response = {'code': '200', 'status': 'true', 'data': trains_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'trains not found'}
        return jsonify(response)

@app.route('/trains_id', methods=['GET'])
def get_all_trainss_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM trains")
    trainss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for trains in trainss:
        trains_dict = dict(zip(column_names, trains))
        data_with_columns.append(trains_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/trains', methods=['POST'])
def get_all_trainss():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM trains")
    trainss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for trains in trainss:
        trains_dict = dict(zip(column_names, trains))
        data_with_columns.append(trains_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM trains")
    # trainss = cur.fetchall()
    # cur.close()
    
    # print(trainss)

    # response = {'code': '200', 'status': 'true', 'data': trainss}
    # return jsonify(response)

@app.route('/del_trains/<int:id>', methods=['DELETE'])
def delete_trains(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM trains WHERE id=%s", (id,))
    trains = cur.fetchone()
    if trains:
        logo_path = trains[2]
        # delete the trains from the database
        cur.execute("DELETE FROM trains WHERE id= %s", (id,))
        mysql.connection.commit()
        # delete the trains's logo file
        os.remove(os.path.join(app.config['UPLOADED_DIRECTORY'], logo_path))
        return jsonify({'message': f'trains with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'trains with id {id} not found'})


@app.route('/upd_trains/<int:trains_id>', methods=['PATCH'])
def update_trains(trains_id):
    form = TrainForm(request.form)
    if form.validate():
        TrainName = form.TrainName.data
        MaxCapacity = form.MaxCapacity.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM trains WHERE id=%s", (trains_id,))
        trains = cur.fetchone()

        if not trains:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'trains not found'}
            return jsonify(final_response)
        cur.execute("UPDATE trains SET TrainName=%s, MaxCapacity=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (TrainName, MaxCapacity, Status, UpdatedAt, trains_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'trains updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)

# Schedule Apis #..............................................................
class ScheduleForm(Form):
    TrainID = IntegerField('TrainID', [validators.InputRequired()])
    DepartureTime = StringField('DepartureTime', [validators.InputRequired()])
    ArrivalTime = StringField('ArrivalTime', [validators.InputRequired()])
    StartStationID = IntegerField('StartStationID', [validators.InputRequired()])
    EndStationID = IntegerField('EndStationID', [validators.InputRequired()])
    Status = IntegerField('Status', [
        validators.InputRequired(),
        validators.AnyOf([0, 1], 'Must be 0 or 1')
    ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    form = ScheduleForm(request.form)
    if form.validate():
        TrainID = form.TrainID.data
        DepartureTime = form.DepartureTime.data
        ArrivalTime = form.ArrivalTime.data
        StartStationID = form.StartStationID.data
        EndStationID = form.EndStationID.data
        Status = form.Status.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO schedule(TrainID, DepartureTime, ArrivalTime, StartStationID, EndStationID, Status, CreatedAt, UpdatedAt) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (TrainID, DepartureTime, ArrivalTime, StartStationID, EndStationID, Status, CreatedAt, UpdatedAt))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'schedule added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)
        
@app.route('/schedule/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM schedule WHERE id=%s", (schedule_id,))
    schedule = cur.fetchone()
    cur.close()

    if schedule:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        schedule_dict = dict(zip(column_names, schedule))

        response = {'code': '200', 'status': 'true', 'data': schedule_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'schedule not found'}
        return jsonify(response)

@app.route('/schedule_id', methods=['POST'])
def get_all_schedules_id():
    data = request.get_json()
  
    # if form.validate():
    tid = data.get('TrainID')
    ssid = data.get('StartStationID')
    esid = data.get('EndStationID')

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, DepartureTime FROM schedule")
    schedules = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for schedule in schedules:
        schedule_dict = dict(zip(column_names, schedule))
        data_with_columns.append(schedule_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/schedule', methods=['GET'])
def get_all_schedules():
    cur = mysql.connection.cursor()

    schedule_query = """
    SELECT schedule.*, 
        departure_station.StationName AS startstationname, 
        arrival_station.StationName AS endstationname,
        T_name.TrainName AS train_name
    FROM schedule
    JOIN stations AS departure_station ON schedule.StartStationID = departure_station.id
    JOIN stations AS arrival_station ON schedule.EndStationID = arrival_station.id
    JOIN trains AS T_name ON schedule.TrainID = T_name.id
"""

    cur.execute(schedule_query)

    schedules = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for schedule in schedules:
        schedule_dict = dict(zip(column_names, schedule))
        data_with_columns.append(schedule_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM schedule")
    # schedules = cur.fetchall()
    # cur.close()
    
    # print(schedules)

    # response = {'code': '200', 'status': 'true', 'data': schedules}
    # return jsonify(response)

@app.route('/del_schedule/<int:id>', methods=['DELETE'])
def delete_schedule(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM schedule WHERE id=%s", (id,))
    schedule = cur.fetchone()
    if schedule:
        logo_path = schedule[2]
        # delete the schedule from the database
        cur.execute("DELETE FROM schedule WHERE id= %s", (id,))
        mysql.connection.commit()
        # delete the schedule's logo file
        os.remove(os.path.join(app.config['UPLOADED_DIRECTORY'], logo_path))
        return jsonify({'message': f'schedule with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'schedule with id {id} not found'})


@app.route('/upd_schedule/<int:schedule_id>', methods=['PATCH'])
def update_schedule(schedule_id):
    form = ScheduleForm(request.form)
    if form.validate():
        TrainID = form.TrainID.data
        DepartureTime = form.DepartureTime.data
        ArrivalTime = form.ArrivalTime.data
        StartStationID = form.StartStationID.data
        EndStationID = form.EndStationID.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM schedule WHERE id=%s", (schedule_id,))
        schedule = cur.fetchone()

        if not schedule:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'schedule not found'}
            return jsonify(final_response)
        cur.execute("UPDATE schedule SET TrainID=%s, DepartureTime=%s, ArrivalTime=%s, StartStationID=%s, EndStationID=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (TrainID, DepartureTime, ArrivalTime, StartStationID, EndStationID, Status, UpdatedAt, schedule_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'schedule updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)

# Ticket Apis #..............................................................
class TicketForm(Form):
    TrainID = IntegerField('TrainID', [validators.InputRequired()])
    UserID = IntegerField('UserID', [validators.InputRequired()])
    ScheduleID = IntegerField('ScheduleID', [validators.InputRequired()])
    NoOfPerson = IntegerField('NoOfPerson', [validators.InputRequired()])
    Date = StringField('Date', [validators.InputRequired()])
    StartStationID = IntegerField('StartStationID', [validators.InputRequired()])
    EndStationID = IntegerField('EndStationID', [validators.InputRequired()])
    TypeOfTicket = StringField('TypeOfTicket', [validators.InputRequired()])
    # Status = IntegerField('Status', [
    #     validators.InputRequired(),
    #     validators.AnyOf([0, 1], 'Must be 0 or 1')
    # ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

class TicketsForm(Form):
    TrainID = IntegerField('TrainID', [validators.InputRequired()])
    UserID = IntegerField('UserID', [validators.InputRequired()])
    ScheduleID = IntegerField('ScheduleID', [validators.InputRequired()])
    Price = IntegerField('Price', [validators.InputRequired()])
    NoOfPerson = IntegerField('NoOfPerson', [validators.InputRequired()])
    Date = StringField('Date', [validators.InputRequired()])
    TypeOfTicket = StringField('TypeOfTicket', [validators.InputRequired()])
    StartStationID = IntegerField('StartStationID', [validators.InputRequired()])
    EndStationID = IntegerField('EndStationID', [validators.InputRequired()])
    Status = IntegerField('Status', [
        validators.InputRequired(),
        validators.AnyOf([0, 1], 'Must be 0 or 1')
    ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

@app.route('/add_tickets', methods=['POST'])
def add_tickets():
    form = TicketForm(request.form)
    if form.validate():
        TrainID = form.TrainID.data
        UserID = form.UserID.data
        ScheduleID = form.ScheduleID.data
        NoOfPerson = form.NoOfPerson.data
        Date = form.Date.data
        StartStationID = form.StartStationID.data
        EndStationID = form.EndStationID.data
        TypeOfTicket = form.TypeOfTicket.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data
        if TypeOfTicket == 'EC':
            Price = 250*NoOfPerson
        elif TypeOfTicket == 'BS':
            Price = 500*NoOfPerson
        else:
            Price = 1000*NoOfPerson
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tickets(TrainID, UserID, ScheduleID, Price, NoOfPerson, Date, StartStationID, EndStationID, TypeOfTicket, CreatedAt, UpdatedAt) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (TrainID, UserID, ScheduleID, Price, NoOfPerson, Date, StartStationID, EndStationID, TypeOfTicket, CreatedAt, UpdatedAt))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'tickets added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)
        
@app.route('/tickets/<int:tickets_id>', methods=['GET'])
def get_tickets(tickets_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tickets WHERE id=%s", (tickets_id,))
    tickets = cur.fetchone()
    cur.close()

    if tickets:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        tickets_dict = dict(zip(column_names, tickets))

        response = {'code': '200', 'status': 'true', 'data': tickets_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'tickets not found'}
        return jsonify(response)

@app.route('/tickets_id', methods=['GET'])
def get_all_ticketss_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM tickets")
    ticketss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for tickets in ticketss:
        tickets_dict = dict(zip(column_names, tickets))
        data_with_columns.append(tickets_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

@app.route('/ticket_s', methods=['GET'])
def get_all_ticketes():
    cur = mysql.connection.cursor()
    today_date = datetime.now().date()

    schedule_query = """
        SELECT tickets.*, 
            departure_station.StationName AS startstationname, 
            arrival_station.StationName AS endstationname,
            T_name.TrainName AS train_name,
            Stime.DepartureTime AS departure_time,
            Etime.ArrivalTime AS arrival_time
        FROM tickets
        JOIN stations AS departure_station ON tickets.StartStationID = departure_station.id
        JOIN schedule AS Stime ON tickets.StartStationID = Stime.id
        JOIN schedule AS Etime ON tickets.EndStationID = Etime.id
        JOIN stations AS arrival_station ON tickets.EndStationID = arrival_station.id
        JOIN trains AS T_name ON tickets.TrainID = T_name.id
        WHERE DATE(tickets.Date) < %s

    """

    cur.execute(schedule_query, (today_date,))
    ticketss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for tickets in ticketss:
        tickets_dict = dict(zip(column_names, tickets))
        data_with_columns.append(tickets_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)



@app.route('/tickets', methods=['GET'])
def get_all_ticketss():
    cur = mysql.connection.cursor()
    today_date = datetime.now().date()

    schedule_query = """
    SELECT tickets.*, 
        departure_station.StationName AS startstationname, 
        arrival_station.StationName AS endstationname,
        T_name.TrainName AS train_name,
        Stime.DepartureTime AS departure_time,
        Etime.ArrivalTime AS arrival_time
    FROM tickets
    JOIN stations AS departure_station ON tickets.StartStationID = departure_station.id
    JOIN schedule AS Stime ON tickets.StartStationID = Stime.id
    JOIN schedule AS Etime ON tickets.EndStationID = Etime.id
    JOIN stations AS arrival_station ON tickets.EndStationID = arrival_station.id
    JOIN trains AS T_name ON tickets.TrainID = T_name.id
    WHERE CAST(tickets.Date AS DATE) > %s
"""

    cur.execute(schedule_query, (today_date,))    
    ticketss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for tickets in ticketss:
        tickets_dict = dict(zip(column_names, tickets))
        data_with_columns.append(tickets_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM tickets")
    # ticketss = cur.fetchall()
    # cur.close()
    
    # print(ticketss)

    # response = {'code': '200', 'status': 'true', 'data': ticketss}
    # return jsonify(response)

@app.route('/del_tickets/<int:id>', methods=['DELETE'])
def delete_tickets(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tickets WHERE id=%s", (id,))
    tickets = cur.fetchone()
    if tickets:
        logo_path = tickets[2]
        # delete the tickets from the database
        cur.execute("DELETE FROM tickets WHERE id= %s", (id,))
        mysql.connection.commit()
        # delete the tickets's logo file
        os.remove(os.path.join(app.config['UPLOADED_DIRECTORY'], logo_path))
        return jsonify({'message': f'tickets with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'tickets with id {id} not found'})


@app.route('/upd_tickets/<int:tickets_id>', methods=['PATCH'])
def update_tickets(tickets_id):
    form = TicketForm(request.form)
    if form.validate():
        TrainID = form.TrainID.data
        UserID = form.UserID.data
        ScheduleID = form.ScheduleID.data
        Price = form.Price.data
        NoOfPerson = form.NoOfPerson.data
        PurchaseTime = form.PurchaseTime.dataD
        Date = form.Date.data
        StartStationID = form.StartStationID.data
        EndStationID = form.EndStationID.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tickets WHERE id=%s", (tickets_id,))
        tickets = cur.fetchone()

        if not tickets:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'tickets not found'}
            return jsonify(final_response)
        cur.execute("UPDATE tickets SET TrainID=%s, UserID=%s, ScheduleID=%s, Price=%s, NoOfPerson=%s, PurchaseTime=%s, Date=%s, StartStationID=%s, EndStationID=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (TrainID, UserID, ScheduleID, Price, NoOfPerson, PurchaseTime, Date, StartStationID, EndStationID, Status, UpdatedAt, tickets_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'tickets updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)

# User Apis #..............................................................
class UserForm(Form):
    UserName = StringField('UserName', [validators.InputRequired()])
    FirstName = StringField('FirstName', [validators.InputRequired()])
    LastName = StringField('LastName', [validators.InputRequired()])
    Email = StringField('Email', [validators.InputRequired()])
    PhoneNumber = StringField('PhoneNumber', [validators.InputRequired()])
    DateOfBirth = StringField('DateOfBirth', [validators.InputRequired()])
    Password = StringField('Password', [validators.InputRequired()])
    # Status = IntegerField('Status', [
    #     validators.InputRequired(),
    #     validators.AnyOf([0, 1], 'Must be 0 or 1')
    # ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

@app.route('/add_users', methods=['POST'])
def add_users():
    form = UserForm(request.form)
    if form.validate():
        UserName = form.UserName.data
        FirstName = form.FirstName.data
        LastName = form.LastName.data
        Email = form.Email.data
        PhoneNumber = form.PhoneNumber.data
        DateOfBirth = form.DateOfBirth.data
        Password = form.Password.data
        # Status = form.Status.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(UserName, FirstName, LastName, PhoneNumber, DateOfBirth, Password, CreatedAt, UpdatedAt, Email) VALUES( %s, %s, %s, %s, %s, %s, %s, %s, %s)", (UserName, FirstName, LastName, PhoneNumber, DateOfBirth, Password, CreatedAt, UpdatedAt, Email))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'users added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)

# @app.route('/add_users', methods=['POST'])
# def add_users():
#     form = UserForm(request.form)
#     if not form.validate():
#         for field, errors in form.errors.items():
#             for error in errors:
#                 flash(f"{field}: {error}", "error")
#         return jsonify(success=False, errors=form.errors)
#     ...
        
@app.route('/users/<int:users_id>', methods=['GET'])
def get_users(users_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (users_id,))
    users = cur.fetchone()
    cur.close()

    if users:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        users_dict = dict(zip(column_names, users))

        response = {'code': '200', 'status': 'true', 'data': users_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'users not found'}
        return jsonify(response)

@app.route('/users_id', methods=['GET'])
def get_all_userss_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM users")
    userss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for users in userss:
        users_dict = dict(zip(column_names, users))
        data_with_columns.append(users_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/users', methods=['GET'])
def get_all_userss():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    userss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for users in userss:
        users_dict = dict(zip(column_names, users))
        data_with_columns.append(users_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM users")
    # userss = cur.fetchall()
    # cur.close()
    
    # print(userss)

    # response = {'code': '200', 'status': 'true', 'data': userss}
    # return jsonify(response)

@app.route('/del_users/<int:id>', methods=['DELETE'])
def delete_users(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (id,))
    users = cur.fetchone()
    if users:
        logo_path = users[2]
        # delete the users from the database
        cur.execute("DELETE FROM users WHERE id= %s", (id,))
        mysql.connection.commit()
        # delete the users's logo file
        os.remove(os.path.join(app.config['UPLOADED_DIRECTORY'], logo_path))
        return jsonify({'message': f'users with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'users with id {id} not found'})


@app.route('/upd_users/<int:users_id>', methods=['PATCH'])
def update_users(users_id):
    form = UserForm(request.form)
    if form.validate():
        UserName = form.UserName.data
        FirstName = form.FirstName.data
        LastName = form.LastName.data
        Email = form.Email.data
        PhoneNumber = form.PhoneNumber.data
        DateOfBirth = form.DateOfBirth.data
        Password = form.Password.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE id=%s", (users_id,))
        users = cur.fetchone()

        if not users:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'users not found'}
            return jsonify(final_response)
        cur.execute("UPDATE users SET UserName=%s, FirstName=%s, LastName=%s, Email=%s, PhoneNumber=%s, DateOfBirth=%s, Password=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (UserName, FirstName, LastName, Email, PhoneNumber, DateOfBirth, Password, Status, UpdatedAt, users_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'users updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)

# Transaction Apis #..............................................................
class TransactionForm(Form):
    TicketID = StringField('TicketID', [validators.InputRequired()])
    TransactionTime = StringField('TransactionTime', [validators.InputRequired()])
    PaymentMethod = StringField('PaymentMethod', [validators.InputRequired()])
    Balance = StringField('Balance', [validators.InputRequired()])
    Status = IntegerField('Status', [
        validators.InputRequired(),
        validators.AnyOf([0, 1], 'Must be 0 or 1')
    ])
    CreatedAt = DateTimeField('Created At', default=datetime.utcnow())
    UpdatedAt = DateTimeField('Updated At', default=datetime.utcnow())

@app.route('/add_transactions', methods=['POST'])
def add_transactions():
    form = TransactionForm(request.form)
    if form.validate():
        TicketID = form.TicketID.data
        TransactionTime = form.TransactionTime.data
        PaymentMethod = form.PaymentMethod.data
        Balance = form.Balance.data
        Status = form.Status.data
        CreatedAt = form.CreatedAt.data
        UpdatedAt = form.UpdatedAt.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO transactions(UserName, FirstName, LastName, TicketID, TransactionTime, PaymentMethod, Balance, Status, CreatedAt, UpdatedAt) VALUES( %s, %s, %s, %s, %s, %s, %s)", (TicketID, TransactionTime, PaymentMethod, Balance, Status, CreatedAt, UpdatedAt))
        mysql.connection.commit()
        cur.close()

        response = {'code': '200', 'status': 'true', 'message': 'transactions added successfully'}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(response)
        
@app.route('/transactions/<int:transactions_id>', methods=['GET'])
def get_transactions(transactions_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM transactions WHERE id=%s", (transactions_id,))
    transactions = cur.fetchone()
    cur.close()

    if transactions:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        transactions_dict = dict(zip(column_names, transactions))

        response = {'code': '200', 'status': 'true', 'data': transactions_dict}
        return jsonify(response)
    else:
        response = {'code': '400', 'status': 'false', 'message': 'transactions not found'}
        return jsonify(response)

@app.route('/transactions_id', methods=['GET'])
def get_all_transactionss_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM transactions")
    transactionss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for transactions in transactionss:
        transactions_dict = dict(zip(column_names, transactions))
        data_with_columns.append(transactions_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/transactions', methods=['GET'])
def get_all_transactionss():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM transactions")
    transactionss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for transactions in transactionss:
        transactions_dict = dict(zip(column_names, transactions))
        data_with_columns.append(transactions_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)

    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM transactions")
    # transactionss = cur.fetchall()
    # cur.close()
    
    # print(transactionss)

    # response = {'code': '200', 'status': 'true', 'data': transactionss}
    # return jsonify(response)

@app.route('/del_transactions/<int:id>', methods=['DELETE'])
def delete_transactions(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM transactions WHERE id=%s", (id,))
    transactions = cur.fetchone()
    if transactions:
        logo_path = transactions[2]
        # delete the transactions from the database
        cur.execute("DELETE FROM transactions WHERE id= %s", (id,))
        mysql.connection.commit()
        # delete the transactions's logo file
        os.remove(os.path.join(app.config['UPLOADED_DIRECTORY'], logo_path))
        return jsonify({'message': f'transactions with id {id} deleted successfully'})
    else:
        return jsonify({'message': f'transactions with id {id} not found'})


@app.route('/upd_transactions/<int:transactions_id>', methods=['PATCH'])
def update_transactions(transactions_id):
    form = TransactionForm(request.form)
    if form.validate():
        TicketID = form.TicketID.data
        TransactionTime = form.TransactionTime.data
        PaymentMethod = form.PaymentMethod.data
        Balance = form.Balance.data
        Status = form.Status.data
        UpdatedAt = form.UpdatedAt.data
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM transactions WHERE id=%s", (transactions_id,))
        transactions = cur.fetchone()

        if not transactions:
            cur.close()
            final_response = {'code': '404', 'status': 'false', 'message': 'transactions not found'}
            return jsonify(final_response)
        cur.execute("UPDATE transactions SET TicketID=%s, TransactionTime=%s, PaymentMethod=%s, Balance=%s, Status=%s, UpdatedAt=%s WHERE id=%s", (TicketID, TransactionTime, PaymentMethod, Balance, Status, UpdatedAt, transactions_id))
        mysql.connection.commit()
        cur.close()
        
        response = {'code': '200', 'status': 'true', 'message': 'transactions updated successfully'}
        return jsonify(response)
    else:
        final_response = {'code': '400', 'status': 'false', 'message': 'Invalid input'}
        return jsonify(final_response)



# User side apis

@app.route('/stations', methods=['POST'])
def get_all_stationes():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM stations")
    stationss = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
    cur.close()

    data_with_columns = []
    for stations in stationss:
        stations_dict = dict(zip(column_names, stations))
        data_with_columns.append(stations_dict)

    response = {
        "code": "200",
        "data": data_with_columns,
        "status": "true"
    }

    return jsonify(response)


@app.route('/email/<string:email>', methods=['GET'])
def get_users_email(email):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE Email=%s", (email,))
    users = cur.fetchone()

    if users:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
        users_dict = dict(zip(column_names, users))

        response = {'code': '200', 'status': 'true', 'data': users_dict}
        cur.close()  # Close the cursor after fetching data
        return jsonify(response)
    else:
        cur.close()  # Close the cursor if no user is found
        response = {'code': '400', 'status': 'false', 'message': 'User not found'}
        return jsonify(response)

@app.route('/username/<string:username>', methods=['GET'])
def get_users_username(username):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE UserName=%s", (username,))
    users = cur.fetchone()

    if users:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description
        users_dict = dict(zip(column_names, users))

        response = {'code': '200', 'status': 'true', 'data': users_dict}
        cur.close()  # Close the cursor after fetching data
        return jsonify(response)
    else:
        cur.close()  # Close the cursor if no user is found
        response = {'code': '400', 'status': 'false', 'message': 'User not found'}
        return jsonify(response)

@app.route('/login', methods=['POST'])
def login():
    # form = UserForm(request.form)
    data = request.get_json()
  
    # if form.validate():
    username = data.get('username')
    password = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE UserName = %s AND Password = %s", (username, password))
    user = cur.fetchone()
    cur.close()
    print(user)
    if user:
        column_names = [desc[0] for desc in cur.description]  # Get column names from cursor description

        user_dict = dict(zip(column_names,user))
        data = {'code': '200', 'status': 'true', 'data': user_dict}
        return jsonify(data)
    else:
            # Authentication failed
        return jsonify({'status': 'false', 'message': 'Invalid email or password'}), 401


if __name__ == "__main__":
    app.run(debug=True)