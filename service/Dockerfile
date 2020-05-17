# Stage 0, build the app
FROM node:latest

CMD mkdir /root/frontend
COPY src/frontend/package.json /root/frontend/package.json
COPY src/frontend/yarn.lock /root/frontend/yarn.lock

RUN yarn --cwd /root/frontend install --production

COPY src/frontend /root/frontend
RUN yarn --cwd /root/frontend run build

from ubuntu:18.04
ENV DEBIAN_FRONTEND noninteractive

run apt-get -qq update && apt-get install -qq --no-install-recommends \
    python3 python3-pip python3-setuptools postgresql-server-dev-all postgresql nginx uwsgi uwsgi-plugin-python3 \
    supervisor build-essential python3-dev sudo \
    && pip3 install setuptools wheel 
# python3-pip, etc.

copy src/requirements.txt /root/requirements.txt
run pip3 install -r /root/requirements.txt

copy deploy/create_users.sh /root/create_users.sh
run /root/create_users.sh

copy deploy/supervisord.conf /etc/supervisord.conf
copy deploy/uwsgi.ini /etc/uwsgi.ini
copy deploy/default /etc/nginx/sites-available/default

run mkdir /grading && chmod 700 /grading && chown www-data:www-data /grading
copy src/assignment_grading /grading/assignment_1_grading
run chmod 755 /grading/assignment_1_grading

copy src/grading_worker.sh /root/grading_worker.sh
copy deploy/create_db.sh /root/create_db.sh

run mkdir /submissions && chown www-data:www-data /submissions && chmod 700 /submissions
run mkdir /jobs && chown www-data:www-data /jobs && chmod 700 /jobs

run mkdir -p /opt/app
copy ./src/setup.py /opt/app
copy ./src/ooonline/ /opt/app/ooonline
run pip3 install -e /opt/app

run /root/create_db.sh

COPY --from=0 /root/frontend/build /frontend 

# the deployment tester will pass in the flag from the yaml
ARG THE_FLAG="OOO{this is a test flag}"
RUN touch /flag && chmod 640 /flag && chown root:www-data /flag && echo $THE_FLAG > /flag

expose 5000
cmd ["/usr/bin/supervisord"]
# ^^ If ps would be too revealing, replace with the line below.
#    AFAIK, this also disables the built-in printf(%n) protection, so YMMV.
#cmd chmod go-rwx /proc && /usr/sbin/xinetd -syslog local0 -dontfork -f /service.conf
