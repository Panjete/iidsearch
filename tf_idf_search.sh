#!/bin/bash

args=()
while [ "$1" != "" ]; do
    args+=("$1")
    shift
done

echo "Processing Started!" 
python top.py "${args[@]}"
echo "All Queries processed!"
