#!/bin/bash

FOLDERS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10")
SONY=("141123_003" "141123_004" "141123_005" "141123_006" "141124_001" "141124_002" "141124_003" "141125_001" "141126_001" "141126_002")

for i in "${!FOLDERS[@]}"; do
    cd ${FOLDERS[$i]}/sony 
    echo "Entering `pwd`"
    echo "ffmpeg -i ${SONY[$i]}.mp3 -ac 1 -ar 16000 ${SONY[$i]}.wav"
    ffmpeg -y -i ${SONY[$i]}.mp3 -ac 1 -ar 16000 ${SONY[$i]}.wav
    cd ../../
done

