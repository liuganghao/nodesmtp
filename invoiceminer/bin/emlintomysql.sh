#!/bin/sh

emlfile=$1
if [ ! -f "$emlfile" ]; then
    echo "not file: $emlfile"
    exit 1
fi

# export LD_LIBRARY_PATH=/opt/rh/python27/root/usr/lib64

_RUN_PYTHON=/usr/bin/python
EXEC_PYTHON_FILE=/opt/ysyc/invoiceminer/emlintomysql.py
LOG_FILE=/opt/ysyc/invoiceminer/logs/emlintomysql.log

cmd="$_RUN_PYTHON $EXEC_PYTHON_FILE $emlfile >> $LOG_FILE 2>&1"
# echo $cmd
eval $cmd
