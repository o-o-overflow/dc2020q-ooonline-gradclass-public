#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import random
import shutil
import subprocess
import tempfile
import time

from flask_sqlalchemy import SQLAlchemy

from . import app

db = app.db

CONSTANT_TIME_EXECUTION_SECONDS = 3
MAX_USERS = 5000

def choose_user():
    user_id = random.randint(0, MAX_USERS-1)
    return f"user_{user_id}"

def grade(submission_id):
    with app.app.app_context():
        with tempfile.TemporaryDirectory() as tmp:
            user = choose_user()
            shutil.chown(tmp, user, user)
            os.chmod(tmp, 0o700)
            
            submission = app.Submission.query.get(submission_id)

            # Copy in the binary
            grading_location = f"{tmp}/grading"
            shutil.copy(submission.assignment.grading_binary, grading_location)
            shutil.chown(grading_location, user, user)
            os.chmod(grading_location, 0o500)

            # Copy in the submission
            submission_location = f"{tmp}/submission.c"
            shutil.copy(submission.filename, submission_location)
            shutil.chown(submission_location, user, user)
            os.chmod(submission_location, 0o400)

            os.chdir(tmp)

            stdout = b""

            with tempfile.NamedTemporaryFile() as tmp_output:

                shutil.chown(tmp_output.name, user, user)
            
                start = datetime.datetime.now()
                result = subprocess.run(["/usr/bin/sudo", "-u", user, "./grading", "./submission.c"],
                                        stdout=tmp_output)
                end = datetime.datetime.now()
                taken = (end - start).total_seconds()
                time.sleep(CONSTANT_TIME_EXECUTION_SECONDS - taken)
            
                grading_result = False
                message = "Parsing Fail"
                tmp_output.seek(0)

                stdout = tmp_output.read()


            if stdout:
                try:
                    print(stdout)
                    response = json.loads(stdout)
                    grading_result = response['passed']
                    message = response['message']
                except json.JSONDecodeError:
                    pass
            elif result.returncode == -9:
                grading_result = False
                message = "Failed test cases"
                
            sr = app.SubmissionResult(submission_id=submission.id,
                                      result=grading_result,
                                      message=message)
            db.session.add(sr)
            db.session.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="grade")
    parser.add_argument("--debug", action="store_true", help="Enable debugging")
    parser.add_argument("--submission-id", required=True, help="Submission to grade")
    parser.add_argument("--version", action="version", version="%(prog)s v0.1.0")

    args = parser.parse_args()

    grade(args.submission_id)
