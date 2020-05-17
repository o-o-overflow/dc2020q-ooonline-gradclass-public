#!/bin/bash
set +e
set +x

(for i in {0..5000}; do
    echo "user_$i:::::/tmp:/usr/sbin/nologin"
done) | newusers 2> /dev/null || true
