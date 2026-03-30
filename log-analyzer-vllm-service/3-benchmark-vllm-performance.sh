#!/bin/sh

apt update
apt install apache2-utils -y

ab -n 100 -c 10 \
    -T 'application/json' \
    -l \
    -s 60 \
    -p request.json \
    http://localhost:8000/v1/chat/completions


