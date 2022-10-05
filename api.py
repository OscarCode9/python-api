from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
import json
import jwt
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.declarative import DeclarativeMeta
from functools import wraps
from validate_email import validate_email
app = Flask(__name__)


app.config['SECRET_KEY'] = 'thisismySewcretKay'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/oscarcode/Documents/pythonAPI/todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from flaskext.mysql import MySQL


mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = os.environ['MYSQL_DATABASE_USER']
app.config['MYSQL_DATABASE_PASSWORD'] = os.environ['MYSQL_DATABASE_PASSWORD']
app.config['MYSQL_DATABASE_DB'] = os.environ['MYSQL_DATABASE_DB']
app.config['MYSQL_DATABASE_HOST'] = os.environ['MYSQL_DATABASE_HOST']

mysql.init_app(app)

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(
                public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid'})
        return f(current_user, *args, **kwargs)
    return decorated


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    # this will fail on non-encodable values, like other classes
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

# delete a user by username


@app.route('/api/v1/user/<username>', methods=['DELETE'])
def mysql_delete_one_user(username):
    conn = mysql.connect()
    cursor = conn.cursor()
    sql_query = """DELETE FROM Users WHERE username = %s"""
    r = cursor.execute(sql_query, (username))
    if r == 1:
        conn.commit()
        conn.close()
        return jsonify({
        'message': 'A user has been deleted',
        'error': False })
    else:
        conn.close()
        return jsonify({
        'message': 'User hasn\'t been deleted, we can\'t find this user',
        'error': True })

# get user by username
@app.route('/api/v1/user/<username>', methods=['GET'])
def mysql_get_one(username):
    conn=mysql.connect()
    cursor=conn.cursor()

    sql_query="""SELECT * FROM Users WHERE username = %s"""
    cursor.execute(sql_query, (username))
    user=cursor.fetchone()

    if not user:
        return make_response(jsonify({
            'message': 'we can\'t find this user',
            'error': True
            }), 404)

    user_object={}

    user_object['id']=user[0]
    user_object['firstName']=user[1]
    user_object['lastName']=user[2]
    user_object['email']=user[3]
    user_object['username']=user[5]

    conn.close()
    return jsonify({'user':  user_object})

@app.route('/api/v1/user/<username>', methods=['PUT'])
def mysql_update_one_user(username):

    conn = mysql.connect()
    cursor = conn.cursor()
    
    data=request.get_json()

    sql_query="""SELECT * FROM Users WHERE username = %s"""
    cursor.execute(sql_query, (username))
    user=cursor.fetchone()

    if not user:
        return make_response(jsonify({
            'message': 'we can\'t find this user',
            'error': True
            }), 404)

    sql_query = """
    UPDATE Users SET
    firstName = %s,
    lastName = %s,
    email = %s,
    username = %s
    WHERE username = %s;"""
    
    firstName=data['firstName']
    lastName=data['lastName']
    email=data['email']
    newusername=data['username']

    cursor.execute(sql_query, (firstName, lastName, email, newusername, username))
    

    sql_select_by_id="""SELECT * FROM Users WHERE username = %s """
    cursor.execute(sql_select_by_id, (newusername))
    user=cursor.fetchone()

    user_object={}

    if not user:
        return make_response(jsonify({
            'message': 'Error is the database',
            'error': True
            }), 404)

    user_object['id']=user[0]
    user_object['firstName']=user[1]
    user_object['lastName']=user[2]
    user_object['email']=user[3]
    user_object['username']=user[5]
    
    conn.commit()
    conn.close()

    return jsonify({
        'user': user_object,
        'message': 'This user has been updated',
        'error': False
    })

@app.route('/api/v1/users', methods=['GET'])
def mysql_get_all_users():
    conn=mysql.connect()
    cursor=conn.cursor()
    cursor.execute("SELECT * from Users")
    users=cursor.fetchall()
    output=[]
    for user in users:
        user_data={}
        user_data['id']=user[0]
        user_data['firstName']=user[1]
        user_data['lastName']=user[2]
        user_data['email']=user[3]
        user_data['password']=user[4]
        user_data['username']=user[5]
        output.append(user_data)
    conn.close()
    return jsonify({'users': output})

@app.route('/api/v1/user', methods=['POST'])
def mysql_create_user():
    conn=mysql.connect()
    cursor=conn.cursor()
    data=request.get_json()

    sql_query="""INSERT INTO
        Users (id,
            firstName,
            lastname,
            email ,
            password,
            username)
    VALUES (null,%s,%s,%s,%s,%s)"""

    hash_password=generate_password_hash(data['password'], method='sha256')
    firstName=data['firstName']
    lastName=data['lastName']
    email=data['email']
    username=data['username']

    is_email=validate_email(email)
    if not is_email:
        return make_response(jsonify({
            'message': 'Email is not validate',
            'error': True
            }), 401)

    cursor.execute(sql_query, (firstName, lastName,
                   email, hash_password, username))

    sql_select_by_id="""SELECT * FROM Users WHERE username = %s """
    cursor.execute(sql_select_by_id, (username))
    user=cursor.fetchone()

    user_object={}

    if not all(user):
        return make_response(jsonify({
            'message': 'Error is the database',
            'error': True
            }), 404)

    user_object['id']=user[0]
    user_object['firstName']=user[1]
    user_object['lastName']=user[2]
    user_object['email']=user[3]
    user_object['username']=user[5]

    conn.commit()
    conn.close()

    return jsonify({
        'user': user_object,
        'message': 'A new user has been inserted in the datebase',
        'error': False
    })

@app.route('/users', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    users=User.query.all()
    output=[]

    for user in users:
        user_data={}
        user_data['public_id']=user.public_id
        user_data['name']=user.name
        user_data['password']=user.password
        user_data['admin']=user.admin
        output.append(user_data)
    return jsonify({'users': output})



@app.route('/user/<public_id>', methods=['GET'])
def get_one_user(public_id):
    user=User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({
            'message': 'No user found!'
        })
    user_data={}
    user_data['public_id']=user.public_id
    user_data['name']=user.name
    user_data['password']=user.password
    user_data['admin']=user.admin
    return jsonify({'user': user_data})


@app.route('/user', methods=['POST'])
def create_user():
    data=request.get_json()
    hash_password=generate_password_hash(data['password'], method='sha256')
    new_user=User(public_id=str(uuid.uuid4()),
                    name=data['name'], password=hash_password, admin=False)
    db.session.add(new_user)
    db.session.commit()
    new_user=json.dumps(new_user, cls=AlchemyEncoder)
    return jsonify({'message': 'A new user has been created', 'user': new_user})


@app.route('/user/<public_id>', methods=['PUT'])
def promote_user(public_id):
    data=request.get_json()
    user=User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'No user found!'})

    hash_password=generate_password_hash(data['password'], method='sha256')
    user.name=data['name']
    user.password=hash_password
    user.admin=data['admin']
    db.session.commit()
    return jsonify({'message': 'The user has been promoted!'})


@app.route('/user/<public_id>', methods=['DELETE'])
def delete_user(public_id):
    user=User.query.filter_by(public_id=public_id).first()
    if not user:
        return jsonify({'message': 'No user found!'})
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'The user has been deleted'})


@app.route('/login')
def login():
    auth=request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Could no verify', 401, {'WWW-Authenticate': 'Basic realm="login required!"'})
    user=User.query.filter_by(name=auth.username). first()
    if not user:
        return make_response('Could no verify', 401, {'WWW-Authenticate': 'Basic realm="login required!"'})
    if check_password_hash(user.password, auth.password):
        token=jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})
    return make_response('Could no verify', 401, {'WWW-Authenticate': 'Basic realm="login required!"'})


if __name__ == '__main__':
    app.run(debug=True)
