FROM python:3.7-alpine

ENV TERM linux


# For example:
run apk update && apk add --no-cache  bash
COPY requirements.txt /requirements.txt
run pip install -r requirements.txt



COPY exploit.py /
COPY solution.c /

COPY check1.py /

