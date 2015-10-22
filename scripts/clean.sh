#!/bin/bash

while IFS= read -r -u3 -d $'\0' file; do
    echo "rm $file"
    rm $file
done 3< <(find ./ -type f -regex ".*\.csv$\|.*sony.*.wav$" -print0 2> /dev/null)

