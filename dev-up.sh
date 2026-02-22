#!/bin/bash

# This script starts the MySQL and Redis services for development.

mysql.server start
redis-server --daemonize yes
echo "Services running."