#!/bin/bash
set +e
set +x

/etc/init.d/postgresql start

sudo -u postgres psql --command "create database ooonline;"
sudo -u postgres SQLALCHEMY_DATABASE_URI="postgres:///ooonline" python3 -m ooonline.app --load-prod

sudo -u postgres psql --command "create user web with encrypted password 'tX9JZuGLb26R';"
sudo -u postgres psql --command "create user grade with encrypted password 'wjKjq3p7pCWB';"

# Web front-end perms
sudo -u postgres psql --command "grant select, insert (username, password) on users to web;" ooonline
sudo -u postgres psql --command "grant usage, select on sequence users_id_seq to web;" ooonline

sudo -u postgres psql --command "grant select on classes to web;" ooonline

sudo -u postgres psql --command "grant select on assignments to web;" ooonline

sudo -u postgres psql --command "grant select, insert (user_id, assignment_id, filename), update (filename) on submissions to web;" ooonline
sudo -u postgres psql --command "grant usage, select on sequence submissions_id_seq to web;" ooonline

sudo -u postgres psql --command "grant select on submission_results to web;" ooonline

# Grading backend perms
sudo -u postgres psql --command "grant select on assignments to grade;" ooonline

sudo -u postgres psql --command "grant select on submissions to grade;" ooonline

sudo -u postgres psql --command "grant select, insert (submission_id, result, message) on submission_results to grade;" ooonline
sudo -u postgres psql --command "grant usage, select on sequence submission_results_id_seq to grade;" ooonline

/etc/init.d/postgresql stop

