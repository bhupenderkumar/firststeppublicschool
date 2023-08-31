#!/bin/bash

set -e

host="$1"
shift
cmd="$@"

until nc -z -v -w30 $host 27017; do
  echo "Waiting for MongoDB..."
  sleep 1
done

exec $cmd
