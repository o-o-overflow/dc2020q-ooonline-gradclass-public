#!/bin/bash

JOB_LOCATION="$1"

cleanup ()
{
    exit 0;
}

trap cleanup SIGINT

while true; do
    if [ "$(ls -A $JOB_LOCATION)" ]; then
        for filename in $(ls -tr "$JOB_LOCATION"/*); do
            FILE="$filename"
            SUBMISSION_ID=$(basename "$FILE")
            (
                flock -n 100 || break
                echo "Processing $SUBMISSION_ID"
                python3 -m ooonline.grade --submission-id "$SUBMISSION_ID"
                rm "$FILE"
            ) 100<$FILE
        done
    fi
    sleep 1
done
