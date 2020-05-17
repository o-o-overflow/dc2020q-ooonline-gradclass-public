#!/usr/bin/env python3
"""
ooonline-course Backend.
"""

import argparse
import base64
import hashlib
import os
import pathlib
import secrets
import string
import sys

from flask import Flask, jsonify, request, json
from flask_cors import CORS
from flask_restful import Api, Resource, abort, reqparse
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy

import itsdangerous 

app = Flask(__name__)
CORS(app)
api = Api(app)
auth = HTTPTokenAuth(header="X-Auth-Token")

app.config['SECRET_KEY'] = secrets.token_bytes(32)

if "SQLALCHEMY_DATABASE_URI" not in os.environ:
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

if 'JOB_LOCATION' in os.environ:
    app.config['JOB_LOCATION'] = os.environ['JOB_LOCATION']

if 'SUBMISSION_LOCATION' in os.environ:
    app.config['SUBMISSION_LOCATION'] = os.environ['SUBMISSION_LOCATION']

if 'FLAG_LOCATION' in os.environ:
    app.config['FLAG_LOCATION'] = os.environ['FLAG_LOCATION']

# Models

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (db.Index('idx_username_password', 'username', 'password'),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    legacy_password = db.Column(db.Boolean(), nullable=False, server_default="0")
    admin = db.Column(db.Boolean(), nullable=False, server_default="0")
    submissions = db.relationship("Submission")

    def auth_token(self):
        auth_s = itsdangerous.URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return auth_s.dumps(dict(id=self.id))

    @staticmethod
    def from_token(token, expires = 3600):
        auth_s = itsdangerous.URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            data = auth_s.loads(token, max_age=expires)
        except Exception as e:
            return None

        return User.query.get(data['id'])

class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(512), nullable=False)
    open = db.Column(db.Boolean(), nullable=False, default=False)
    assignments = db.relationship("Assignment", back_populates='klass')

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            open=self.open,
        )

class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    klass = db.relationship("Class", back_populates="assignments")
    name = db.Column(db.String(128), nullable=False)
    text = db.Column(db.String(5000), nullable=False)
    grading_binary = db.Column(db.String(2048), nullable=False)
    submissions = db.relationship("Submission", back_populates="assignment")

    def to_dict(self):
        return dict(id=self.id,
                    class_id=self.class_id,
                    text=self.text,
                    name=self.name,
        )

class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    assignment = db.relationship("Assignment", back_populates="submissions")
    filename = db.Column(db.String(2048), nullable=True)

    submission_result = db.relationship("SubmissionResult", uselist=False, back_populates="submission")

    def to_dict(self):
        return dict(id=self.id,
                    user_id=self.user_id,
                    assignment_id=self.assignment_id)

class SubmissionResult(db.Model):
    __tablename__ = "submission_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    submission = db.relationship("Submission", back_populates="submission_result")
    result = db.Column(db.Boolean(), nullable=False)
    message = db.Column(db.String(100), nullable=False)

# Auth information
@auth.verify_token
def verify_token(token):
    user = User.from_token(token)
    if not user:
        return False
    return user

# Views

class UserRegistration(Resource):
    def post(self):
        name = request.json.get('name')
        if name is None:
            abort(400)

        # Simulate a waf
        banned = [' ', ';', '\\', '|', '/', '*', 'insert', 'update', 'delete', 'drop', 'union']
        if any(map(lambda c: c in name.lower(), banned)):
            abort(403)

        # they don't get to choose their password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))

        # sqlalchemy is too slow, need to execute own query
        query = db.text(f"insert into users(username, password) values('{name}', :passwd) RETURNING id, username");
        result = db.session.execute(query, {'name': name, 'passwd': hashlib.sha512(password.encode('utf-8')).hexdigest()})
        if not result:
            abort(500)
        result = list(result)
        
        if len(result) != 1:
            abort(500)

        id, db_name = result[0]
        db.session.commit()

        return jsonify(dict(id=id,
                            password=password,
                            returning_from_db_name=db_name))

class UserLogin(Resource):
    def post(self):
        name = request.json.get('name')
        passwd = request.json.get('passwd')
        if name is None or passwd is None:
            abort(400)
        user = User.query.filter_by(username=name, password=hashlib.sha512(passwd.encode('utf-8')).hexdigest()).first()
        if not user:
            _the_user = User.query.filter_by(username=name).first()
            if _the_user.legacy_password:
                user = User.query.filter_by(username=name, password=passwd).first()

        if not user:
            return jsonify(dict(message="User not found"))

        return jsonify(dict(message="Successful login",
                            token=user.auth_token(),
                            id=user.id))


class ClassList(Resource):

    @auth.login_required
    def get(self):
        return jsonify([x.to_dict() for x in db.session.query(Class)])

class AssignmentList(Resource):

    @auth.login_required
    def get(self, class_id):
        _class = Class.query.get(class_id)
        if not _class:
            abort(404)

        if not _class.open:
            abort(404)
            
        return jsonify([x.to_dict() for x in db.session.query(Assignment).filter_by(class_id=class_id)])

class AnAssignment(Resource):
    
    @auth.login_required
    def get(self, assignment_id):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            abort(404)

        return jsonify(assignment.to_dict())
    

class SubmissionList(Resource):

    @auth.login_required
    def get(self, assignment_id):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            abort(404)

        return jsonify([x.to_dict() for x in db.session.query(Submission).filter_by(assignment_id=assignment_id,
                                                                                    user_id=auth.current_user().id)])

    @auth.login_required
    def post(self, assignment_id):
        file = request.json.get('file')
        if file is None:
            abort(400)

        if len(file) > 1024:
            abort(400)

        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            abort(404)

        if not assignment.klass.open:
            abort(404)

        submission = Submission(user_id=auth.current_user().id,
                                assignment_id=assignment.id)

        db.session.add(submission)
        db.session.flush()

        target_dir = f"{app.config['SUBMISSION_LOCATION']}/{assignment.id}/{auth.current_user().id}"
        pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)

        fname = f"{target_dir}/{submission.id}"
        with open(fname, "w") as f:
            f.write(file)

        submission.filename = fname
        db.session.merge(submission)
      
        db.session.commit()

        with open(f"{app.config['JOB_LOCATION']}/{submission.id}", "w"):
            # Only need to create the file
            pass

        return jsonify(dict(id=submission.id,
                            message="Succesfully created submission"))

class TheSubmission(Resource):

    @auth.login_required
    def get(self, submission_id):
        submission = Submission.query.get(submission_id)
        if not submission:
            abort(404)

        if not submission.user_id == auth.current_user().id:
            abort(404)

        return jsonify(dict(id=submission.id,
                            filename=submission.filename))

class ShowSubmissionResult(Resource):

    @auth.login_required
    def get(self, submission_id):
        submission = Submission.query.get(submission_id)
        if not submission:
            abort(404)

        if not submission.user_id == auth.current_user().id:
            abort(404)

        if not submission.submission_result:
            return jsonify(dict(message="Not graded",
                                retry=True))

        if submission.submission_result.result:
            with open(app.config['FLAG_LOCATION'], 'r') as flag:
                return jsonify(dict(message=f"Success! Flag: {flag.read()}"))
        else:
            return jsonify(dict(message=f"Failure. Grading message: {submission.submission_result.message}"))


class AdminAssignment(Resource):

    @auth.login_required
    def get(self, assignment_id):
        if not auth.current_user().admin:
            abort(404)

        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            abort(404)

        return jsonify(dict(id=assignment.id,
                            grading_binary=base64.b64encode(open(assignment.grading_binary, 'rb').read()).decode('utf-8')))


api.add_resource(UserRegistration, '/user/register')
api.add_resource(UserLogin, '/user/login')
api.add_resource(ClassList, '/classes')
api.add_resource(AssignmentList, '/class/<int:class_id>/assignments')
api.add_resource(AnAssignment, '/assignment/<int:assignment_id>')
api.add_resource(SubmissionList, '/assignment/<int:assignment_id>/submissions')
api.add_resource(TheSubmission, '/submission/<int:submission_id>')
api.add_resource(ShowSubmissionResult, '/submission/<int:submission_id>/result')
api.add_resource(AdminAssignment, '/assignment/<int:assignment_id>/admin')

def init_data():
    db.session.add(User(username='admin',
                        password='zKSTznZYGD',
                        admin=True,
                        legacy_password=True,
    ))
    _class = Class(name="Decidability",
                   open=True)
    db.session.add(_class)
    db.session.commit()

    db.session.add(Class(name="Cybersecurity 101",
                         open=False))

    db.session.add(Class(name="Cybersecurity 201",
                         open=False))

    db.session.add(Class(name="Ethical Hacking",
                         open=False))

    db.session.add(Assignment(class_id=_class.id,
                              name="Halt, who goes there?",
                              text=r"""In this assignment you will write a C program that decides if the given Python3 program on the given program halts or not.

### Input

JSON will be sent to the standard input of your program. The `program` field will have the Python3 program, and the `input` field will have the standard input of the program.

### Output

Your program must output `HALT` (without quotes) if the program halts, or `DOES NOT HALT` (without quotes) if the program does not halt.

### Examples

If your program is given the following input:

```
{"program": "print(\"hello world\")", "input": "testing"}
```

It should output:

```
HALT
```

If your program is given the following input:

```
{"program": "user = input()\nif user == \"hello\":\n    while True:\n        pass\n", "input": "testing"}
```

It should output:

```
HALT
```

If your program is given the following input:

```
{"program": "user = input()\nif user == \"hello\":\n    while True:\n        pass\n", "input": "hello\n"}
```

It should output:

```
DOES NOT HALT
```

### Implementation

Upload your C program.

### Evaluation

Your program will need to pass all the test cases for credit. Successful submissions will receive the flag. 
""",
                              grading_binary="/grading/assignment_1_grading"))
    db.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="oonline")
    parser.add_argument("--debug", action="store_true", help="Enable debugging")
    parser.add_argument("--port", type=int, default=5001, help="Port to listen on [default: 5001]")
    parser.add_argument("--host", default='127.0.0.1', help="Host to listen on [default: 127.0.0.1]")
    parser.add_argument("--job-location", default="/tmp/jobs", help="Directory to store grading jobs")
    parser.add_argument("--submission-location", default="/tmp/submissions", help="Directory to store the submissions")
    parser.add_argument("--flag-location", default="/flag", help="Flag file location")
    parser.add_argument("--test", action="store_true", help="Add test data")
    parser.add_argument("--load-prod", action="store_true", help="Create DB and load production data")
    parser.add_argument("--version", action="version", version="%(prog)s v0.1.0")

    args = parser.parse_args()

    if args.load_prod:
        db.create_all()
        init_data()
        sys.exit(0)

    if args.test:
        db.create_all()
        init_data()

    pathlib.Path(args.job_location).mkdir(parents=True, exist_ok=True)
    app.config['JOB_LOCATION'] = args.job_location

    pathlib.Path(args.submission_location).mkdir(parents=True, exist_ok=True)
    app.config['SUBMISSION_LOCATION'] = args.submission_location

    app.config['FLAG_LOCATION'] = args.flag_location

    app.run(host=args.host, port=args.port, debug=args.debug)

if "FLASK_WSGI_DEBUG" in os.environ:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
    app.debug = True
