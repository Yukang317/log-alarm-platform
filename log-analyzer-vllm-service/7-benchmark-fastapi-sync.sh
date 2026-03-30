#!/bin/sh

ab -n 200 -c 50 \
   -T 'text/plain' \
   -l \
   -s 60 \
   -p request.data \
   http://localhost:8000/analyze

