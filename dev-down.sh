#!/bin/bash

# This script stops the MySQL and Redis services that were started by dev-up.sh.

redis-cli shutdown
mysql.server stop
echo "Services stopped."