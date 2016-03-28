#!/bin/bash

SCRIPTDIR=`dirname $(readlink -f $0)`
DATADIR=`readlink -f ${SCRIPTDIR}/../data/mapreduce`


# === MR Job Parameters ===

interpreter=python
script=wordcount.py
src="${DATADIR}/twitter-stream.log.2016-03-26_13-13"

# ==========================


# Build Commands
LOCAL_JOB="${interpreter} ${script} ${src}"
EMR_JOB="${interpreter} ${script} ${src} -r emr --output-dir=${dst} --no-output"


# Run
${LOCAL_JOB}
#${EMR_JOB}
