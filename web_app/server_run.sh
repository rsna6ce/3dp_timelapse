#!/bin/bash

# crontab delay
cd `dirname $0`
sleep 10s

# start server (if stopped auto restart)
while :
do
  python3 server.py
  sleep 1s
done
