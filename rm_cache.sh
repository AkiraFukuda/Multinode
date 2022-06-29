#!/bin/bash 
while :
do
    echo 3 > /proc/sys/vm/drop_caches
    echo "Finish drop cache!"
    sleep 1
done