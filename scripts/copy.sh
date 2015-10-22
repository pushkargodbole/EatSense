#!/bin/bash

FOLDERS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10")
OLYMPUS=("DD_0483.wav" "DD_0484.wav" "DD_0485.wav" "DD_0486.wav" "DD_0487.wav" "DD_0488.wav" "DD_0489.wav" "DD_0490.wav" "DD_0491.wav" "DD_0492.wav")
SONY=("141123_003.mp3" "141123_004.mp3" "141123_005.mp3" "141123_006.mp3" "141124_001.mp3" "141124_002.mp3" "141124_003.mp3" "141125_001.mp3" "141126_001.mp3" "141126_002.mp3")

for i in "${!FOLDERS[@]}"; do
    echo "mkdir ${FOLDERS[$i]}/olympus ${FOLDERS[$i]}/sony"
    mkdir ${FOLDERS[$i]}/olympus ${FOLDERS[$i]}/sony
    echo "cp --preserve=timestamps raw/olympus/${OLYMPUS[$i]} ${FOLDERS[$i]}/olympus"
    echo "cp --preserve=timestamps raw/sony/${SONY[$i]} ${FOLDERS[$i]}/sony"
    cp --preserve=timestamps raw/olympus/${OLYMPUS[$i]} ${FOLDERS[$i]}/olympus
    cp --preserve=timestamps raw/sony/${SONY[$i]} ${FOLDERS[$i]}/sony
done

