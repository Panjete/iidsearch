#!/bin/bash

echo "Processing started!" 
args=()
while [ "$1" != "" ]; do
    args+=("$1")
    shift
done
python invidx_cons.py "${args[@]}"
echo "Shell script successfully terminated!"
