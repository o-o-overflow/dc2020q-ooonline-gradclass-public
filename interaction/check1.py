#!/usr/bin/env python3

import json
import random
import requests
import sys
import time

import logging
logging.basicConfig(level=logging.DEBUG)

def main():

    host = sys.argv[1]
    port = int(sys.argv[2])

    url = f"http://{host}:{port}"

    result = requests.get(f"{url}/")
    assert result.status_code == 200

    # register

    username = f"adamd{random.randint(0, 1000000)}"
    
    result = requests.post(f"{url}/user/register",
                           json=dict(name=username))

    assert result.status_code == 200
    r = result.json()
    assert 'id' in r
    assert 'password' in r

    passwd = r['password']


    result = requests.post(f"{url}/user/login",
                           json=dict(name=username,
                                     passwd=passwd))

    assert result.status_code == 200
    r = result.json()
    token = r['token']

    auth_headers = {"X-Auth-Token": token}

    result = requests.get(f"{url}/classes",
                          headers=auth_headers)
    r = result.json()
    assert len(r) > 0

    result = requests.get(f"{url}/class/1/assignments",
                          headers=auth_headers)
    r = result.json()
    assert len(r) > 0

    result = requests.get(f"{url}/assignment/1/submissions",
                          headers=auth_headers)
    r = result.json()
    assert len(r) == 0

    result = requests.post(f"{url}/assignment/1/submissions",
                           json=dict(file="hello world, I am not a C file"),
                           headers=auth_headers)

    r = result.json()
    id = r['id']

    time.sleep(5)

    result = requests.get(f"{url}/submission/{id}/result",
                          headers=auth_headers)
    r = result.json()
    print(r)

    result = requests.post(f"{url}/assignment/1/submissions",
                           json=dict(file="int main() { return 0; }"),
                           headers=auth_headers)

    r = result.json()
    id = r['id']

    time.sleep(5)

    result = requests.get(f"{url}/submission/{id}/result",
                          headers=auth_headers)
    r = result.json()
    success_message = r['message']
    print(r)

    result = requests.post(f"{url}/assignment/1/submissions",
                           json=dict(file="int main() { while (1) { } }"),
                           headers=auth_headers)

    r = result.json()
    id = r['id']

    time.sleep(5)

    result = requests.get(f"{url}/submission/{id}/result",
                          headers=auth_headers)
    r = result.json()

    # check that a ending submission has the same output as an infinite loop
    assert success_message == r['message']
    print(r)

    sys.exit(0)


if __name__ == '__main__':
    main()

