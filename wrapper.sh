#!/bin/bash

declare -a arr=(
  # list of domains
)

for i in "${arr[@]}"
do
    python main.py "$i" 100
done

