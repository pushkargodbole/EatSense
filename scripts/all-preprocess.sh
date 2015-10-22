#!/bin/bash

FOLDERS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10")

for i in "${!FOLDERS[@]}"; do
    echo "./preprocess.py ${FOLDERS[$i]}"
    ./preprocess.py ${FOLDERS[$i]}
done

