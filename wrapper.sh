#!/bin/bash

declare -a arr=(
                "ritcheylaw.com"
                "sreeravilaw.com"
                "huntsvillealabamaattorneys.com"
                )

for i in "${arr[@]}"
do
    python main.py "$i" 2
done

