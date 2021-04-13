#!/bin/bash

FILE=~/.ssh/known_hosts
RES=$(ssh-keygen -F $1)

if [ ${#RES} == 0 ]
    then FINGERPRINT=$(ssh-keyscan -H $1)
    if [ ${#FINGERPRINT} == 0 ]
        then (exit 1); echo "$?: Invalid host"
    else echo $FINGERPRINT >> $FILE
        (exit 0); echo "$?: OK"
    fi
else (exit 0); echo "$?: Host already exists"
fi