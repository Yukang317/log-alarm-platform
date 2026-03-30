#!/bin/sh
# 这个回答比较简短，只有“alive”，所以并发2000，1万个用户

apt update
apt install apache2-utils -y

ab -n 10000 -c 2000 \
    -T 'application/json' \
    -l \
    -s 60 \
    http://localhost:8000/health


