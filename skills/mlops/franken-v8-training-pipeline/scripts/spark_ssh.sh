#!/bin/bash
# Quick SSH to Spark with common options
# Usage: ./spark_ssh.sh [command]

HOST="djg6228@spark-85e8.local"
SSH_OPTS="-o ConnectTimeout=10 -o ServerAliveInterval=5 -o StrictHostKeyChecking=no"

if [ $# -eq 0 ]; then
    # Interactive shell
    ssh $SSH_OPTS $HOST
else
    # Run command and exit
    ssh $SSH_OPTS $HOST "$@"
fi