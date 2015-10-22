#!/bin/bash


FILES="`find ./ -maxdepth 3 -type f -regex "./[0-9]+\(.*waccel-.*\|.*IMU.*.txt\|.*sony.*mp3\|.*olympus.*wav\)" -printf "%p " 2> /dev/null`"
echo "$FILES"
SCRIPTS="`find ./ -maxdepth 1 -type f -regex ".*\(py\|sh\)" -printf "%p " 2> /dev/null`"
echo "$SCRIPTS"

zip scripts.zip ${SCRIPTS}
zip raw-data.zip ${FILES}


# while IFS= read -r -u3 -d $'\0' file; do
#     echo "rm $file"
#     rm $file
# done 3< <(find ./ -type f -regex ".*\.csv$\|.*sony.*.wav$" -print0 2> /dev/null)

